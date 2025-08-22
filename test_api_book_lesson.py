#!/usr/bin/env python3
"""
Test script for the API book lesson endpoint.
This script demonstrates how to use the API endpoint with the provided curl command format.
"""

import requests
import json

def test_api_book_lesson():
    """Test the API book lesson endpoint."""
    
    # Base URL - adjust as needed
    base_url = "http://localhost:8000"
    
    # Test data matching the curl command format
    test_data = {
        'tutor': '1',
        'date': '2024-12-20',
        'start_time': '10:00',
        'end_time': '11:00',
        'location': 'Test',
        'student_class': 'class1'
    }
    
    # Headers matching the curl command
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    # Test the API endpoint
    api_url = f"{base_url}/api/book-lesson/"
    
    try:
        response = requests.post(api_url, data=test_data, headers=headers)
        print(f"API Response Status: {response.status_code}")
        
        if response.status_code == 403:
            print("❌ Authentication required. Please log in as a student first.")
            print("   The API endpoint requires an authenticated student user.")
        elif response.status_code == 200:
            try:
                response_json = response.json()
                print(f"✅ API Response: {json.dumps(response_json, indent=2)}")
            except json.JSONDecodeError:
                print("❌ Invalid JSON response:")
                print(response.text)
        else:
            try:
                response_json = response.json()
                print(f"❌ API Error: {json.dumps(response_json, indent=2)}")
            except json.JSONDecodeError:
                print(f"❌ HTTP {response.status_code} - Invalid JSON response:")
                print(response.text)
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
        print("   Make sure Django server is running on http://localhost:8000")
        return None
    
    return response

def test_curl_equivalent():
    """Show the equivalent curl command for testing."""
    print("\n" + "="*50)
    print("EQUIVALENT CURL COMMAND:")
    print("="*50)
    print('curl -X POST http://localhost:8000/api/book-lesson/ \\')
    print('  -d "tutor=1&date=2024-12-20&start_time=10:00&end_time=11:00&location=Test&student_class=class1" \\')
    print('  -H "Content-Type: application/x-www-form-urlencoded" \\')
    print('  -b "sessionid=YOUR_SESSION_ID" -v')
    print("="*50)
    print("\nNote: Replace YOUR_SESSION_ID with actual session cookie after login")
    print("\nTo get session cookie:")
    print("1. Log in to the web application as a student")
    print("2. Open browser developer tools (F12)")
    print("3. Go to Application/Storage > Cookies")
    print("4. Copy the value of 'sessionid' cookie")

if __name__ == "__main__":
    print("Testing API book lesson endpoint...")
    print("⚠️  Make sure Django server is running: python manage.py runserver")
    print("⚠️  You need to be logged in as a student for this to work")
    print()
    test_api_book_lesson()
    test_curl_equivalent()
