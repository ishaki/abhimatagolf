"""
Test script for Scorecard API endpoints
Tests all scorecard CRUD operations and calculations
"""

import requests
import json

BASE_URL = "http://localhost:8000"

# Test credentials
ADMIN_EMAIL = "admin@abhimatagolf.com"
ADMIN_PASSWORD = "admin123"

def print_result(test_name, success, message=""):
    """Print test result"""
    status = "[OK]" if success else "[FAIL]"
    print(f"{status} {test_name}")
    if message:
        print(f"    {message}")
    print()

def login():
    """Login and get JWT token"""
    print("=" * 60)
    print("AUTHENTICATING...")
    print("=" * 60)

    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )

    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print_result("Login", True, f"Token: {token[:20]}...")
        return token
    else:
        print_result("Login", False, f"Status: {response.status_code}")
        return None

def get_test_data(token):
    """Get first event and participant for testing"""
    print("=" * 60)
    print("GETTING TEST DATA...")
    print("=" * 60)

    headers = {"Authorization": f"Bearer {token}"}

    # Get events
    response = requests.get(f"{BASE_URL}/events/", headers=headers)
    if response.status_code != 200:
        print_result("Get Events", False, f"Status: {response.status_code}")
        return None, None

    events_data = response.json()
    events = events_data.get("events", [])
    if not events:
        print_result("Get Events", False, "No events found")
        return None, None

    event = events[0]
    event_id = event.get("id")
    print_result("Get Event", True, f"Event ID: {event_id}, Name: {event.get('name')}")

    # Get participants for this event
    response = requests.get(
        f"{BASE_URL}/api/v1/participants/",
        params={"event_id": event_id},
        headers=headers
    )

    if response.status_code != 200:
        print_result("Get Participants", False, f"Status: {response.status_code}")
        return event_id, None

    participants_data = response.json()
    participants = participants_data.get("participants", [])

    # If no participants, create one for testing
    if not participants:
        print("No participants found, creating test participant...")

        # Create test participant
        create_response = requests.post(
            f"{BASE_URL}/api/v1/participants/",
            json={
                "name": "Test Golfer",
                "email": "test.golfer@example.com",
                "phone": "+1234567890",
                "event_id": event_id,
                "handicap": 12.0,
                "division": "Championship",
                "is_vip": False
            },
            headers=headers
        )

        if create_response.status_code != 201:
            print_result("Create Test Participant", False, f"Status: {create_response.status_code}, Response: {create_response.text}")
            return event_id, None

        participant = create_response.json()
        participant_id = participant.get("id")
        print_result("Create Test Participant", True, f"Created participant ID: {participant_id}")
    else:
        participant = participants[0]
        participant_id = participant.get("id")
    print_result(
        "Get Participant",
        True,
        f"Participant ID: {participant_id}, Name: {participant.get('name')}, Handicap: {participant.get('handicap')}"
    )

    return event_id, participant_id

def test_submit_single_hole_score(token, participant_id):
    """Test submitting a single hole score"""
    print("=" * 60)
    print("TEST: Submit Single Hole Score")
    print("=" * 60)

    headers = {"Authorization": f"Bearer {token}"}

    # Submit score for hole 1
    response = requests.post(
        f"{BASE_URL}/api/v1/scorecards/",
        params={
            "participant_id": participant_id,
            "hole_number": 1,
            "strokes": 5
        },
        headers=headers
    )

    if response.status_code == 201:
        data = response.json()
        print_result(
            "Submit Hole 1 Score",
            True,
            f"Hole: {data.get('hole_number')}, Par: {data.get('hole_par')}, "
            f"Strokes: {data.get('strokes')}, To Par: {data.get('score_to_par')}, "
            f"Color: {data.get('color_code')}"
        )
        return data.get("id")
    else:
        print_result("Submit Hole 1 Score", False, f"Status: {response.status_code}, Response: {response.text}")
        return None

def test_bulk_submit_scores(token, participant_id):
    """Test bulk submitting scores for all 18 holes"""
    print("=" * 60)
    print("TEST: Bulk Submit Scores (18 holes)")
    print("=" * 60)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Create scores for 18 holes (varied scores)
    scores = []
    for hole in range(1, 19):
        # Vary the scores: some pars, birdies, bogeys
        if hole % 5 == 0:
            strokes = 3  # Birdie on par 4
        elif hole % 3 == 0:
            strokes = 5  # Bogey on par 4
        else:
            strokes = 4  # Par on par 4

        scores.append({
            "hole_number": hole,
            "strokes": strokes
        })

    payload = {
        "participant_id": participant_id,
        "scores": scores
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/scorecards/bulk",
        json=payload,
        headers=headers
    )

    if response.status_code == 201:
        data = response.json()
        print_result(
            "Bulk Submit Scores",
            True,
            f"Participant: {data.get('participant_name')}, "
            f"Gross: {data.get('gross_score')}, Net: {data.get('net_score')}, "
            f"To Par: {data.get('score_to_par')}, Holes Completed: {data.get('holes_completed')}"
        )
        print(f"    OUT: {data.get('out_total')} ({data.get('out_to_par'):+d})")
        print(f"    IN:  {data.get('in_total')} ({data.get('in_to_par'):+d})")
        print()
        return True
    else:
        print_result("Bulk Submit Scores", False, f"Status: {response.status_code}, Response: {response.text}")
        return False

