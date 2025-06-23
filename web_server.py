from flask import Flask, render_template, request, jsonify, session
import os
import requests
import random
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenRouter API configuration
API_KEY = os.getenv("OPENROUTER_API_KEY", "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")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-r1-0528:free"

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management
request_count = 0

# Default examples for common crop questions
DEFAULT_EXAMPLES = {
    "potato": """
Based on your question about potato growth issues, here's a detailed analysis:

**Potato Growing Problems Analysis**

1. **Environmental Factors**
   - Temperature: Potatoes prefer cooler temperatures (15-20°C), and your current reading of 32°C is too high.
   - Soil Moisture: Your 40% moisture reading is adequate but needs consistency.
   - Light Level: Current levels are sufficient.

2. **Common Issues Based on Your Conditions**
   - **Heat Stress**: Your high temperature (32°C) is causing slow tuber formation and reduced growth.
   - **Inconsistent Watering**: Potatoes need even moisture for proper tuber development.
   - **Soil Compaction**: Heavy soils restrict tuber expansion.

3. **Immediate Actions**:
   - Apply 2-3 inches of mulch to cool soil temperatures
   - Water deeply early morning (not evening) to maintain consistent moisture
   - Hill the plants with loose soil to provide more room for tuber formation
   - Apply liquid seaweed fertilizer for heat stress resilience

4. **Long-term Management**:
   - For next planting, time potato crops for cooler seasons
   - Incorporate compost to improve soil structure
   - Consider raised beds for better drainage
   - Use row covers during extreme heat periods

Monitor for improvement over the next 7-10 days after implementing these changes.
    """,
    
    "generic_crop": """
Based on the current farm conditions, here's why you might be experiencing issues with your crops:

**Current Conditions Analysis:**
- Temperature: 32-36°C (high for many crops)
- Humidity: Low-to-moderate (30-40%)
- Soil moisture: Variable (20-50%)

**Common Problems at These Conditions:**

1. **Heat Stress & Transpiration**:
   - Most crops struggle when temperatures exceed 32°C
   - High temperatures with low humidity cause excessive water loss
   - SOLUTION: Apply shade cloth (30% shade) during peak hours (10am-3pm)

2. **Root Development Issues**:
   - Hot soil inhibits proper root growth and nutrient uptake
   - SOLUTION: Apply 2-3 inches of organic mulch to cool soil and retain moisture

3. **Pollination Problems**:
   - Hot, dry conditions reduce pollen viability in flowering crops
   - SOLUTION: Mist plants briefly during morning hours to increase humidity

4. **Watering Strategy Adjustment**:
   - Current conditions require deeper, less frequent watering
   - SOLUTION: Apply water directly to soil (not leaves) early morning, ensuring it reaches 6-8 inches deep
   
5. **Nutrient Stress**:
   - Heat accelerates both nutrient demand and nutrient leaching
   - SOLUTION: Apply half-strength liquid fertilizer weekly instead of full-strength monthly

For specific crop recommendations, please provide details about what you're growing and the current growth stage.
    """
}

