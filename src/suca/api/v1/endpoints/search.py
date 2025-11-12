import json
from fastapi import APIRouter, Depends, HTTPException
from typing import Any
from sqlmodel import Session, select, col, SQLModel
from sqlalchemy import or_
from src.suca.api.deps import get_session
from src.suca.db.model import Entry, Kanji, Reading

# Response models
class MeaningResponse(SQLModel):
    pos: list[str]
    definitions: list[str]
    examples: list[dict]
    notes: list[str]

class DictionaryEntryResponse(SQLModel):
    word: str
    reading: str | None
    is_common: bool
    jlpt_level: str | None
    meanings: list[MeaningResponse]
    other_forms: list[str]
    tags: list[str]
    variants: list[dict]

class SearchResponse(SQLModel):
    results: list[DictionaryEntryResponse]
    total_count: int

router = APIRouter(prefix="/search", tags=["Search"])

def _to_jisho(entry: Entry) -> DictionaryEntryResponse:
    """Convert a single Entry to Jisho-style dictionary format"""
    # --- primary kanji & reading ---
    primary_kanji = entry.kanjis[0].keb if entry.kanjis else None
    primary_reading = entry.readings[0].reb if entry.readings else None

    # --- other forms ---
    other_forms = []
    for r in entry.readings:
        if r.reb != primary_reading:
            other_forms.append(r.reb)
    for k in entry.kanjis:
        if k.keb != primary_kanji:
            other_forms.append(k.keb)

    # --- variants ---
    variants = []
    for k in entry.kanjis:
        for r in entry.readings:
            variants.append({"kanji": k.keb, "reading": r.reb})

    # --- meanings ---
    meanings = []
    for s in entry.senses:
        defs = [g.text for g in s.glosses if g.lang == "eng"]
        pos_list = s.pos.split("; ") if s.pos else []

        # examples: JSON {"japanese": ..., "english": ...}
        examples = []
        for ex in s.examples:
            try:
                ex_obj = json.loads(ex.text)
                examples.append(ex_obj)
            except Exception:
                pass

        meaning_obj = MeaningResponse(
            pos=pos_list,
            definitions=defs,
            examples=examples,
            notes=[]
        )
        meanings.append(meaning_obj)

    return DictionaryEntryResponse(
        word=primary_kanji or primary_reading or "Unknown",
        reading=primary_reading,
        is_common=bool(entry.is_common) if hasattr(entry, 'is_common') else False,
        jlpt_level=entry.jlpt_level if hasattr(entry, 'jlpt_level') else None,
        meanings=meanings,
        other_forms=other_forms,
        tags=["common word"] if hasattr(entry, 'is_common') and entry.is_common else [],
        variants=variants
    )


