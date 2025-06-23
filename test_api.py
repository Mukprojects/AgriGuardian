import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load API key from environment
API_KEY = os.environ.get("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "anthropic/claude-3-sonnet-20240229"  # Amazon Bedrock model via OpenRouter

def get_api_key():
    """Get API key from environment or prompt user"""
    global API_KEY
    if API_KEY:
        return API_KEY
    
    # Prompt user for API key
    print("\n===== OpenRouter API Key Required =====")
    print("To use AgriGuardian, you need an OpenRouter API key with access to Amazon Bedrock models.")
    print("Get your key at: https://openrouter.ai/keys")
    api_key = input("Enter your OpenRouter API key: ").strip()
    
    if api_key:
        # Save to environment variable for current session
        API_KEY = api_key
        os.environ["OPENROUTER_API_KEY"] = api_key
        
        # Ask if user wants to save to .env file
        save_to_env = input("Save this API key to .env file for future use? (y/n): ").strip().lower()
        if save_to_env == 'y':
            try:
                with open('.env', 'w') as f:
                    f.write(f"OPENROUTER_API_KEY={api_key}\n")
                print("API key saved to .env file.")
            except Exception as e:
                print(f"Error saving API key to .env file: {e}")
    
    return API_KEY

def test_api():
    """Test the OpenRouter API with a simple query"""
    # Ensure we have an API key
    api_key = get_api_key()
    if not api_key:
        print("Error: No API key provided. Please provide your OpenRouter API key.")
        return
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://agriguardian-app.com",
        "X-Title": "AgriGuardian"
    }
    
    data = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": "Hello, are you working?"}
        ]
    }
    
    print("Testing OpenRouter API connection...")
    print(f"Using model: {MODEL}")
    
    try:
        response = requests.post(
            url=API_URL,
            headers=headers,
            json=data,
            timeout=30
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                message = result["choices"][0]["message"]["content"].strip()
                print("Success! API response:")
                print(message[:100] + "..." if len(message) > 100 else message)
            else:
                print("Error: Unexpected response format")
                print(result)
        else:
            print("Error response:")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_api() 