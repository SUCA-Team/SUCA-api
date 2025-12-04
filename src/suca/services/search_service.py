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

    # Priority scoring constants
    EXACT_MATCH = 1000
    STARTS_WITH = 500
    CONTAINS_WORD = 300  # For English word boundary matches
    CONTAINS = 100
    COMMON_BONUS = 10000  # Bonus for common words

    def __init__(self, session: Session):
        super().__init__(session)

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
            results: Raw query results [(ent_seq, priority, length), ...]
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
        seen: set[int] = set()
        unique_entry_ids = []
        for ent_seq, _priority, _length in results:
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

        Priority scoring (two-dimensional):
        Common words: +10000
        - Exact match:     1000 → 11000 (common) / 1000 (rare)
        - Starts with:      500 → 10500 / 500
        - Contains (word):  300 → 10300 / 300
        - Contains (any):   100 → 10100 / 100
        """
        query_lower = query.lower()

        # Create word boundary pattern for exact word matches
        # "eat" should match "to eat" but not "create"
        word_pattern = f"%{query_lower}%"
        starts_pattern = f"{query_lower}%"

        # Build scoring query for English glosses
        priority_score = func.max(
            case(
                # COMMON WORDS
                # Exact match (whole gloss)
                (
                    and_(func.lower(col(Gloss.text)) == query_lower, col(Entry.is_common)),
                    self.EXACT_MATCH + self.COMMON_BONUS,
                ),
                # Starts with query
                (
                    and_(
                        func.lower(col(Gloss.text)).like(starts_pattern),
                        col(Entry.is_common),
                    ),
                    self.STARTS_WITH + self.COMMON_BONUS,
                ),
                # Contains as separate word (with word boundaries)
                (
                    and_(
                        or_(
                            func.lower(col(Gloss.text)).like(f"% {query_lower} %"),
                            func.lower(col(Gloss.text)).like(f"{query_lower} %"),
                            func.lower(col(Gloss.text)).like(f"% {query_lower}"),
                            func.lower(col(Gloss.text)).like(f"% {query_lower},%"),
                            func.lower(col(Gloss.text)).like(f"% {query_lower};%"),
                        ),
                        col(Entry.is_common),
                    ),
                    self.CONTAINS_WORD + self.COMMON_BONUS,
                ),
                # Contains anywhere
                (
                    and_(func.lower(col(Gloss.text)).like(word_pattern), col(Entry.is_common)),
                    self.CONTAINS + self.COMMON_BONUS,
                ),
                # RARE WORDS
                (func.lower(col(Gloss.text)) == query_lower, self.EXACT_MATCH),
                (func.lower(col(Gloss.text)).like(starts_pattern), self.STARTS_WITH),
                (
                    or_(
                        func.lower(col(Gloss.text)).like(f"% {query_lower} %"),
                        func.lower(col(Gloss.text)).like(f"{query_lower} %"),
                        func.lower(col(Gloss.text)).like(f"% {query_lower}"),
                        func.lower(col(Gloss.text)).like(f"% {query_lower},%"),
                        func.lower(col(Gloss.text)).like(f"% {query_lower};%"),
                    ),
                    self.CONTAINS_WORD,
                ),
                (func.lower(col(Gloss.text)).like(word_pattern), self.CONTAINS),
                else_=0,
            )
        ).label("priority")

        # Word length for secondary sorting
        word_length = self._get_word_length_expr()

        # Build the main query
        stmt = (
            select(col(Entry.ent_seq), priority_score, word_length)
            .select_from(Entry)
            .outerjoin(Kanji, col(Entry.ent_seq) == col(Kanji.entry_id))
            .outerjoin(Reading, col(Entry.ent_seq) == col(Reading.entry_id))
            .join(Sense, col(Entry.ent_seq) == col(Sense.entry_id))
            .join(Gloss, col(Sense.id) == col(Gloss.sense_id))
            .where(and_(func.lower(col(Gloss.text)).like(word_pattern), col(Gloss.lang) == "eng"))
            .group_by(col(Entry.ent_seq))
            .having(priority_score > 0)
            .order_by(priority_score.desc(), word_length.asc())
            .limit(request.limit * 2)
        )

        # Filter by commonality if requested
        if not request.include_rare:
            stmt = stmt.where(col(Entry.is_common))

        # Filter by part of speech if requested
        if request.pos:
            stmt = stmt.where(col(Sense.pos).like(f"%{request.pos}%"))

        # Execute and process results
        results = self.session.exec(stmt).all()
        return self._process_search_results(results, request, query, "English")

    def _search_by_japanese(self, query: str, request: SearchRequest) -> SearchResponse:
        """
        Search by Japanese kanji/reading.

        Scoring system (Match Type × Commonality):
        Common words always ranked higher than rare words for the same match type.

        Match types (base score):
        - Exact match: 1000
        - Starts with: 500
        - Contains: 100

        Commonality bonus:
        - Common word: +10000 (ensures common words always appear first)
        - Rare word: +0

        Final scores:
        - Common exact: 11000
        - Rare exact: 1000
        - Common starts-with: 10500
        - Rare starts-with: 500
        - Common contains: 10100
        - Rare contains: 100
        """
        # Two-dimensional scoring: match_type_score + commonality_bonus
        # Common words get +10000, ensuring they always rank above rare words
        priority_score = func.max(
            case(
                # COMMON WORDS (score 10000+)
                # Exact matches - common
                (
                    and_(col(Kanji.keb) == query, col(Entry.is_common)),
                    self.EXACT_MATCH + self.COMMON_BONUS,
                ),
                (
                    and_(col(Reading.reb) == query, col(Entry.is_common)),
                    self.EXACT_MATCH + self.COMMON_BONUS,
                ),
                # Starts with - common
                (
                    and_(col(Kanji.keb).like(f"{query}%"), col(Entry.is_common)),
                    self.STARTS_WITH + self.COMMON_BONUS,
                ),
                (
                    and_(col(Reading.reb).like(f"{query}%"), col(Entry.is_common)),
                    self.STARTS_WITH + self.COMMON_BONUS,
                ),
                # Contains - common
                (
                    and_(col(Kanji.keb).like(f"%{query}%"), col(Entry.is_common)),
                    self.CONTAINS + self.COMMON_BONUS,
                ),
                (
                    and_(col(Reading.reb).like(f"%{query}%"), col(Entry.is_common)),
                    self.CONTAINS + self.COMMON_BONUS,
                ),
                # RARE WORDS (score <10000)
                # Exact matches - rare
                (col(Kanji.keb) == query, self.EXACT_MATCH),
                (col(Reading.reb) == query, self.EXACT_MATCH),
                # Starts with - rare
                (col(Kanji.keb).like(f"{query}%"), self.STARTS_WITH),
                (col(Reading.reb).like(f"{query}%"), self.STARTS_WITH),
                # Contains - rare
                (col(Kanji.keb).like(f"%{query}%"), self.CONTAINS),
                (col(Reading.reb).like(f"%{query}%"), self.CONTAINS),
                else_=0,
            )
        ).label("priority")

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

        # If not including rare words, filter by common
        if not request.include_rare:
            stmt = stmt.where(col(Entry.is_common))

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

        # Build tags
        tags = []
        if entry.is_common:
            tags.append("common word")

        return DictionaryEntryResponse(
            word=primary_kanji or primary_reading or "Unknown",
            reading=primary_reading,
            is_common=bool(entry.is_common),
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
        Common words are prioritized.
        """
        query = request.query.strip()
        if not query:
            raise SearchException("Search query cannot be empty")

        starts_pattern = f"{query}%"

        # Build the query for suggestions
        stmt = (
            select(col(Kanji.keb))
            .select_from(Entry)
            .join(Kanji, col(Entry.ent_seq) == col(Kanji.entry_id))
            .where(col(Kanji.keb).like(starts_pattern))
            .group_by(col(Kanji.keb), col(Entry.is_common))
            .order_by(col(Entry.is_common).desc(), func.min(func.length(col(Kanji.keb))).asc())
            .limit(request.limit)
        )

        # If not including rare words, filter by common
        if not request.include_rare:
            stmt = stmt.where(col(Entry.is_common))

        # Execute and fetch suggestions
        results = self.session.exec(stmt).all()

        # suggestions = [keb for keb in results]
        return SearchSuggestionResponse(suggestions=list(results))