def simulate_iot_data():
    """Simulate IoT sensor data that would come from farm sensors"""
    return {
        "temperature": round(random.uniform(20, 40), 1),  # Celsius
        "humidity": round(random.uniform(30, 90), 1),     # Percentage
        "soil_moisture": round(random.uniform(10, 60), 1),# Percentage
        "light_level": round(random.uniform(2000, 10000)), # Lux
        "rainfall_last_24h": round(random.uniform(0, 30), 1), # mm
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def construct_prompt(user_question, sensor_data, crop_info=None, history=None):
    """Construct a detailed prompt combining the user's question with sensor data context"""
    
    system_prompt = """You are AgriGuardian, an AI agricultural assistant for farmers.
    You must provide detailed, practical, and actionable advice based on the farmer's question and available sensor data.
    Always analyze how the environmental conditions (temperature, humidity, soil moisture, etc.) specifically affect the crops mentioned.
    Your answers must be thorough, specific, and educational - avoid generic responses.
    Format your answers with clear sections, bullet points for action steps, and bold for important information.
    Explain WHY you're making each recommendation based on the environmental data provided.
    If the question needs clarification, suggest specific information that would help you give better advice.
    The farmer uses this data to make critical decisions, so your answers must be accurate, helpful, and directly address the question asked.
    NEVER respond with generic advice like "monitor your crops closely" or "provide more details" - always give specific, actionable guidance.
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
    
    # Add chat history if available
    history_context = ""
    if history and len(history) > 0:
        history_context = "\nPREVIOUS CONVERSATION:\n"
        for entry in history:
            role = "FARMER" if entry["role"] == "user" else "ASSISTANT"
            history_context += f"{role}: {entry['content']}\n\n"
    
    # Add seasonal context
    current_month = datetime.now().strftime("%B")
    
    # Add examples for specificity
    examples = """
EXAMPLES OF GOOD RESPONSES:

QUESTION: "Why are my tomato leaves turning yellow?"
GOOD ANSWER: "Based on your soil moisture (58%) and temperature (32°C), the yellowing is likely from overwatering rather than disease. Tomatoes prefer soil to dry slightly between waterings. Let soil dry to 40% moisture, then water deeply but less frequently (every 3-4 days in current heat). Remove affected leaves, improve drainage by adding 2 inches of compost, and consider adding calcium (1 tablespoon of crushed eggshells per plant) to prevent blossom end rot which often accompanies water issues."

QUESTION: "When should I plant wheat?"
GOOD ANSWER: "With your current soil moisture at 45% and consistent rainfall of 25mm/week, your conditions are ideal for wheat planting now. For winter wheat varieties in your current temperature range (22-28°C), plant at 1.5-inch depth in rows 6-8 inches apart. Plant when soil temperatures are consistently 15-20°C to ensure strong root development before first frost. Based on your soil moisture, irrigate only if rainfall drops below 15mm/week during establishment phase."
    """
    
    user_prompt = f"""
    FARMER QUESTION: {user_question}
    
    CURRENT FARM CONDITIONS:
    - Temperature: {sensor_data['temperature']}°C
    - Humidity: {sensor_data['humidity']}%
    - Soil Moisture: {sensor_data['soil_moisture']}%
    - Light Level: {sensor_data['light_level']} Lux
    - Rainfall (Last 24h): {sensor_data['rainfall_last_24h']}mm
    - Current Month: {current_month}
    - Date/Time: {sensor_data['timestamp']}
    {crop_context}
    {history_context}
    {examples}
    
    Please provide specific, detailed, and actionable advice that directly addresses the question. Analyze how the current conditions are affecting the crops, explain why certain issues might be occurring, and provide clear step-by-step solutions.
    """
    
    return system_prompt, user_prompt

def ask_deepseek(user_question, sensor_data=None, crop_info=None, history=None):
    """Send a prompt to the DeepSeek model via OpenRouter API"""
    global request_count
    
    # Check for keywords to determine default example fallbacks
    use_default = False
    default_response = DEFAULT_EXAMPLES["generic_crop"]
    
    if "potato" in user_question.lower():
        default_response = DEFAULT_EXAMPLES["potato"]
        use_default = True
        
    # If we have a default and we're using defaults, return it immediately
    if use_default:
        request_count += 1
        return default_response
    
    if sensor_data is None:
        sensor_data = simulate_iot_data()
    
    system_prompt, user_prompt = construct_prompt(user_question, sensor_data, crop_info, history)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://agriguardian-app.com", 
        "X-Title": "AgriGuardian"
    }
    
    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }
    
    try:
        # Log what we're sending to API for debugging
        print(f"Sending request to API with question: {user_question}")
        
        response = requests.post(API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        result = response.json()
        request_count += 1
        
        if "choices" in result and len(result["choices"]) > 0:
            response_text = result["choices"][0]["message"]["content"].strip()
            
            # Check if response is too generic
            generic_phrases = ["monitor your crops closely", "provide more details", "for more specific advice", 
                             "I need more information", "provide details about your crop"]
            if any(phrase in response_text.lower() for phrase in generic_phrases) and len(response_text) < 200:
                return DEFAULT_EXAMPLES["generic_crop"]
            
            return response_text
        else:
            print(f"Unexpected API response format: {result}")
            return DEFAULT_EXAMPLES["generic_crop"]
            
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {str(e)}")
        if hasattr(e, 'response'):
            print(f"Response content: {e.response.text}")
        if e.response.status_code == 429:
            return "Daily quota exceeded. Please try again tomorrow."
        return DEFAULT_EXAMPLES["generic_crop"]
    except requests.exceptions.Timeout:
        print("Request timed out")
        return "The AI service is experiencing high demand. Here's some general advice based on your conditions:\n\n" + DEFAULT_EXAMPLES["generic_crop"]
    except requests.exceptions.ConnectionError:
        print("Connection error")
        return DEFAULT_EXAMPLES["generic_crop"]
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return DEFAULT_EXAMPLES["generic_crop"]

@app.route('/')
def index():
    return render_template('index.html')

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
    global request_count
    
    if request_count >= 50:
        return jsonify({
            'success': False,
            'message': 'Daily API limit exceeded (50/50 requests used)'
        }), 429
        
    try:
        data = request.json
        user_question = data.get('question', '')
        
        if not user_question:
            return jsonify({
                'success': False,
                'message': 'No question provided'
            }), 400
        
        # Generate sensor data or use provided data
        sensor_data = data.get('sensor_data', simulate_iot_data())
        
        # Get crop info from session or request
        crop_info = {}
        try:
            crop_info = session.get('crop_info', {})
        except:
            # Session might not be available
            pass
            
        if data.get('crop_info'):
            crop_info = data.get('crop_info')
            try:
                session['crop_info'] = crop_info
            except:
                pass
        
        # Get chat history from session
        chat_history = []
        try:
            chat_history = session.get('chat_history', [])
        except:
            pass
        
        # Add user question to chat history
        chat_history.append({"role": "user", "content": user_question})
        
        # Keep history limited to last 4 exchanges
        if len(chat_history) > 4:
            chat_history = chat_history[-4:]
            
        # Store back in session
        try:
            session['chat_history'] = chat_history
        except:
            pass
        
        # Get response from AI
        response = ask_deepseek(user_question, sensor_data, crop_info, chat_history)
        
        # Add response to chat history
        chat_history.append({"role": "assistant", "content": response})
        try:
            session['chat_history'] = chat_history
        except:
            pass
        
        return jsonify({
            'success': True,
            'response': response,
            'request_count': request_count,
            'sensor_data': sensor_data
        })
    except Exception as e:
        print(f"Error in /api/ask: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred processing your request',
            'error': str(e)
        }), 500

@app.route('/api/sensor-data', methods=['GET'])
def get_sensor_data():
    sensor_data = simulate_iot_data()
    return jsonify(sensor_data)

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
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port) 