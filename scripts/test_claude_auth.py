#!/usr/bin/env python3
"""
Script to test Claude API authentication and get error details.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
import requests
import json

# Load environment variables
load_dotenv()

def test_auth():
    """Test Claude API authentication."""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in environment")
        return
    
    print(f"Testing API key: {api_key[:12]}...{api_key[-4:]}")
    print(f"API key length: {len(api_key)} characters")
    print()
    
    # Test with a simple request
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    # Try with the simplest possible model name
    data = {
        "model": "claude-3-opus-20240229",
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "Hi"}]
    }
    
    print("Sending test request to Anthropic API...")
    print(f"URL: {url}")
    print(f"Model: {data['model']}")
    print()
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print()
        print("Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            print("\n✓ SUCCESS! API key is valid and working.")
        elif response.status_code == 401:
            print("\n✗ AUTHENTICATION ERROR: Invalid API key")
        elif response.status_code == 404:
            print("\n✗ MODEL NOT FOUND: The model name may be incorrect")
            print("   This could also mean your API key doesn't have access to this model")
        else:
            print(f"\n? UNEXPECTED STATUS: {response.status_code}")
            
    except Exception as e:
        print(f"✗ ERROR: {e}")

if __name__ == "__main__":
    test_auth()

