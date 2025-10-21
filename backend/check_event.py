import requests
import json

base_url = "http://localhost:8000"
admin_email = "admin@abhimatagolf.com"
admin_password = "admin123"

def check_event_scoring_type():
    print("Checking event scoring type...")
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
    
    # Get event details
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.get(f"{base_url}/api/v1/events", headers=headers)
        print(f"Event API Status: {response.status_code}")
        
        if response.status_code == 200:
            events = response.json()
            print(f"Total Events: {len(events)}")
            for i, event in enumerate(events):
                print(f"Event {i+1}: {event.get('name', 'N/A')} - Scoring: {event.get('scoring_type', 'N/A')} - ID: {event.get('id', 'N/A')}")
        else:
            print(f"Event API failed: {response.text}")
    except Exception as e:
        print(f"Event API error: {e}")

if __name__ == "__main__":
    check_event_scoring_type()
