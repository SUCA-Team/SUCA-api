#!/usr/bin/env python3
"""Create sample data for testing the search functionality."""

import os
import sys

from sqlmodel import Session

# Add src to path so we can import from our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.suca.db.db import engine, init_db
from src.suca.db.model import Entry, Gloss, Kanji, Reading, Sense
from src.suca.schemas.search import SearchRequest
from src.suca.services.search_service import SearchService


def create_sample_data():
    """Create sample Japanese dictionary entries for testing."""

    # Initialize database
    init_db()

    with Session(engine) as session:
        # Clear existing data (optional - comment out if you want to keep existing data)
        # session.exec(delete(Entry))
        # session.commit()

        # Sample entries
        sample_entries = [
            {
                "ent_seq": 1000000,
                "is_common": True,
                "jlpt_level": "N5",
                "kanjis": ["行く"],
                "readings": ["いく"],
                "senses": [{"pos": "verb", "glosses": ["to go", "to move"]}],
            },
            {
                "ent_seq": 1000001,
                "is_common": True,
                "jlpt_level": "N5",
                "kanjis": ["行き"],
                "readings": ["いき"],
                "senses": [{"pos": "noun", "glosses": ["going", "journey"]}],
            },
            {
                "ent_seq": 1000002,
                "is_common": True,
                "jlpt_level": "N4",
                "kanjis": ["銀行"],
                "readings": ["ぎんこう"],
                "senses": [{"pos": "noun", "glosses": ["bank", "banking institution"]}],
            },
            {
                "ent_seq": 1000003,
                "is_common": True,
                "jlpt_level": "N4",
                "kanjis": ["旅行"],
                "readings": ["りょこう"],
                "senses": [{"pos": "noun", "glosses": ["travel", "trip", "journey"]}],
            },
            {
                "ent_seq": 1000004,
                "is_common": True,
                "jlpt_level": "N5",
                "kanjis": ["行"],
                "readings": ["こう", "ぎょう"],
                "senses": [{"pos": "noun", "glosses": ["line", "row", "going"]}],
            },
            {
                "ent_seq": 1000005,
                "is_common": False,
                "jlpt_level": None,
                "kanjis": ["実行"],
                "readings": ["じっこう"],
                "senses": [{"pos": "noun", "glosses": ["execution", "implementation"]}],
            },
            {
                "ent_seq": 1000006,
                "is_common": True,
                "jlpt_level": "N5",
                "kanjis": ["水"],
                "readings": ["みず"],
                "senses": [{"pos": "noun", "glosses": ["water"]}],
            },
            {
                "ent_seq": 1000007,
                "is_common": True,
                "jlpt_level": "N5",
                "kanjis": ["食べる"],
                "readings": ["たべる"],
                "senses": [{"pos": "verb", "glosses": ["to eat", "to consume"]}],
            },
        ]

        for entry_data in sample_entries:
            # Create entry
            entry = Entry(
                ent_seq=entry_data["ent_seq"],
                is_common=entry_data["is_common"],
                jlpt_level=entry_data["jlpt_level"],
            )

            # Add kanjis
            for kanji_text in entry_data["kanjis"]:
                kanji = Kanji(keb=kanji_text, entry_id=entry.ent_seq)
                entry.kanjis.append(kanji)

            # Add readings
            for reading_text in entry_data["readings"]:
                reading = Reading(reb=reading_text, entry_id=entry.ent_seq)
                entry.readings.append(reading)

            # Add senses
            for sense_data in entry_data["senses"]:
                sense = Sense(entry_id=entry.ent_seq, pos=sense_data["pos"])

                # Add glosses
                for gloss_text in sense_data["glosses"]:
                    gloss = Gloss(
                        sense_id=None,  # Will be set after sense is saved
                        lang="eng",
                        text=gloss_text,
                    )
                    sense.glosses.append(gloss)

                entry.senses.append(sense)

            session.add(entry)

        session.commit()

        # Verify data was created
        from sqlmodel import select

        total_entries = len(session.exec(select(Entry)).all())
        print(f"✅ Created {total_entries} sample entries")

        # Test a few searches
        search_service = SearchService(session)

        test_queries = ["行", "行く", "銀行", "水"]
        for query in test_queries:
            request = SearchRequest(query=query, limit=5, include_rare=False)
            result = search_service.search_entries(request)
            print(f"🔍 Search '{query}': found {result.total_count} results")


if __name__ == "__main__":
    create_sample_data()
