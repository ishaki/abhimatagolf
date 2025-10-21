#!/usr/bin/env python3
"""
Test script to verify leaderboard API functionality
"""
import requests
import json

def test_leaderboard_api():
    base_url = "http://localhost:8000"
    
    print("Testing Leaderboard API...")
    print("=" * 50)
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   [OK] Health check passed")
        else:
            print("   [ERROR] Health check failed")
    except Exception as e:
        print(f"   [ERROR] Health check error: {e}")
        return
    
    # Test 2: Login
    print("\n2. Testing login...")
    login_data = {
        'email': 'admin@abhimatagolf.com',
        'password': 'admin123'
    }
    
    try:
        response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data['access_token']
            print(f"   [OK] Login successful")
            print(f"   Token: {token[:20]}...")
        else:
            print(f"   [ERROR] Login failed: {response.text}")
            return
    except Exception as e:
        print(f"   [ERROR] Login error: {e}")
        return
    
    # Test 3: Leaderboard API
    print("\n3. Testing leaderboard API...")
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.get(f"{base_url}/api/v1/leaderboards/event/1", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            leaderboard_data = response.json()
            print("   [OK] Leaderboard API working!")
            print(f"   Event: {leaderboard_data.get('event_name', 'N/A')}")
            print(f"   Participants: {leaderboard_data.get('total_participants', 0)}")
            print(f"   Entries: {len(leaderboard_data.get('entries', []))}")
        else:
            print(f"   [ERROR] Leaderboard API failed: {response.text}")
    except Exception as e:
        print(f"   [ERROR] Leaderboard API error: {e}")
    
    # Test 4: Public leaderboard API
    print("\n4. Testing public leaderboard API...")
    try:
        response = requests.get(f"{base_url}/api/v1/leaderboards/public/event/1")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            leaderboard_data = response.json()
            print("   [OK] Public leaderboard API working!")
            print(f"   Event: {leaderboard_data.get('event_name', 'N/A')}")
            print(f"   Participants: {leaderboard_data.get('total_participants', 0)}")
        else:
            print(f"   [ERROR] Public leaderboard API failed: {response.text}")
    except Exception as e:
        print(f"   [ERROR] Public leaderboard API error: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_leaderboard_api()
