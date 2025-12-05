"""Search service for dictionary operations - Optimized version."""

import json

from sqlalchemy import case, func
from sqlmodel import Session, and_, col, or_, select

from ..core.exceptions import SearchException
from ..db.model import Entry, Gloss, Kanji, Reading, Sense
from ..schemas.search import (
    DictionaryEntryResponse,
    MeaningResponse,
    SearchRequest,
    SearchResponse,
    SearchSuggestionResponse,
)
from .base import BaseService


class SearchService(BaseService[Entry]):
    """Service for search operations with optimized queries."""

    # Priority scoring constants - Match type base scores
    EXACT_MATCH = 1000
    STARTS_WITH = 500
    CONTAINS_WORD = 300  # For English word boundary matches
    CONTAINS = 100

    # Commonality bonuses based on ke_pri/re_pri frequency indicators
    # Higher tiers get progressively larger bonuses to ensure proper ordering
    ICHI1_BONUS = 50000  # Most common (ichi1)
    NEWS1_BONUS = 40000  # Very common (news1)
    SPEC1_BONUS = 30000  # Common specialized (spec1)
    NF01_BONUS = 25000  # Common news frequency (nf01)
    GAI1_BONUS = 22000  # Common loanword (gai1)
    ICHI2_BONUS = 20000  # Moderately common (ichi2)
    NEWS2_BONUS = 15000  # Moderately common news (news2)
    SPEC2_BONUS = 10000  # Less common specialized (spec2)
    NF02_BONUS = 8000  # Less common news frequency (nf02)
    GAI2_BONUS = 8000  # Less common loanword (gai2)

    def __init__(self, session: Session):
        super().__init__(session)

    def _get_priority_bonus_expr(self, pri_column):
        """
        Create SQLAlchemy CASE expression for priority bonus based on ke_pri/re_pri.

        Args:
            pri_column: The column to check (Kanji.ke_pri or Reading.re_pri)

        Returns:
            SQLAlchemy CASE expression that returns the appropriate bonus score
        """
        return case(
            (pri_column.like("%ichi1%"), self.ICHI1_BONUS),
            (pri_column.like("%news1%"), self.NEWS1_BONUS),
            (pri_column.like("%spec1%"), self.SPEC1_BONUS),
            (pri_column.like("%nf01%"), self.NF01_BONUS),
            (pri_column.like("%gai1%"), self.GAI1_BONUS),
            (pri_column.like("%ichi2%"), self.ICHI2_BONUS),
            (pri_column.like("%news2%"), self.NEWS2_BONUS),
            (pri_column.like("%spec2%"), self.SPEC2_BONUS),
            (pri_column.like("%nf02%"), self.NF02_BONUS),
            (pri_column.like("%gai2%"), self.GAI2_BONUS),
            else_=0,
        )

    def _is_english_query(self, query: str) -> bool:
        """
        Detect if query is in English (ASCII only) or Japanese.
        Returns True for English queries, False for Japanese.
        """
        # Remove spaces and check if all characters are ASCII
        cleaned = query.strip()
        return cleaned.isascii() and cleaned.replace(" ", "").replace("-", "").isalpha()

    def _get_word_length_expr(self):
        """
        Create SQLAlchemy expression for word length calculation.
        Returns the minimum length among all kanji and reading forms.
        """
        kanji_min_length = func.min(func.length(col(Kanji.keb)))
        reading_min_length = func.min(func.length(col(Reading.reb)))
        return func.coalesce(
            func.least(kanji_min_length, reading_min_length),
            kanji_min_length,
            reading_min_length,
            999,
        ).label("word_length")

    def _process_search_results(
        self, results, request: SearchRequest, query: str, search_type: str
    ) -> SearchResponse:
        """
        Process search results: deduplicate, paginate, fetch full entries, and format response.

        Args:
            results: Raw query results - can be [(ent_seq, priority), ...] or [(ent_seq, priority, length), ...]
            request: Original search request with limit/page
            query: Search query string
            search_type: "English" or "Japanese" for message formatting

        Returns:
            SearchResponse with formatted results
        """
        if not results:
            return SearchResponse(
                results=[], total_count=0, query=query, message=f"No results found for '{query}'"
            )

        # Get unique entry IDs preserving priority order
        # Handle both 2-tuple and 3-tuple results
        seen: set[int] = set()
        unique_entry_ids = []
        for result in results:
            ent_seq = result[0]  # First element is always ent_seq
            if ent_seq not in seen:
                seen.add(ent_seq)
                unique_entry_ids.append(ent_seq)
                if len(unique_entry_ids) >= request.limit:
                    break

        # Fetch full entry data
        entries_stmt = select(Entry).where(col(Entry.ent_seq).in_(unique_entry_ids))
        entries = self.session.exec(entries_stmt).all()

        # Create ordered results
        entry_map = {e.ent_seq: e for e in entries}
        ordered_entries = [entry_map[ent_id] for ent_id in unique_entry_ids if ent_id in entry_map]

        # Convert to response format
        response_results = [self._entry_to_response(entry) for entry in ordered_entries]

        return SearchResponse(
            results=response_results,
            total_count=len(seen),
            query=query,
            message=f"Found {len(seen)} results for '{query}' ({search_type} search)",
        )

    def search_entries(self, request: SearchRequest) -> SearchResponse:
        """
        Intelligent search supporting both Japanese and English queries.

        Auto-detects language:
        - ASCII queries → Search English glosses
        - Japanese queries → Search kanji/readings

        Two-dimensional priority (both languages):
        - Common words always ranked higher than rare words
        - Match type determines ranking within each group
        """
        try:
            if not request.query.strip():
                raise SearchException("Search query cannot be empty")

            query = request.query.strip()

            # Auto-detect language and route to appropriate search
            if self._is_english_query(query):
                return self._search_by_english(query, request)
            else:
                return self._search_by_japanese(query, request)

        except SearchException:
            raise
        except Exception as e:
            self._handle_db_error(e, "search")
            return SearchResponse(results=[], total_count=0, query=request.query)

    def _search_by_english(self, query: str, request: SearchRequest) -> SearchResponse:
        """
        Search by English gloss text.

        Priority scoring system:
        Base match score + Commonality bonus + Sense position penalty

        Match types (base scores):
        - Exact match:     1000
        - Starts with:      500
        - Contains (word):  300
        - Contains (any):   100

        Commonality bonuses (from kanji/reading priority):
        - ichi1: +50000 (most common)
        - news1: +40000
        - spec1: +30000
        - nf01:  +25000
        - gai1:  +22000
        - ichi2: +20000
        - news2: +15000
        - spec2: +10000
        - nf02:  +8000
        - gai2:  +8000
        - none:  +0 (rare words)

        Sense position penalty:
        - Earlier senses (1st, 2nd meaning) are prioritized
        - Uses minimum sense ID to favor primary meanings
        """
        query_lower = query.lower()

        # Create word boundary pattern for exact word matches
        # "eat" should match "to eat" but not "create"
        word_pattern = f"%{query_lower}%"
        # starts_pattern = f"{query_lower}%"

        # Get maximum priority bonus from kanji and reading tables
        max_kanji_bonus = func.max(self._get_priority_bonus_expr(col(Kanji.ke_pri)))
        max_reading_bonus = func.max(self._get_priority_bonus_expr(col(Reading.re_pri)))
        commonality_bonus = func.coalesce(
            func.greatest(max_kanji_bonus, max_reading_bonus), 0
        ).label("commonality_bonus")

        # Strip parenthetical clarifications for exact matching
        # e.g. "water (esp. cool or cold)" -> "water"
        stripped_text = func.regexp_replace(
            func.lower(col(Gloss.text)),
            " \\([^)]+\\)",  # Match space followed by (anything)
            "",
            "g",
        )

        # Base match score with sense position consideration
        # Check both original and stripped text for exact matches
        match_score = func.max(
            case(
                # Exact match: full text equals query, or stripped text equals query
                # This matches "water" or "water (esp. cool)" but NOT "watermelon"
                (
                    or_(func.lower(col(Gloss.text)) == query_lower, stripped_text == query_lower),
                    self.EXACT_MATCH,
                ),
                # Starts with: "water..." at beginning followed by space or punctuation
                # Matches "water surface" but NOT "watermelon"
                (
                    or_(
                        func.lower(col(Gloss.text)).like(f"{query_lower} %"),
                        func.lower(col(Gloss.text)).like(f"{query_lower},%"),
                        func.lower(col(Gloss.text)).like(f"{query_lower};%"),
                    ),
                    self.STARTS_WITH,
                ),
                # Contains as separate word: surrounded by spaces or punctuation
                (
                    or_(
                        func.lower(col(Gloss.text)).like(f"% {query_lower} %"),
                        func.lower(col(Gloss.text)).like(f"% {query_lower}"),
                        func.lower(col(Gloss.text)).like(f"% {query_lower},%"),
                        func.lower(col(Gloss.text)).like(f"% {query_lower};%"),
                    ),
                    self.CONTAINS_WORD,
                ),
                # Contains anywhere (least specific, for compound words)
                (func.lower(col(Gloss.text)).like(word_pattern), self.CONTAINS),
                else_=0,
            )
        ).label("match_score")

        # Calculate sense position penalty efficiently
        # Use conditional aggregation instead of expensive subqueries

        # Calculate sense position penalty using CTE for better performance and correctness
        # CTE to find first matching sense for each entry
        sense_positions_cte = (
            select(
                col(Sense.entry_id).label("entry_id"),
                func.min(col(Sense.id)).label("first_sense_id"),
                func.min(
                    case(
                        (func.lower(col(Gloss.text)).like(word_pattern), col(Sense.id)),
                        else_=999999,
                    )
                ).label("first_matching_sense_id"),
            )
            .select_from(Sense)
            .join(Gloss, col(Sense.id) == col(Gloss.sense_id))
            .where(col(Gloss.lang) == "eng")
            .group_by(col(Sense.entry_id))
        ).cte("sense_positions")

        # Calculate sense position difference
        sense_position = func.greatest(
            col(sense_positions_cte.c.first_matching_sense_id)
            - col(sense_positions_cte.c.first_sense_id),
            0,
        )

        # Apply penalty: first 2 senses get no penalty, later senses heavily penalized
        sense_penalty = case(
            (sense_position < 2, 0),
            (sense_position >= 999, 999999),  # Entry doesn't match (shouldn't happen)
            else_=sense_position * 10000,  # 10k penalty per sense position
        ).label("sense_penalty")

        # Total priority score
        priority_score = (match_score + commonality_bonus - sense_penalty).label("priority")

        # Build the main query with CTE
        stmt = (
            select(col(Entry.ent_seq), priority_score)
            .select_from(Entry)
            .outerjoin(Kanji, col(Entry.ent_seq) == col(Kanji.entry_id))
            .outerjoin(Reading, col(Entry.ent_seq) == col(Reading.entry_id))
            .join(sense_positions_cte, col(Entry.ent_seq) == col(sense_positions_cte.c.entry_id))
            .join(Sense, col(Entry.ent_seq) == col(Sense.entry_id))
            .join(Gloss, col(Sense.id) == col(Gloss.sense_id))
            .where(
                and_(
                    func.lower(col(Gloss.text)).like(word_pattern),
                    col(Gloss.lang) == "eng",
                    # Exclude confusing example patterns
                    ~func.lower(col(Gloss.text)).like("%as ... as ...%"),
                    # Exclude if gloss is enclosed in parentheses (examples)
                    ~func.lower(col(Gloss.text)).ilike(f"%({word_pattern})%"),
                    # Exclude negation patterns that would cause false matches
                    ~func.lower(col(Gloss.text)).ilike("not %"),
                    ~func.lower(col(Gloss.text)).ilike("% not %"),
                    ~func.lower(col(Gloss.text)).ilike("never %"),
                    ~func.lower(col(Gloss.text)).ilike("% never %"),
                    ~func.lower(col(Gloss.text)).ilike("non-%"),
                    ~func.lower(col(Gloss.text)).ilike("% non-%"),
                    ~func.lower(col(Gloss.text)).ilike("without %"),
                    ~func.lower(col(Gloss.text)).ilike("% without %"),
                    ~func.lower(col(Gloss.text)).ilike("un%"),  # unhappy, etc.
                )
            )
            .group_by(
                col(Entry.ent_seq),
                col(sense_positions_cte.c.first_sense_id),
                col(sense_positions_cte.c.first_matching_sense_id),
            )
            .having(priority_score > 0)
            .order_by(priority_score.desc())
            .limit(request.limit * 2)
        )

        # Filter by commonality if requested (exclude entries with no priority markers)
        if not request.include_rare:
            stmt = stmt.having(commonality_bonus > 0)

        # Filter by part of speech if requested
        if request.pos:
            stmt = stmt.where(col(Sense.pos).ilike(f"%{request.pos}%"))

        # Execute and process results
        results = self.session.exec(stmt).all()
        return self._process_search_results(results, request, query, "English")

    def _search_by_japanese(self, query: str, request: SearchRequest) -> SearchResponse:
        """
        Search by Japanese kanji/reading.

        Priority scoring system:
        Base match score + Commonality bonus from ke_pri/re_pri

        Match types (base scores):
        - Exact match: 1000
        - Starts with: 500
        - Contains: 100

        Commonality bonuses (from priority indicators):
        - ichi1: +50000 (most common)
        - news1: +40000
        - spec1: +30000
        - nf01:  +25000
        - gai1:  +22000
        - ichi2: +20000
        - news2: +15000
        - spec2: +10000
        - nf02:  +8000
        - gai2:  +8000
        - none:  +0 (rare words)

        Examples:
        - ichi1 exact match: 51000
        - news1 starts with: 40500
        - rare exact match: 1000
        """
        # Get maximum priority bonus from matching kanji/reading
        max_kanji_bonus = func.max(
            case(
                (col(Kanji.keb) == query, self._get_priority_bonus_expr(col(Kanji.ke_pri))),
                (
                    col(Kanji.keb).like(f"{query}%"),
                    self._get_priority_bonus_expr(col(Kanji.ke_pri)),
                ),
                (
                    col(Kanji.keb).like(f"%{query}%"),
                    self._get_priority_bonus_expr(col(Kanji.ke_pri)),
                ),
                else_=0,
            )
        )
        max_reading_bonus = func.max(
            case(
                (col(Reading.reb) == query, self._get_priority_bonus_expr(col(Reading.re_pri))),
                (
                    col(Reading.reb).like(f"{query}%"),
                    self._get_priority_bonus_expr(col(Reading.re_pri)),
                ),
                (
                    col(Reading.reb).like(f"%{query}%"),
                    self._get_priority_bonus_expr(col(Reading.re_pri)),
                ),
                else_=0,
            )
        )
        commonality_bonus = func.coalesce(
            func.greatest(max_kanji_bonus, max_reading_bonus), 0
        ).label("commonality_bonus")

        # Base match score (independent of commonality)
        match_score = func.max(
            case(
                (col(Kanji.keb) == query, self.EXACT_MATCH),
                (col(Reading.reb) == query, self.EXACT_MATCH),
                (col(Kanji.keb).like(f"{query}%"), self.STARTS_WITH),
                (col(Reading.reb).like(f"{query}%"), self.STARTS_WITH),
                (col(Kanji.keb).like(f"%{query}%"), self.CONTAINS),
                (col(Reading.reb).like(f"%{query}%"), self.CONTAINS),
                else_=0,
            )
        ).label("match_score")

        # Total priority = match score + commonality bonus
        priority_score = (match_score + commonality_bonus).label("priority")

        # Word length for secondary sorting
        word_length = self._get_word_length_expr()

        # Build the main query
        stmt = (
            select(col(Entry.ent_seq), priority_score, word_length)
            .select_from(Entry)
            .outerjoin(Kanji, col(Entry.ent_seq) == col(Kanji.entry_id))
            .outerjoin(Reading, col(Entry.ent_seq) == col(Reading.entry_id))
            .join(Sense, col(Entry.ent_seq) == col(Sense.entry_id))
            .where(or_(col(Kanji.keb).like(f"%{query}%"), col(Reading.reb).like(f"%{query}%")))
            .group_by(col(Entry.ent_seq))
            .having(priority_score > 0)  # Only entries with matches
            .order_by(priority_score.desc(), word_length.asc())
            .limit(request.limit * 2)
            .offset((request.page - 1) * request.limit)  # Get extra for deduplication
        )

        # If not including rare words, filter by commonality (exclude entries with no priority markers)
        if not request.include_rare:
            stmt = stmt.having(commonality_bonus > 0)

        # Filter by part of speech if requested
        if request.pos:
            stmt = stmt.where(col(Sense.pos).like(f"%{request.pos}%"))

        # Execute and process results
        results = self.session.exec(stmt).all()
        return self._process_search_results(results, request, query, "Japanese")

    def _entry_to_response(self, entry: Entry) -> DictionaryEntryResponse:
        """Convert Entry model to response format efficiently."""
        # Primary kanji & reading
        primary_kanji = entry.kanjis[0].keb if entry.kanjis else None
        primary_reading = entry.readings[0].reb if entry.readings else None

        # Calculate is_common based on ke_pri/re_pri
        is_common = False
        commonality_level = None
        for k in entry.kanjis:
            if k.ke_pri:
                is_common = True
                # Store the highest priority level
                if "ichi1" in k.ke_pri:
                    commonality_level = "ichi1"
                    break
                elif not commonality_level or "news1" in k.ke_pri:
                    commonality_level = "news1" if "news1" in k.ke_pri else commonality_level

        if not is_common:
            for r in entry.readings:
                if r.re_pri:
                    is_common = True
                    if "ichi1" in r.re_pri:
                        commonality_level = "ichi1"
                        break
                    elif not commonality_level or "news1" in r.re_pri:
                        commonality_level = "news1" if "news1" in r.re_pri else commonality_level

        # Other forms (excluding primary)
        other_forms = []
        if entry.readings:
            for r in entry.readings[1:]:  # Skip first (primary)
                other_forms.append(r.reb)
        if entry.kanjis:
            for k in entry.kanjis[1:]:  # Skip first (primary)
                other_forms.append(k.keb)

        # Variants (all kanji-reading combinations)
        variants = []
        for k in entry.kanjis:
            for r in entry.readings:
                variants.append({"kanji": k.keb, "reading": r.reb})

        # Meanings
        meanings = []
        for s in entry.senses:
            # Get English definitions
            defs = [g.text for g in s.glosses if g.lang == "eng"]

            # Parse parts of speech
            pos_list = s.pos.split("; ") if s.pos else []

            # Parse examples
            examples = []
            for ex in s.examples:
                try:
                    ex_obj = json.loads(ex.text)
                    examples.append(ex_obj)
                except Exception:
                    # Skip invalid JSON examples
                    pass

            meaning_obj = MeaningResponse(
                pos=pos_list, definitions=defs, examples=examples, notes=[]
            )
            meanings.append(meaning_obj)

        # Build tags based on priority markers
        tags = []
        if commonality_level == "ichi1":
            tags.append("very common")
        elif is_common:
            tags.append("common word")

        return DictionaryEntryResponse(
            word=primary_kanji or primary_reading or "Unknown",
            reading=primary_reading,
            is_common=is_common,
            jlpt_level=entry.jlpt_level if hasattr(entry, "jlpt_level") else None,
            meanings=meanings,
            other_forms=other_forms,
            tags=tags,
            variants=variants,
        )

    def get_suggestions(self, request: SearchRequest) -> SearchSuggestionResponse:
        """
        Get search suggestions based on partial query.

        Suggestions are derived from kanji and reading forms that start with the query.
        Words with higher commonality (based on ke_pri) are prioritized.
        """
        query = request.query.strip()
        if not query:
            raise SearchException("Search query cannot be empty")

        starts_pattern = f"{query}%"

        # Calculate priority bonus for ordering
        priority_bonus = self._get_priority_bonus_expr(col(Kanji.ke_pri))

        # Build the query for suggestions
        stmt = (
            select(col(Kanji.keb), func.max(priority_bonus).label("priority"))
            .select_from(Entry)
            .join(Kanji, col(Entry.ent_seq) == col(Kanji.entry_id))
            .where(col(Kanji.keb).like(starts_pattern))
            .group_by(col(Kanji.keb))
            .order_by(func.max(priority_bonus).desc(), func.min(func.length(col(Kanji.keb))).asc())
            .limit(request.limit)
        )

        # If not including rare words, filter by priority
        if not request.include_rare:
            stmt = stmt.having(func.max(priority_bonus) > 0)

        # Execute and fetch suggestions
        results = self.session.exec(stmt).all()

        # Extract just the kanji text from results
        suggestions = [keb for keb, _ in results]
        return SearchSuggestionResponse(suggestions=suggestions)
