import os
import requests
import random
import json
import traceback
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session

# Load environment variables from .env file
load_dotenv()

# OpenRouter API configuration
API_KEY = os.environ.get("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "anthropic/claude-3-sonnet-20240229"  # Amazon Bedrock model via OpenRouter

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))  # For session management
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
request_count = 0

# Add welcome message
WELCOME_MESSAGE = "Welcome to AgriGuardian! I'm your AI farming assistant. I provide quick 5-10 second responses to help with your farming questions. How can I help with your farm today?"

# Check if API key is set
if not API_KEY:
    print("WARNING: No OpenRouter API key found. You will be prompted to enter one when starting the server.")

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

def simulate_iot_data():
    """Simulate IoT sensor data that would come from farm sensors"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "temperature": round(random.uniform(20, 40), 1),  # Celsius
        "humidity": round(random.uniform(30, 90), 1),     # Percentage
        "soil_moisture": round(random.uniform(10, 60), 1),# Percentage
        "light_level": round(random.uniform(2000, 10000)), # Lux
        "rainfall_last_24h": round(random.uniform(0, 30), 1), # mm
        "timestamp": current_time
    }

def construct_prompt(user_question, sensor_data, crop_info=None, history=None):
    """Construct a concise prompt combining the user's question with sensor data context"""
    
    system_prompt = """You are AgriGuardian, a fast-response agricultural assistant. 
    Provide VERY BRIEF advice based on the farmer's question and sensor data.
    Keep responses under 150 words - brevity is critical for fast response times.
    Focus on:
    1. One-sentence direct answer to the question
    2. 1-2 specific action steps based on environmental data
    3. Only the most essential information

    Use bullet points for actions. Use bold only for the single most important advice.
    Be extremely concise and direct - avoid unnecessary explanations.
    Do not introduce your answer or provide context the user already knows.
    """
    
    # Add crop information if available
    crop_context = ""
    if crop_info:
        crop_context = f"""
    CROP INFORMATION:
    - Main crops: {crop_info.get('crops', 'various crops')}
    - Growth stage: {crop_info.get('stage', 'unknown')}"""
        
        if crop_info.get('issues'):
            crop_context += f"\n    - Reported issues: {crop_info.get('issues')}"
    
    # Add minimal chat history if available
    history_context = ""
    if history and len(history) > 0:
        # Only include the last exchange for context
        last_entries = history[-2:] if len(history) >= 2 else history
        history_context = "\nLAST EXCHANGE:\n"
        for entry in last_entries:
            role = "FARMER" if entry["role"] == "user" else "ASSISTANT"
            # Only include first 50 chars of previous messages
            content = entry["content"][:100] + ("..." if len(entry["content"]) > 100 else "")
            history_context += f"{role}: {content}\n"
    
    # Add seasonal context
    current_month = datetime.now().strftime("%B")
    
    # Remove examples to reduce token count
    
    user_prompt = f"""
    QUESTION: {user_question}
    
    CONDITIONS:
    - Temperature: {sensor_data['temperature']}°C
    - Humidity: {sensor_data['humidity']}%
    - Soil Moisture: {sensor_data['soil_moisture']}%
    - Light Level: {sensor_data['light_level']} Lux
    - Rainfall (Last 24h): {sensor_data['rainfall_last_24h']}mm
    - Month: {current_month}
    {crop_context}
    {history_context}
    
    Provide brief, specific advice that directly addresses the question. Include 2-3 actionable steps.
    """
    
    return system_prompt, user_prompt