def test_get_participant_scorecard(token, participant_id):
    """Test getting complete scorecard for a participant"""
    print("=" * 60)
    print("TEST: Get Participant Scorecard")
    print("=" * 60)

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{BASE_URL}/api/v1/scorecards/participant/{participant_id}",
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        print_result(
            "Get Scorecard",
            True,
            f"Participant: {data.get('participant_name')}, Event: {data.get('event_name')}"
        )

        # Display front nine
        print("    FRONT NINE:")
        front_nine = data.get('front_nine', [])
        for hole in front_nine:
            print(f"      Hole {hole['hole_number']}: Par {hole['hole_par']}, "
                  f"Strokes {hole['strokes']}, {hole['score_to_par']:+d} ({hole['color_code']})")

        print(f"    OUT: {data.get('out_total')} ({data.get('out_to_par'):+d})\n")

        # Display back nine
        print("    BACK NINE:")
        back_nine = data.get('back_nine', [])
        for hole in back_nine:
            print(f"      Hole {hole['hole_number']}: Par {hole['hole_par']}, "
                  f"Strokes {hole['strokes']}, {hole['score_to_par']:+d} ({hole['color_code']})")

        print(f"    IN:  {data.get('in_total')} ({data.get('in_to_par'):+d})\n")

        print(f"    TOTAL: Gross {data.get('gross_score')}, Net {data.get('net_score')}, "
              f"To Par {data.get('score_to_par'):+d}")
        print()

        return True
    else:
        print_result("Get Scorecard", False, f"Status: {response.status_code}, Response: {response.text}")
        return False

def test_get_event_scorecards(token, event_id):
    """Test getting scorecards for all participants in an event"""
    print("=" * 60)
    print("TEST: Get Event Scorecards")
    print("=" * 60)

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{BASE_URL}/api/v1/scorecards/event/{event_id}",
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        scorecards = data.get('scorecards', [])
        print_result(
            "Get Event Scorecards",
            True,
            f"Total scorecards: {data.get('total')}"
        )

        for scorecard in scorecards:
            print(f"    {scorecard.get('participant_name')}: Gross {scorecard.get('gross_score')}, "
                  f"Net {scorecard.get('net_score')}, Holes {scorecard.get('holes_completed')}/18")
        print()

        return True
    else:
        print_result("Get Event Scorecards", False, f"Status: {response.status_code}, Response: {response.text}")
        return False

def test_update_hole_score(token, scorecard_id):
    """Test updating a hole score"""
    print("=" * 60)
    print("TEST: Update Hole Score")
    print("=" * 60)

    if not scorecard_id:
        print_result("Update Score", False, "No scorecard ID available")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "strokes": 6,
        "reason": "Score correction after review"
    }

    response = requests.put(
        f"{BASE_URL}/api/v1/scorecards/{scorecard_id}",
        json=payload,
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        print_result(
            "Update Score",
            True,
            f"Hole: {data.get('hole_number')}, New Strokes: {data.get('strokes')}, "
            f"To Par: {data.get('score_to_par')}, Color: {data.get('color_code')}"
        )
        return True
    else:
        print_result("Update Score", False, f"Status: {response.status_code}, Response: {response.text}")
        return False

def main():
    """Main test runner"""
    print("\n")
    print("="* 60)
    print(" SCORECARD API TESTING")
    print("=" * 60)
    print()

    # Step 1: Login
    token = login()
    if not token:
        print("FAILED: Cannot proceed without authentication")
        return

    # Step 2: Get test data
    event_id, participant_id = get_test_data(token)
    if not event_id or not participant_id:
        print("FAILED: Cannot proceed without test data")
        print("Please ensure you have at least one event with participants")
        return

    # Step 3: Test single hole score submission
    scorecard_id = test_submit_single_hole_score(token, participant_id)

    # Step 4: Test bulk score submission (all 18 holes)
    test_bulk_submit_scores(token, participant_id)

    # Step 5: Test getting participant scorecard
    test_get_participant_scorecard(token, participant_id)

    # Step 6: Test getting event scorecards
    test_get_event_scorecards(token, event_id)

    # Step 7: Test updating a hole score
    if scorecard_id:
        test_update_hole_score(token, scorecard_id)

    print("=" * 60)
    print(" TESTING COMPLETE")
    print("=" * 60)
    print()

if __name__ == "__main__":
    main()
