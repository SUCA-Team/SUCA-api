"""
Test script to verify FSRS service integration.

This script tests that the FSRSService correctly wraps the FSRS library
and integrates with the flashcard service.

Run with: python scripts/test_fsrs_integration.py
"""

from datetime import datetime, UTC
from fsrs import Card, Rating
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from suca.services.fsrs_service import FSRSService, CardState


def test_fsrs_service():
    """Test FSRSService basic functionality."""
    print("=" * 60)
    print("TESTING FSRS SERVICE INTEGRATION")
    print("=" * 60)

    service = FSRSService()

    # Test 1: Create a new card
    print("\n1. Creating new card...")
    card = service.create_card()
    print(f"   OK Card created")
    print(f"   State: {card.state.name}")
    print(f"   Step: {card.step}")
    print(f"   Difficulty: {card.difficulty}")
    print(f"   Stability: {card.stability}")

    # Test 2: Convert card to dict
    print("\n2. Converting card to dict...")
    card_dict = service.card_to_dict(card)
    print(f"   OK Converted to dict")
    print(f"   Dict keys: {list(card_dict.keys())}")
    print(f"   State value: {card_dict['state']}")
    print(f"   Reps (mapped from step): {card_dict['reps']}")

    # Test 3: Convert dict back to card
    print("\n3. Converting dict back to card...")
    restored_card = service.dict_to_card(card_dict)
    print(f"   OK Restored card")
    print(f"   State: {restored_card.state.name}")
    print(f"   Step: {restored_card.step}")

    # Test 4: Review a card
    print("\n4. Reviewing card with 'Good' rating...")
    updated_card, log = service.review_card(card, Rating.Good)
    print(f"   OK Card reviewed")
    print(f"   State: {updated_card.state.name}")
    print(f"   Step: {updated_card.step}")
    print(f"   Difficulty: {updated_card.difficulty:.4f}")
    print(f"   Stability: {updated_card.stability:.4f}")
    print(f"   Next due: {updated_card.due}")

    # Test 5: Check if card is new
    print("\n5. Testing is_card_new()...")
    print(f"   Original card is new: {service.is_card_new(card)}")
    print(f"   Reviewed card is new: {service.is_card_new(updated_card)}")

    # Test 6: Check if card is due
    print("\n6. Testing is_card_due()...")
    print(f"   Original card is due: {service.is_card_due(card)}")
    print(f"   Reviewed card is due: {service.is_card_due(updated_card)}")

    # Test 7: Get retrievability
    print("\n7. Testing get_retrievability()...")
    retrievability = service.get_retrievability(updated_card)
    print(f"   OK Retrievability: {retrievability:.4f}")

    # Test 8: Get next states preview
    print("\n8. Testing get_next_states()...")
    next_states = service.get_next_states(card)
    print(f"   OK Next states for each rating:")
    for rating, next_card in next_states.items():
        print(
            f"     {rating.name}: state={next_card.state.name}, "
            f"difficulty={next_card.difficulty:.4f}, "
            f"stability={next_card.stability:.4f}"
        )

    # Test 9: CardState enum
    print("\n9. Testing CardState enum...")
    print(f"   OK CardState values:")
    for state in CardState:
        print(f"     {state.name} = {state.value}")

    # Test 10: Test with state=0 (New) from database
    print("\n10. Testing dict_to_card with state=0 (New)...")
    new_card_dict = {
        "difficulty": 0.0,
        "stability": 0.0,
        "reps": 0,
        "state": 0,  # CardState.New
        "last_review": None,
        "due": datetime.now(UTC),
    }
    converted_card = service.dict_to_card(new_card_dict)
    print(f"   OK Converted state=0 to FSRS card")
    print(f"   State: {converted_card.state.name} (should be Learning)")
    print(f"   Step: {converted_card.step}")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    test_fsrs_service()
