import requests
import json

base_url = "http://localhost:8000"
admin_email = "admin@abhimatagolf.com"
admin_password = "admin123"

def create_test_event():
    print("Creating test event...")
    print("=" * 50)

    # Login
    login_data = {
        "email": admin_email,
        "password": admin_password
    }
    
    try:
        response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            token = token_data['access_token']
            print("Login successful")
        else:
            print(f"Login failed: {response.text}")
            return
    except Exception as e:
        print(f"Login error: {e}")
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Create event
    event_data = {
        "name": "Test Event",
        "description": "Test event for debugging",
        "event_date": "2025-10-20",
        "course_id": 1,
        "scoring_type": "stroke",
        "max_participants": 10
    }
    
    try:
        response = requests.post(f"{base_url}/events", json=event_data, headers=headers)
        print(f"Event Creation Status: {response.status_code}")
        
        if response.status_code == 201:
            event = response.json()
            event_id = event['id']
            print(f"Event created with ID: {event_id}")
            
            # Create participant
            participant_data = {
                "name": "Test Player",
                "email": "test@example.com",
                "phone": "1234567890",
                "declared_handicap": 10.0,
                "division": "Test Division",
                "event_id": event_id
            }
            
            response = requests.post(f"{base_url}/participants", json=participant_data, headers=headers)
            print(f"Participant Creation Status: {response.status_code}")
            
            if response.status_code == 201:
                participant = response.json()
                participant_id = participant['id']
                print(f"Participant created with ID: {participant_id}")
                
                # Create some test scores
                for hole_num in range(1, 4):  # Create scores for holes 1-3
                    score_data = {
                        "participant_id": participant_id,
                        "hole_number": hole_num,
                        "strokes": 4,
                        "points": 0
                    }
                    
                    response = requests.post(f"{base_url}/scorecards", json=score_data, headers=headers)
                    print(f"Hole {hole_num} Score Status: {response.status_code}")
                    if response.status_code != 201:
                        print(f"Hole {hole_num} Score Error: {response.text}")
                
                print(f"\nTest event created successfully!")
                print(f"Event ID: {event_id}")
                print(f"Participant ID: {participant_id}")
                print(f"Now test leaderboard with: /api/v1/leaderboards/event/{event_id}")
            else:
                print(f"Participant creation failed: {response.text}")
        else:
            print(f"Event creation failed: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_test_event()