def ask_ai(user_question, sensor_data=None, crop_info=None, history=None):
    """Send a prompt to the AI model via OpenRouter API"""
    global request_count
    
    # Ensure we have an API key
    api_key = get_api_key()
    if not api_key:
        return "Error: No API key provided. Please restart the server and enter your OpenRouter API key."
    
    if sensor_data is None:
        sensor_data = simulate_iot_data()
    
    system_prompt, user_prompt = construct_prompt(user_question, sensor_data, crop_info, history)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://agriguardian-app.com", 
        "X-Title": "AgriGuardian"
    }
    
    # Follow exactly the OpenRouter example format
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    data = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 350,  # Limit token count for faster responses
        "temperature": 0.7,  # Slightly reduced temperature for more focused responses
        "top_p": 0.1,       # Lower top_p for more deterministic responses (faster)
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    }
    
    # Debug
    print(f"Sending to OpenRouter API with model: {MODEL}")
    
    try:
        # Log what we're sending to API for debugging
        print(f"Sending request to API with question: {user_question}")
        
        response = requests.post(
            url=API_URL,
            headers=headers,
            json=data,
            timeout=120  # Increased timeout to 2 minutes to ensure response completion
        )
        
        # Debug response
        print(f"API Response status: {response.status_code}")
        print(f"API Response headers: {response.headers}")
        
        # Log the full response for debugging
        try:
            print(f"API Response text: {response.text}")
        except:
            print("Could not print response text")
        
        # Check if response is valid JSON
        try:
            result = response.json()
            print(f"API Response JSON parsed successfully: {json.dumps(result, indent=2)[:500]}...")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {str(e)}")
            return "Error: The API returned an invalid response format. Please try again."
        
        response.raise_for_status()  # Raise exception for HTTP errors
        
        # Ensure we have valid JSON response
        result = response.json()
        request_count += 1
        
        # Extract message from response
        if "choices" in result and len(result["choices"]) > 0:
            message = result["choices"][0]["message"]
            content = ""
            
            # Check for content field
            if "content" in message and message["content"]:
                content = message["content"].strip()
            
            # Check for reasoning field (fallback if content is empty)
            if not content and "reasoning" in message and message["reasoning"]:
                print("Using reasoning field as content")
                content = message["reasoning"].strip()
                
                # Extract the most useful part of the reasoning
                if "Actionable steps:" in content:
                    parts = content.split("Actionable steps:")
                    actionable_part = parts[1].strip()
                    content = f"Based on the analysis of your farm conditions, here's what to do:\n\nActionable steps:{actionable_part}"
                elif "Analysis:" in content:
                    parts = content.split("Analysis:")
                    if len(parts) > 1:
                        analysis = parts[1].strip()
                        # Look for solution sections
                        solution_markers = ["Solution:", "Actions:", "Recommendations:", "Steps:", "What to do:"]
                        for marker in solution_markers:
                            if marker in analysis:
                                solution_parts = analysis.split(marker)
                                if len(solution_parts) > 1:
                                    content = f"Analysis summary: {solution_parts[0][:200]}...\n\n{marker}{solution_parts[1]}"
                                    break
                        else:
                            # If no solution marker found, use the first part of the analysis
                            content = f"Based on analysis of your farm conditions:\n\n{analysis[:800]}"
            
            if content:
                # Clean up the content to focus on actionable advice
                if len(content) > 1500:
                    # Try to extract the most important parts
                    important_sections = []
                    
                    # Look for specific sections
                    sections = ["Actionable steps:", "Recommendations:", "Solution:", "What to do:"]
                    for section in sections:
                        if section in content:
                            parts = content.split(section)
                            if len(parts) > 1:
                                important_sections.append(f"{section}{parts[1].split(sections[0])[0] if len(sections) > 0 else parts[1]}")
                    
                    # If we found important sections, use them
                    if important_sections:
                        content = "\n\n".join(important_sections)
                    else:
                        # Otherwise, trim the content
                        content = content[:1500] + "..."
                
                return content
            else:
                print("No content or reasoning in message")
                return "Sorry, I couldn't generate a helpful response. Based on common issues with tomatoes, check your watering schedule, ensure adequate sunlight, and inspect for pests or disease signs."
        else:
            print(f"Unexpected API response format: {result}")
            error_message = "Sorry, I encountered an issue understanding your question. Please try rephrasing it."
            if "error" in result:
                error_detail = result.get("error", {})
                if isinstance(error_detail, dict):
                    error_message = f"API Error: {error_detail.get('message', 'Unknown error')}"
                else:
                    error_message = f"API Error: {error_detail}"
            return error_message
            
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {str(e)}")
        if hasattr(e, 'response'):
            print(f"Response content: {e.response.text}")
        if hasattr(e, 'response') and e.response.status_code == 429:
            return "Daily quota exceeded. Please try again tomorrow."
        return f"API Error: {str(e)}"
    except requests.exceptions.Timeout:
        print("Request timed out")
        return "The AI service is taking longer than expected to respond. Please try again with a simpler question."
    except requests.exceptions.ConnectionError:
        print("Connection error")
        return "Connection error: Unable to reach the AI service. Please check your internet connection and try again."
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        traceback.print_exc()
        return f"Error: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html', welcome_message=WELCOME_MESSAGE)

@app.route('/api/setup', methods=['POST'])
def setup():
    data = request.json
    crop_info = {
        'crops': data.get('crops', 'various crops'),
        'stage': data.get('stage', 'unknown'),
        'issues': data.get('issues')
    }
    
    # Store in session
    session['crop_info'] = crop_info
    session['chat_history'] = []
    
    return jsonify({
        'success': True,
        'message': 'Crop information stored'
    })

@app.route('/api/ask', methods=['POST'])
def ask():
    """API endpoint to ask questions to the AI"""
    try:
        # Get request data
        data = request.json
        user_question = data.get('question', '')
        crop_info = data.get('crop_info', None)
        
        # Check if question is empty
        if not user_question:
            return jsonify({
                'success': False,
                'message': 'No question provided'
            }), 400
        
        # Get chat history from session
        chat_history = session.get('chat_history', [])
        
        # Get or generate sensor data
        sensor_data = data.get('sensor_data', simulate_iot_data())
        
        # Get response from AI
        response = ask_ai(user_question, sensor_data, crop_info, chat_history)
        
        # Add response to chat history
        chat_history.append({"role": "user", "content": user_question})
        chat_history.append({"role": "assistant", "content": response})
        
        # Keep only the last 10 messages to avoid context getting too large
        if len(chat_history) > 10:
            chat_history = chat_history[-10:]
        
        # Save chat history to session
        session['chat_history'] = chat_history
        
        return jsonify({
            'success': True,
            'response': response,
            'request_count': request_count,
            'sensor_data': sensor_data
        })
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/sensor-data', methods=['GET'])
def get_sensor_data():
    sensor_data = simulate_iot_data()
    return jsonify(sensor_data)

@app.route('/api/chat-history', methods=['GET'])
def get_chat_history():
    """Get the current chat history and crop info for persistence"""
    try:
        chat_history = session.get('chat_history', [])
        crop_info = session.get('crop_info', {})
        
        return jsonify({
            'success': True,
            'chat_history': chat_history,
            'crop_info': crop_info
        })
    except Exception as e:
        print(f"Error in /api/chat-history: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Unable to retrieve chat history',
            'error': str(e)
        }), 500

@app.route('/api/reset', methods=['POST'])
def reset_session():
    try:
        session.clear()
    except:
        pass
    return jsonify({
        'success': True,
        'message': 'Session reset'
    })

if __name__ == '__main__':
    # Print API key for debugging (first few chars)
    safe_api_key = API_KEY[:8] + "..." if API_KEY else "Not set"
    print(f"Starting with API key: {safe_api_key}")
    print(f"API URL: {API_URL}")
    print(f"Model: {MODEL}")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port) 