from fastapi import APIRouter, Request
import requests

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("")
async def search_word(request: Request, q: str | None = None) -> dict:
    if q is None:
        return {
            "notification": "Please enter a word!"
        }

    ip = q
    rows = await request.app.state.db.fetch("""
        WITH word_data AS (
            SELECT 
                e.ent_seq,
                (SELECT string_agg(keb, ', ') FROM kanji WHERE entry_id = e.ent_seq) AS kanji,
                (SELECT string_agg(reb, ', ') FROM readings WHERE entry_id = e.ent_seq) AS readings
            FROM entries e
            WHERE EXISTS (
                SELECT 1 FROM kanji WHERE entry_id = e.ent_seq AND keb = $1
            ) OR EXISTS (
                SELECT 1 FROM readings WHERE entry_id = e.ent_seq AND reb = $1
            )
        )
        SELECT 
            w.ent_seq,
            w.kanji,
            w.readings,
            s.sense_order,
            s.gloss,
            s.pos
        FROM word_data w
        JOIN senses s ON w.ent_seq = s.entry_id
        ORDER BY s.sense_order;
    """, ip)

    if not rows:
        return {
            "notification": "Please enter a word!"
        }

    kanji_list = rows[0]["kanji"].split(", ") if rows[0]["kanji"] else []
    reading_list = rows[0]["readings"].split(", ") if rows[0]["readings"] else []

    meanings = {}
    for row in rows:
        pos_text = row["pos"] if row["pos"] else "Other"
        gloss = row["gloss"]

        if pos_text not in meanings:
            meanings[pos_text] = []

        if gloss not in meanings[pos_text]:
            meanings[pos_text].append(gloss)

    meanings_list = []
    for pos, defs in meanings.items():
        numbered_defs = [f"{i+1}. {d}" for i, d in enumerate(defs)]
        meanings_list.append({"pos": pos, "definitions": numbered_defs})

    url = "https://tatoeba.org/en/api_v0/search?query=" + ip + "&from=jpn&to=eng"
    req = requests.get(url).json()
    results = req.get("results", [])

    examples = []
    for item in results[:5]:
        jp = item.get('text', '')
        translations = item.get('translations', [])
        if translations and translations[0]:
            en_raw = translations[0][0].get('text', '')
            en = en_raw.replace('\\"', '"')
        else:
            en = ""
        examples.append({"jp": jp, "en": en})

    return {
        "word": ip,
        "kanji": kanji_list,
        "reading": reading_list,
        "meanings": meanings_list,
        "examples": examples
    }