import json
from fastapi import APIRouter, Depends, HTTPException
from typing import Any
from sqlmodel import Session, select
from suca.db.db import get_session
from suca.db.model import Entry, Kanji, Reading

router = APIRouter(prefix="/search", tags=["Search"])

def _to_jisho(entry: Entry) -> dict:
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

        meaning_obj = {
            "pos": pos_list,
            "definitions": defs,
            "examples": examples,
            "notes": []
        }
        meanings.append(meaning_obj)

    out = {
        "word": primary_kanji or primary_reading,
        "reading": primary_reading,
        "is_common": bool(entry.is_common),
        "jlpt_level": entry.jlpt_level,
        "meanings": meanings,
        "other_forms": other_forms,
        "tags": ["common word"] if entry.is_common else [],
        "variants": variants
    }
    return out


@router.get("")
def search(q: str, session: Session = Depends(get_session)) -> Any:
    if not q:
        raise HTTPException(status_code=400, detail="q (query) is required")

    # exact match in kanji or readings
    stmt = select(Entry).where(
        Entry.ent_seq.in_(select(Kanji.entry_id).where(Kanji.keb == q))
        | Entry.ent_seq.in_(select(Reading.entry_id).where(Reading.reb == q))
    )
    result = session.exec(stmt).first()

    if not result:
        # partial match: kanji contains or reading contains
        stmt2 = select(Entry).where(
            Entry.ent_seq.in_(select(Kanji.entry_id).where(Kanji.keb.like(f"%{q}%")))
            | Entry.ent_seq.in_(select(Reading.entry_id).where(Reading.reb.like(f"%{q}%")))
        )
        result = session.exec(stmt2).first()
        if not result:
            raise HTTPException(status_code=404, detail="Word not found")

    return _to_jisho(result)
