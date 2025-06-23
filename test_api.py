import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenRouter API configuration
API_KEY = os.getenv("OPENROUTER_API_KEY", "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")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-r1-0528:free"

def test_api_direct():
    """Test calling the OpenRouter API directly"""
    
    # Define example query
    system_message = "You are AgriGuardian, an AI agricultural assistant for farmers."
    user_message = """
    FARMER QUESTION: Why are my tomato leaves turning yellow?
    
    CURRENT FARM CONDITIONS:
    - Temperature: 32.5°C
    - Humidity: 65.0%
    - Soil Moisture: 15.3%
    - Light Level: 8500 Lux
    - Rainfall (Last 24h): 0mm
    
    Please provide the most accurate and practical advice based on this information.
    """
    
    # Set up API request
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
    }
    
    # Make API request
    print("Sending request to OpenRouter API...")
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        
        # Parse and print response
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            answer = result["choices"][0]["message"]["content"].strip()
            print("\n=== AI RESPONSE ===")
            print(answer)
            print("\n=================")
        else:
            print("Error: Unexpected API response format")
            print(result)
            
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(e.response.text)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    print("🌱 AgriGuardian - API Test")
    print("This script tests direct API communication with OpenRouter")
    print("Note: This will count as 1 of your 50 daily requests\n")
    
    proceed = input("Do you want to proceed with the test? (y/n): ")
    if proceed.lower() == 'y':
        test_api_direct()
    else:
        print("Test cancelled") 