@router.get("", response_model=SearchResponse)
def search(q: str, session: Session = Depends(get_session)) -> SearchResponse:
    """
    Search dictionary entries with intelligent prioritization:
    1. Exact matches (行 = 行)
    2. Common words starting with query (行 → 行く, 行き)  
    3. Common words containing query (行 → 銀行, 旅行)
    4. All other partial matches
    """
    if not q:
        raise HTTPException(status_code=400, detail="q (query) is required")
    
    # Debug: Let's see what we can find for words starting with the query
    debug_stmt = select(Entry).join(Kanji).where(col(Kanji.keb).like(f"{q}%")).limit(5)
    debug_results = session.exec(debug_stmt).all()
    print(f"DEBUG: Found {len(debug_results)} entries starting with '{q}':")
    for entry in debug_results:
        kanji_list = [k.keb for k in entry.kanjis]
        reading_list = [r.reb for r in entry.readings] 
        print(f"  - {kanji_list} ({reading_list}) - is_common: {getattr(entry, 'is_common', 'N/A')}")

    all_results = []
    
    # Priority 1: Exact matches (highest priority)
    exact_results = []
    
    # Exact kanji matches
    exact_kanji_stmt = select(Entry).join(Kanji).where(Kanji.keb == q)
    exact_kanji_results = session.exec(exact_kanji_stmt).all()
    exact_results.extend(exact_kanji_results)
    
    # Exact reading matches
    exact_reading_stmt = select(Entry).join(Reading).where(Reading.reb == q)
    exact_reading_results = session.exec(exact_reading_stmt).all()
    exact_results.extend(exact_reading_results)
    
    # Priority 2: Words that START with the query (regardless of common flag first)
    start_results = []
    
    # Words starting with kanji (try common first, then all)
    start_kanji_common_stmt = select(Entry).join(Kanji).where(
        col(Kanji.keb).like(f"{q}%") & 
        (Kanji.keb != q) & 
        (Entry.is_common == True)
    ).limit(5)
    start_kanji_common = session.exec(start_kanji_common_stmt).all()
    start_results.extend(start_kanji_common)
    
    # If we don't have enough common ones, add any words starting with kanji
    start_kanji_any_stmt = select(Entry).join(Kanji).where(
        col(Kanji.keb).like(f"{q}%") & 
        (Kanji.keb != q)
    ).limit(10)
    start_kanji_any = session.exec(start_kanji_any_stmt).all()
    start_results.extend(start_kanji_any)
    
    # Words starting with reading (try common first, then all)
    start_reading_common_stmt = select(Entry).join(Reading).where(
        col(Reading.reb).like(f"{q}%") & 
        (Reading.reb != q) & 
        (Entry.is_common == True)
    ).limit(5)
    start_reading_common = session.exec(start_reading_common_stmt).all()
    start_results.extend(start_reading_common)
    
    # If we don't have enough common ones, add any words starting with reading
    start_reading_any_stmt = select(Entry).join(Reading).where(
        col(Reading.reb).like(f"{q}%") & 
        (Reading.reb != q)
    ).limit(10)
    start_reading_any = session.exec(start_reading_any_stmt).all()
    start_results.extend(start_reading_any)
    
    # Priority 3: Common words containing the query (medium priority)
    common_contains_results = []
    
    # Common words containing kanji
    common_contains_kanji_stmt = select(Entry).join(Kanji).where(
        col(Kanji.keb).like(f"%{q}%") & 
        (~col(Kanji.keb).like(f"{q}%")) &  # Exclude words that start with query
        (Entry.is_common == True)
    ).limit(10)
    common_contains_kanji = session.exec(common_contains_kanji_stmt).all()
    common_contains_results.extend(common_contains_kanji)
    
    # Priority 4: All other partial matches (lower priority)
    other_partial_results = []
    
    # Other kanji matches (not common, not starting with query)
    other_kanji_stmt = select(Entry).join(Kanji).where(
        col(Kanji.keb).like(f"%{q}%") & 
        (Kanji.keb != q) & 
        (~col(Kanji.keb).like(f"{q}%") | (Entry.is_common != True))
    ).limit(15)
    other_kanji = session.exec(other_kanji_stmt).all()
    other_partial_results.extend(other_kanji)
    
    # Other reading matches
    other_reading_stmt = select(Entry).join(Reading).where(
        col(Reading.reb).like(f"%{q}%") & 
        (Reading.reb != q) & 
        (~col(Reading.reb).like(f"{q}%") | (Entry.is_common != True))
    ).limit(15)
    other_reading = session.exec(other_reading_stmt).all()
    other_partial_results.extend(other_reading)
    
    # Combine results in priority order
    all_results = exact_results + start_results + common_contains_results + other_partial_results
    
    # Remove duplicates while preserving order (priority)
    seen = set()
    unique_results = []
    for entry in all_results:
        if entry.ent_seq not in seen:
            seen.add(entry.ent_seq)
            unique_results.append(entry)
    
    if not unique_results:
        raise HTTPException(status_code=404, detail="Word not found")
    
    # Additional sorting within priority groups by word length (shorter = more common)
    def get_sort_key(entry):
        # Get shortest kanji/reading for sorting
        kanji_len = min([len(k.keb) for k in entry.kanjis]) if entry.kanjis else 999
        reading_len = min([len(r.reb) for r in entry.readings]) if entry.readings else 999
        return min(kanji_len, reading_len)
    
    # Sort each priority group by length, but preserve overall priority
    final_results = []
    current_group = []
    last_priority = None
    
    for i, entry in enumerate(unique_results):
        # Determine which priority group this entry belongs to
        if entry in exact_results:
            priority = 1
        elif entry in start_results:
            priority = 2  
        elif entry in common_contains_results:
            priority = 3
        else:
            priority = 4
            
        # If priority changed, sort the current group and add to final results
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
    
    # Always return multiple results format for consistency
    return SearchResponse(
        results=[_to_jisho(entry) for entry in final_results[:10]],  # Show top 10 results
        total_count=len(unique_results)
    )
