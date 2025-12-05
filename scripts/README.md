# Scripts Directory

This directory contains utility scripts for the SUCA API project.

## Available Scripts

### `demo_fsrs.py`
**Interactive FSRS Flashcard Demo Application**

A standalone command-line application demonstrating the FSRS (Free Spaced Repetition Scheduler) algorithm with flashcard management.

**Features:**
- Multi-user support with JSON file storage
- Add and review flashcards
- Automatic scheduling based on FSRS algorithm
- Statistics and card listing
- User management (create, switch, delete)

**Usage:**
```bash
python scripts/demo_fsrs.py
```

**Storage:** Creates `flashcards_demo_data.json` in the scripts directory.

---

### `test_fsrs_integration.py`
**FSRS Service Integration Tests**

Tests the FSRSService wrapper to ensure proper integration with the FSRS library.

**Tests:**
- Card creation and initialization
- Card-to-dict and dict-to-card conversion
- Card review with different ratings
- Retrievability calculation
- State management (New, Learning, Review, Relearning)
- Database compatibility (state=0 mapping)

**Usage:**
```bash
python scripts/test_fsrs_integration.py
```

**Expected output:** All tests should pass, confirming the service works correctly.

---

### `create_sample_data.py`
Creates sample dictionary data for development and testing.

---

### `parse_jmdict.py`
Parses JMDict XML data and imports it into the database.

---

## Notes

- The demo and test scripts are independent of the main API application
- They use the same FSRS service implementation as the production API
- Demo data is stored separately from production data
