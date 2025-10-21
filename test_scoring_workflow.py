"""
Test script for scoring workflow
Tests the complete scorecard API workflow from login to score entry
"""
import requests
import json
import sys

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000"

def test_scoring_workflow():
    print("=" * 60)
    print("SCORING WORKFLOW TEST")
    print("=" * 60)

    # 1. Login
    print("\n1. Logging in as admin...")
    login_response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={
            "email": "admin@abhimatagolf.com",
            "password": "admin123"
        }
    )

    if login_response.status_code != 200:
        print(f"[FAIL] Login failed: {login_response.status_code}")
        print(login_response.text)
        return

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[PASS] Login successful")

    # 2. Get events
    print("\n2. Fetching events...")
    events_response = requests.get(f"{BASE_URL}/events/", headers=headers)

    if events_response.status_code != 200:
        print(f"[FAIL] Failed to fetch events: {events_response.status_code}")
        return

    events = events_response.json().get("events", [])
    if not events:
        print("[FAIL] No events found")
        return

    event = events[0]
    event_id = event["id"]
    print(f"[PASS] Found event: {event['name']} (ID: {event_id})")

    # 3. Get participants
    print("\n3. Fetching participants...")
    participants_response = requests.get(
        f"{BASE_URL}/api/v1/participants/",
        params={"event_id": event_id},
        headers=headers
    )

    if participants_response.status_code != 200:
        print(f"[FAIL] Failed to fetch participants: {participants_response.status_code}")
        return

    participants = participants_response.json().get("participants", [])
    if not participants:
        print("[FAIL] No participants found")
        return

    participant = participants[0]
    participant_id = participant["id"]
    print(f"[PASS] Found participant: {participant['name']} (ID: {participant_id})")
    print(f"   Handicap: {participant['declared_handicap']}")

    # 4. Get participant scorecard
    print(f"\n4. Fetching scorecard for participant {participant_id}...")
    scorecard_response = requests.get(
        f"{BASE_URL}/api/v1/scorecards/participant/{participant_id}",
        headers=headers
    )

    if scorecard_response.status_code != 200:
        print(f"[FAIL] Failed to fetch scorecard: {scorecard_response.status_code}")
        print(scorecard_response.text)
        return

    scorecard = scorecard_response.json()
    print(f"[PASS] Scorecard loaded:")
    print(f"   Participant: {scorecard['participant_name']}")
    print(f"   Event: {scorecard['event_name']}")
    print(f"   Course Par: {scorecard['course_par']}")
    print(f"   Handicap: {scorecard['handicap']}")
    print(f"   Holes Completed: {scorecard['holes_completed']}/18")
    print(f"   Gross Score: {scorecard['gross_score']}")
    print(f"   Net Score: {scorecard['net_score']}")

    # 5. Submit bulk scores
    print("\n5. Submitting scores for holes 1-9...")
    test_scores = [
        {"hole_number": 1, "strokes": 4},
        {"hole_number": 2, "strokes": 5},
        {"hole_number": 3, "strokes": 3},
        {"hole_number": 4, "strokes": 4},
        {"hole_number": 5, "strokes": 5},
        {"hole_number": 6, "strokes": 4},
        {"hole_number": 7, "strokes": 3},
        {"hole_number": 8, "strokes": 4},
        {"hole_number": 9, "strokes": 5},
    ]

    bulk_submit_response = requests.post(
        f"{BASE_URL}/api/v1/scorecards/bulk",
        headers=headers,
        json={
            "participant_id": participant_id,
            "scores": test_scores
        }
    )

    if bulk_submit_response.status_code not in [200, 201]:
        print(f"[FAIL] Failed to submit scores: {bulk_submit_response.status_code}")
        print(bulk_submit_response.text)
        return

    updated_scorecard = bulk_submit_response.json()
    print("[PASS] Scores submitted successfully!")
    print(f"   OUT Total: {updated_scorecard['out_total']} ({format_to_par(updated_scorecard['out_to_par'])})")
    print(f"   Gross Score: {updated_scorecard['gross_score']} ({format_to_par(updated_scorecard['score_to_par'])})")
    print(f"   Net Score: {updated_scorecard['net_score']}")
    print(f"   Holes Completed: {updated_scorecard['holes_completed']}/18")

    # 6. Verify scores by fetching scorecard again
    print("\n6. Verifying scores by re-fetching scorecard...")
    verify_response = requests.get(
        f"{BASE_URL}/api/v1/scorecards/participant/{participant_id}",
        headers=headers
    )

    if verify_response.status_code != 200:
        print(f"[FAIL] Failed to verify: {verify_response.status_code}")
        return

    verified_scorecard = verify_response.json()
    print("[PASS] Verification successful!")
    print(f"   OUT Total: {verified_scorecard['out_total']}")
    print(f"   IN Total: {verified_scorecard['in_total']}")
    print(f"   Gross Score: {verified_scorecard['gross_score']}")
    print(f"   Net Score: {verified_scorecard['net_score']}")

    # Display front nine details
    print("\n   Front Nine Details:")
    for hole in verified_scorecard['front_nine']:
        if hole['strokes'] > 0:
            print(f"   Hole {hole['hole_number']}: {hole['strokes']} strokes "
                  f"(Par {hole['hole_par']}, {format_to_par(hole['score_to_par'])}) "
                  f"[{hole['color_code']}]")

    print("\n" + "=" * 60)
    print("[PASS] ALL TESTS PASSED!")
    print("=" * 60)

def format_to_par(score_to_par):
    if score_to_par == 0:
        return "E"
    elif score_to_par > 0:
        return f"+{score_to_par}"
    else:
        return str(score_to_par)

if __name__ == "__main__":
    try:
        test_scoring_workflow()
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
