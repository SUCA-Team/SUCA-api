"""Search service for dictionary operations."""

import json

from sqlmodel import Session, col, select

from ..core.exceptions import SearchException
from ..db.model import Entry, Kanji, Reading
from ..schemas.search import DictionaryEntryResponse, MeaningResponse, SearchRequest, SearchResponse
from .base import BaseService


class SearchService(BaseService[Entry]):
    """Service for search operations."""

    def __init__(self, session: Session):
        super().__init__(session)

    def search_entries(self, request: SearchRequest) -> SearchResponse:
        """
        Search dictionary entries with intelligent prioritization:
        1. Exact matches
        2. Common words starting with query
        3. Common words containing query
        4. All other partial matches
        """
        try:
            if not request.query.strip():
                raise SearchException("Search query cannot be empty")

            query = request.query.strip()
            all_results = []

            # Priority 1: Exact matches
            exact_results = self._get_exact_matches(query)

            # Priority 2: Words starting with query
            start_results = self._get_start_matches(query, request.include_rare)

            # Priority 3: Common words containing query
            contain_results = self._get_contain_matches(query, request.include_rare)

            # Priority 4: Other partial matches
            other_results = self._get_other_matches(query, request.include_rare)

            # Combine and deduplicate results
            all_results = exact_results + start_results + contain_results + other_results
            unique_results = self._deduplicate_results(all_results)

            # Sort within priority groups by word length
            sorted_results = self._sort_by_priority_and_length(
                unique_results, exact_results, start_results, contain_results
            )

            # Limit results
            limited_results = sorted_results[: request.limit]

            # Convert to response format
            response_results = [self._entry_to_response(entry) for entry in limited_results]

            return SearchResponse(
                results=response_results,
                total_count=len(unique_results),
                query=query,
                message=f"Found {len(unique_results)} results for '{query}'",
            )

        except SearchException:
            raise
        except Exception as e:
            self._handle_db_error(e, "search")
            # This will never be reached due to exception, but needed for type checker
            return SearchResponse(results=[], total_count=0, query=request.query)

    def _get_exact_matches(self, query: str) -> list[Entry]:
        """Get exact matches for kanji and readings."""
        results = []

        # Exact kanji matches
        kanji_stmt = select(Entry).join(Kanji).where(Kanji.keb == query)
        kanji_results = self.session.exec(kanji_stmt).all()
        results.extend(kanji_results)

        # Exact reading matches
        reading_stmt = select(Entry).join(Reading).where(Reading.reb == query)
        reading_results = self.session.exec(reading_stmt).all()
        results.extend(reading_results)

        return results

    def _get_start_matches(self, query: str, include_rare: bool) -> list[Entry]:
        """Get words that start with the query."""
        results = []

        base_kanji_filter = col(Kanji.keb).like(f"{query}%") & (Kanji.keb != query)
        base_reading_filter = col(Reading.reb).like(f"{query}%") & (Reading.reb != query)

        if not include_rare:
            # Priority to common words
            kanji_stmt = (
                select(Entry)
                .join(Kanji)
                .where(base_kanji_filter & (Entry.is_common == True))
                .limit(5)
            )
            results.extend(self.session.exec(kanji_stmt).all())

            reading_stmt = (
                select(Entry)
                .join(Reading)
                .where(base_reading_filter & (Entry.is_common == True))
                .limit(5)
            )
            results.extend(self.session.exec(reading_stmt).all())

        # Add other words starting with query
        kanji_stmt = select(Entry).join(Kanji).where(base_kanji_filter).limit(10)
        results.extend(self.session.exec(kanji_stmt).all())

        reading_stmt = select(Entry).join(Reading).where(base_reading_filter).limit(10)
        results.extend(self.session.exec(reading_stmt).all())

        return results

    def _get_contain_matches(self, query: str, include_rare: bool) -> list[Entry]:
        """Get common words containing the query."""
        results = []

        if not include_rare:
            # Only common words containing query (not starting with it)
            kanji_stmt = (
                select(Entry)
                .join(Kanji)
                .where(
                    col(Kanji.keb).like(f"%{query}%")
                    & (~col(Kanji.keb).like(f"{query}%"))
                    & (Entry.is_common == True)
                )
                .limit(10)
            )
            results.extend(self.session.exec(kanji_stmt).all())

        return results

    def _get_other_matches(self, query: str, include_rare: bool) -> list[Entry]:
        """Get other partial matches."""
        results = []

        # Other kanji matches
        kanji_stmt = (
            select(Entry)
            .join(Kanji)
            .where(
                col(Kanji.keb).like(f"%{query}%")
                & (Kanji.keb != query)
                & (~col(Kanji.keb).like(f"{query}%") | (Entry.is_common != True))
            )
            .limit(15)
        )
        results.extend(self.session.exec(kanji_stmt).all())

        # Other reading matches
        reading_stmt = (
            select(Entry)
            .join(Reading)
            .where(
                col(Reading.reb).like(f"%{query}%")
                & (Reading.reb != query)
                & (~col(Reading.reb).like(f"{query}%") | (Entry.is_common != True))
            )
            .limit(15)
        )
        results.extend(self.session.exec(reading_stmt).all())

        return results

    def _deduplicate_results(self, results: list[Entry]) -> list[Entry]:
        """Remove duplicate entries while preserving order."""
        seen = set()
        unique_results = []
        for entry in results:
            if entry.ent_seq not in seen:
                seen.add(entry.ent_seq)
                unique_results.append(entry)
        return unique_results

    def _sort_by_priority_and_length(
        self,
        unique_results: list[Entry],
        exact_results: list[Entry],
        start_results: list[Entry],
        contain_results: list[Entry],
    ) -> list[Entry]:
        """Sort results by priority groups and word length within groups."""

        def get_sort_key(entry):
            kanji_len = min([len(k.keb) for k in entry.kanjis]) if entry.kanjis else 999
            reading_len = min([len(r.reb) for r in entry.readings]) if entry.readings else 999
            return min(kanji_len, reading_len)

        final_results = []
        current_group = []
        last_priority = None

        for entry in unique_results:
            # Determine priority group
            if entry in exact_results:
                priority = 1
            elif entry in start_results:
                priority = 2
            elif entry in contain_results:
                priority = 3
            else:
                priority = 4

            # If priority changed, sort current group and add to final results
            if last_priority is not None and priority != last_priority:
                current_group.sort(key=get_sort_key)
                final_results.extend(current_group)
                current_group = []

            current_group.append(entry)
            last_priority = priority

        # Don't forget the last group
        if current_group:
            current_group.sort(key=get_sort_key)
            final_results.extend(current_group)

        return final_results

    def _entry_to_response(self, entry: Entry) -> DictionaryEntryResponse:
        """Convert Entry model to response format."""
        # Primary kanji & reading
        primary_kanji = entry.kanjis[0].keb if entry.kanjis else None
        primary_reading = entry.readings[0].reb if entry.readings else None

        # Other forms
        other_forms = []
        for r in entry.readings:
            if r.reb != primary_reading:
                other_forms.append(r.reb)
        for k in entry.kanjis:
            if k.keb != primary_kanji:
                other_forms.append(k.keb)

        # Variants
        variants = []
        for k in entry.kanjis:
            for r in entry.readings:
                variants.append({"kanji": k.keb, "reading": r.reb})

        # Meanings
        meanings = []
        for s in entry.senses:
            defs = [g.text for g in s.glosses if g.lang == "eng"]
            pos_list = s.pos.split("; ") if s.pos else []

            # Examples
            examples = []
            for ex in s.examples:
                try:
                    ex_obj = json.loads(ex.text)
                    examples.append(ex_obj)
                except Exception:
                    pass

            meaning_obj = MeaningResponse(
                pos=pos_list, definitions=defs, examples=examples, notes=[]
            )
            meanings.append(meaning_obj)

        return DictionaryEntryResponse(
            word=primary_kanji or primary_reading or "Unknown",
            reading=primary_reading,
            is_common=bool(entry.is_common) if hasattr(entry, "is_common") else False,
            jlpt_level=entry.jlpt_level if hasattr(entry, "jlpt_level") else None,
            meanings=meanings,
            other_forms=other_forms,
            tags=["common word"] if hasattr(entry, "is_common") and entry.is_common else [],
            variants=variants,
        )
