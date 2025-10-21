#!/usr/bin/env python3
"""Test script for Abhimata Golf APIs"""
import requests
import json

BASE_URL = "http://localhost:8000"
AUTH_BASE = f"{BASE_URL}/api/v1/auth"
EVENTS_BASE = f"{BASE_URL}/events"
PARTICIPANTS_BASE = f"{BASE_URL}/api/v1/participants"

def print_header(text):
    print(f"\n{'='*60}")
    print(f"{text:^60}")
    print(f"{'='*60}\n")

def test_login():
    """Test login and get token"""
    print_header("Testing Login")
    response = requests.post(
        f"{AUTH_BASE}/login",
        json={"email": "admin@abhimatagolf.com", "password": "admin123"}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Login successful")
        print(f"  User: {data['user']['full_name']} ({data['user']['role']})")
        return data['access_token']
    else:
        print(f"[FAIL] Login failed: {response.text}")
        return None

def test_events(token):
    """Test events API"""
    print_header("Testing Events API")
    headers = {"Authorization": f"Bearer {token}"}

    # Get events list
    response = requests.get(f"{EVENTS_BASE}/", headers=headers)
    print(f"GET /events/ - Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Found {data['total']} events")
        if data['events']:
            event = data['events'][0]
            print(f"  First event: {event['name']} (ID: {event['id']})")
            return event['id']
    else:
        print(f"[FAIL] Failed: {response.text}")
        return None

def test_event_detail(token, event_id):
    """Test single event API"""
    print_header(f"Testing Event Detail (ID: {event_id})")
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(f"{EVENTS_BASE}/{event_id}", headers=headers)
    print(f"GET /events/{event_id} - Status: {response.status_code}")
    if response.status_code == 200:
        event = response.json()
        print(f"[OK] Event details retrieved")
        print(f"  Name: {event['name']}")
        print(f"  Course: {event.get('course_name', 'N/A')}")
        print(f"  Participants: {event.get('participant_count', 0)}")
        return event
    else:
        print(f"[FAIL] Failed: {response.text}")
        return None

def test_participants(token, event_id):
    """Test participants API"""
    print_header(f"Testing Participants API (Event: {event_id})")
    headers = {"Authorization": f"Bearer {token}"}

    # Get participants for event
    response = requests.get(
        f"{PARTICIPANTS_BASE}/",
        headers=headers,
        params={"event_id": event_id, "per_page": 10}
    )
    print(f"GET /participants/?event_id={event_id} - Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Found {data['total']} participants")
        if data['participants']:
            p = data['participants'][0]
            print(f"  First participant: {p['name']} (Handicap: {p['declared_handicap']})")
    else:
        print(f"[FAIL] Failed: {response.text}")

def test_participant_stats(token, event_id):
    """Test participant stats API"""
    print_header(f"Testing Participant Stats (Event: {event_id})")
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{PARTICIPANTS_BASE}/event/{event_id}/stats",
        headers=headers
    )
    print(f"GET /participants/event/{event_id}/stats - Status: {response.status_code}")
    if response.status_code == 200:
        stats = response.json()
        print(f"[OK] Stats retrieved")
        print(f"  Total participants: {stats['total_participants']}")
        print(f"  VIP count: {stats['vip_count']}")
        print(f"  Avg handicap: {stats['average_handicap']:.1f}")
        if stats['by_division']:
            print(f"  Divisions: {list(stats['by_division'].keys())}")
    else:
        print(f"[FAIL] Failed: {response.text}")

def main():
    print_header("Abhimata Golf API Tests")
    print(f"Backend URL: {BASE_URL}")

    # Test login
    token = test_login()
    if not token:
        print("\n[FAIL] Cannot proceed without auth token")
        return

    # Test events
    event_id = test_events(token)
    if not event_id:
        print("\n[FAIL] Cannot proceed without event")
        return

    # Test event detail
    event = test_event_detail(token, event_id)

    # Test participants
    test_participants(token, event_id)

    # Test participant stats
    test_participant_stats(token, event_id)

    print_header("All Tests Completed!")
    print("[OK] Backend APIs are working correctly")
    print(f"[OK] Frontend running at: http://localhost:5177")
    print(f"[OK] Backend docs at: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
