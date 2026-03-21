#!/usr/bin/env python3
"""
Script to check available Claude models from Anthropic API.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

def check_models():
    """Check available Claude models."""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in environment")
        print("Please set it in your .env file")
        return
    
    print(f"Using API key: {api_key[:8]}...{api_key[-4:]}")
    print("\nFetching available models from Anthropic API...")
    
    # Try to list models (note: Anthropic may not have a models endpoint)
    # Let's try a simple completion to see what error we get
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    # Try different model names
    test_models = [
        # Claude 4 models (2026)
        "claude-sonnet-4",
        "claude-sonnet-4-5",
        "claude-opus-4",
        "claude-4-opus",
        "claude-4-sonnet",
        # Claude 3.5 models
        "claude-3-5-sonnet-20240620",
        "claude-3-5-sonnet-20241022",
        # Claude 3 models
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        # Older models
        "claude-2.1",
        "claude-2.0",
        "claude-instant-1.2",
    ]
    
    print("\nTesting model availability:")
    print("-" * 60)
    
    for model in test_models:
        data = {
            "model": model,
            "max_tokens": 10,
            "messages": [{"role": "user", "content": "Hi"}]
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            if response.status_code == 200:
                print(f"✓ {model:40} AVAILABLE")
            elif response.status_code == 404:
                error_data = response.json()
                if 'not_found_error' in str(error_data):
                    print(f"✗ {model:40} NOT FOUND")
                else:
                    print(f"? {model:40} ERROR: {response.status_code}")
            else:
                print(f"? {model:40} HTTP {response.status_code}")
        except Exception as e:
            print(f"✗ {model:40} ERROR: {str(e)[:30]}")
    
    print("-" * 60)
    print("\nRecommendation: Use the first model marked with ✓")

if __name__ == "__main__":
    check_models()
