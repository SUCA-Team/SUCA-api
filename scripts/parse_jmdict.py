# -*- coding: utf-8 -*-
"""
Parse JMdict XML and import into PostgreSQL using SQLModel.
Only English glosses are imported.
"""

import json
from lxml import etree
from sqlmodel import Session
from db import init_db, engine, get_session
from model import Entry, Kanji, Reading, Sense, Gloss, Example


# === CONFIG ===
JMDFILE = r"jm.db"  # Path to your JMdict file
BATCH_SIZE = 500
LIMIT_ENTRIES = 100  # For testing only — set None for full parse

PRIORITY_COMMON_KEYS = {
    "news1", "news2", "ichi1", "ichi2",
    "spec1", "spec2", "gai1", "gai2",
    "nf01", "nf02", "nf03"
}

# === HELPERS ===
def is_common_from_pris(pris):
    for p in pris:
        if not p:
            continue
        for token in p.split():
            if any(token.startswith(k) for k in PRIORITY_COMMON_KEYS):
                return True
    return False

def text_of(elem, tag):
    child = elem.find(tag)
    return child.text.strip() if child is not None and child.text else None

# === MAIN PARSER ===
def parse():
    print("🚀 Initializing database (creating tables if needed)...")
    init_db()

    # Open XML as bytes to avoid encoding issues
    with open(JMDFILE, "rb") as f:
        context = etree.iterparse(
            f,
            events=("end",),
            tag="entry",
            recover=True
        )

        session = get_session() if callable(get_session) else Session(engine)
        count = 0

        try:
            for _, entry_elem in context:
                # if LIMIT_ENTRIES and count >= LIMIT_ENTRIES:
                #     break

                ent_seq_text = entry_elem.findtext("ent_seq")
                if not ent_seq_text:
                    entry_elem.clear()
                    continue

                ent_seq = int(ent_seq_text.strip())
                count += 1

                # === Kanji elements ===
                kanjis, ke_pris = [], []
                for k_ele in entry_elem.findall("k_ele"):
                    keb = text_of(k_ele, "keb")
                    ke_inf = text_of(k_ele, "ke_inf")
                    ke_pri = text_of(k_ele, "ke_pri")
                    if keb:
                        kanjis.append({"keb": keb, "ke_inf": ke_inf, "ke_pri": ke_pri})
                    if ke_pri:
                        ke_pris.append(ke_pri)

                # === Reading elements ===
                readings, re_pris = [], []
                for r_ele in entry_elem.findall("r_ele"):
                    reb = text_of(r_ele, "reb")
                    re_nokanji = text_of(r_ele, "re_nokanji")
                    re_inf = text_of(r_ele, "re_inf")
                    re_pri = text_of(r_ele, "re_pri")
                    if reb:
                        readings.append({
                            "reb": reb,
                            "re_nokanji": re_nokanji,
                            "re_pri": re_pri,
                            "re_inf": re_inf
                        })
                    if re_pri:
                        re_pris.append(re_pri)

                is_common = is_common_from_pris(ke_pris + re_pris)
                entry_obj = Entry(ent_seq=ent_seq, is_common=is_common, jlpt_level=None)

                # Add kanjis
                for k in kanjis:
                    entry_obj.kanjis.append(
                        Kanji(
                            keb=k["keb"],
                            ke_inf=k["ke_inf"],
                            ke_pri=k["ke_pri"],
                            entry_id=ent_seq
                        )
                    )

                # Add readings
                for r in readings:
                    entry_obj.readings.append(
                        Reading(
                            reb=r["reb"],
                            re_nokanji=r["re_nokanji"],
                            re_pri=r["re_pri"],
                            re_inf=r["re_inf"],
                            entry_id=ent_seq
                        )
                    )

                # === Sense & Gloss & Example ===
                for s_elem in entry_elem.findall("sense"):
                    pos_text = "; ".join([p.text.strip() for p in s_elem.findall("pos") if p.text]) or None
                    field_text = "; ".join([f.text.strip() for f in s_elem.findall("field") if f.text]) or None
                    misc_text = "; ".join([m.text.strip() for m in s_elem.findall("misc") if m.text]) or None

                    sense_obj = Sense(entry_id=ent_seq, pos=pos_text, field=field_text, misc=misc_text)

                    # English gloss only
                    for gloss in s_elem.findall("gloss"):
                        lang = gloss.get("{http://www.w3.org/XML/1998/namespace}lang") or "eng"
                        if lang.lower().startswith("eng"):
                            text = (gloss.text or "").strip()
                            if text:
                                sense_obj.glosses.append(Gloss(lang="eng", text=text))

                    # Examples
                    for example in s_elem.findall("example"):
                        jp_sentence = None
                        eng_sentence = None
                        for ex_sent in example.findall("ex_sent"):
                            lang = ex_sent.get("{http://www.w3.org/XML/1998/namespace}lang")
                            if lang == "jpn":
                                jp_sentence = ex_sent.text.strip() if ex_sent.text else None
                            elif lang == "eng":
                                eng_sentence = ex_sent.text.strip() if ex_sent.text else None
                        if jp_sentence or eng_sentence:
                            sense_obj.examples.append(
                                Example(text=json.dumps({"japanese": jp_sentence, "english": eng_sentence}))
                            )

                    # Append sense to entry
                    entry_obj.senses.append(sense_obj)

                # Add to session
                session.add(entry_obj)

                # Batch commit
                if count % BATCH_SIZE == 0:
                    session.commit()
                    print(f"💾 Committed {count} entries...")
                    session.expunge_all()

                # Free memory
                entry_elem.clear()
                while entry_elem.getprevious() is not None:
                    del entry_elem.getparent()[0]

            session.commit()
            print(f"✅ Finished parsing. Total entries parsed: {count}")

        finally:
            session.close()

if __name__ == "__main__":
    parse()
