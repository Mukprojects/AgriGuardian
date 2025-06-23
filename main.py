import os
import random
import json
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv()

# OpenRouter API configuration
API_KEY = os.getenv("OPENROUTER_API_KEY")
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

# Default examples for common crop questions
DEFAULT_EXAMPLES = {
    "tomato_yellowing": """
    Q: Why are my tomato leaves turning yellow?
    A: Your tomato leaves are likely turning yellow due to one of these common causes:
    
    1. NUTRIENT DEFICIENCY: The most common cause is nitrogen deficiency, showing as yellowing of older, lower leaves first.
       - Solution: Apply a balanced fertilizer with higher N value (like 10-5-5).
    
    2. OVERWATERING: With your soil moisture at 55%, this could be the issue. Wet soil prevents roots from accessing oxygen.
       - Solution: Let the top 1-2 inches of soil dry between waterings. Improve drainage with compost.
    
    3. DISEASE: Early blight causes yellow spots with concentric rings.
       - Solution: Remove affected leaves immediately. Apply copper-based fungicide in early morning.
    
    4. TEMPERATURE STRESS: Tomatoes struggle above 35°C or below 10°C.
       - Solution: Use shade cloth during peak heat or row covers in cool conditions.
    
    Monitor new growth after treatment - if yellowing continues after addressing these issues, soil testing is recommended.
    """,
    
    "water_frequency": """
    Q: How often should I water my crops?
    A: Based on your current conditions, here's my watering advice:
    
    1. SOIL MOISTURE READING: Your current reading of 42% is moderate - neither too dry nor saturated.
    
    2. WATERING FREQUENCY BY CROP TYPE:
       - Shallow-rooted crops (lettuce, herbs): Water when soil moisture drops to 35%
       - Medium-rooted crops (peppers, beans): Water at 30-32% moisture
       - Deep-rooted crops (tomatoes, corn): Wait until 25-28% moisture
    
    3. ADJUST FOR TEMPERATURE:
       - In your current temperature (34°C): Increase frequency by 20%
       - For every 5°C above normal, check moisture 1 day earlier
    
    4. RAINFALL IMPACT:
       - Recent rainfall (18mm) provides approximately 2-3 days of moisture
    
    BOTTOM LINE: For most vegetable crops, water deeply twice weekly at your current conditions. Use your finger to test moisture at 2-inch depth before watering.
    """,
    
    "pest_control": """
    Q: How can I control aphids on my crops?
    A: Based on your environmental conditions, here's my targeted aphid control plan:
    
    1. IMMEDIATE ACTION (INFESTATION):
       - Spray plants with strong water stream to dislodge aphids
       - Apply insecticidal soap solution (2 tbsp soap per gallon of water)
       - Focus spray on leaf undersides where aphids cluster
    
    2. NATURAL PREDATORS:
       - Release ladybugs in evening when temperatures are 21-26°C
       - Plant sweet alyssum, dill, and fennel to attract beneficial insects
    
    3. PREVENTATIVE MEASURES:
       - Apply reflective mulch around plants
       - Spray diluted neem oil (1 tbsp per gallon) every 7 days
       - Remove severely infested plant parts immediately
    
    4. ENVIRONMENTAL ADJUSTMENTS:
       - Reduce nitrogen fertilization - high nitrogen promotes tender growth that attracts aphids
       - Your current humidity (65%) is ideal for predatory insects - maintain this level in greenhouse settings
    
    Monitor every 2-3 days after treatment. If aphid population isn't declining within a week, consider rotating to a different organic solution like pyrethrins.
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

def get_user_farm_conditions():
    """Get farm conditions from user input or simulation"""
    print("\n===== FARM CONDITIONS SETUP =====")
    print("Would you like to enter your own farm conditions or use simulated values?")
    choice = input("Enter 'custom' or 'simulate' (default: simulate): ").strip().lower()

    if choice == 'custom':
        print("\nPlease enter your farm conditions:")
        try:
            temperature = float(input("Temperature (°C, 10-50): "))
            humidity = float(input("Humidity (%, 0-100): "))
            soil_moisture = float(input("Soil Moisture (%, 0-100): "))
            light_level = float(input("Light Level (Lux, 0-15000): "))
            rainfall = float(input("Rainfall last 24h (mm, 0-100): "))
            
            return {
                "temperature": round(max(10, min(50, temperature)), 1),
                "humidity": round(max(0, min(100, humidity)), 1),
                "soil_moisture": round(max(0, min(100, soil_moisture)), 1),
                "light_level": round(max(0, min(15000, light_level))),
                "rainfall_last_24h": round(max(0, min(100, rainfall)), 1),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except ValueError:
            print("Invalid input detected. Using simulated values instead.")
            return simulate_iot_data()
    else:
        return simulate_iot_data()

def get_crop_information():
    """Get information about the crops being grown"""
    print("\n===== CROP INFORMATION =====")
    print("What are your main crops? (e.g., tomatoes, wheat, corn, potatoes)")
    crops = input("Enter your crops (comma separated): ").strip()
    
    print("\nWhat growth stage are they in?")
    print("1) Planting/Seeding")
    print("2) Sprouting/Emergence")
    print("3) Vegetative Growth")
    print("4) Flowering")
    print("5) Fruiting/Grain Development")
    print("6) Harvesting")
    stage = input("Enter the number or describe the stage: ").strip()
    
    print("\nAny specific pest or disease issues?")
    issues = input("Enter any issues (or 'none'): ").strip()
    
    return {
        "crops": crops if crops else "various crops",
        "stage": stage if stage else "unknown",
        "issues": issues if issues and issues.lower() != 'none' else None
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
    - Main crops: {crop_info['crops']}
    - Growth stage: {crop_info['stage']}"""
        
        if crop_info['issues']:
            crop_context += f"\n    - Reported issues: {crop_info['issues']}"
    
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

def ask_ai(user_question, sensor_data=None, crop_info=None, history=None, timeout=60):
    """Send a prompt to the AI model via OpenRouter API"""
    
    # Ensure we have an API key
    api_key = get_api_key()
    if not api_key:
        print("Error: No API key provided. Please restart and enter your OpenRouter API key.")
        sys.exit(1)
    
    if sensor_data is None:
        sensor_data = simulate_iot_data()
    
    system_prompt, user_prompt = construct_prompt(user_question, sensor_data, crop_info, history)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }
    
    try:
        # Show a progress indication
        print("Requesting advice", end="")
        for _ in range(5):
            print(".", end="", flush=True)
            time.sleep(0.5)
        print()
        
        # Send the request with timeout
        response = requests.post(API_URL, headers=headers, json=data, timeout=timeout)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"].strip()
        else:
            return "Error: Unexpected response format from the AI service."
            
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "Error: Invalid API key. Please check your OpenRouter API key and try again."
        elif e.response.status_code == 429:
            return "Error: API rate limit exceeded. Please try again later."
        else:
            return f"Error: HTTP error occurred: {str(e)}"
    except requests.exceptions.ConnectionError:
        return "Error: Failed to connect to the API service. Please check your internet connection."
    except requests.exceptions.Timeout:
        return "Error: Request timed out. The AI service is taking too long to respond."
    except Exception as e:
        return f"Error: {str(e)}"

def display_sensor_data(sensor_data):
    """Format and display sensor data nicely"""
    print("\n===== CURRENT FARM CONDITIONS =====")
    print(f"🌡️  Temperature: {sensor_data['temperature']}°C")
    print(f"💧 Humidity: {sensor_data['humidity']}%")
    print(f"🌱 Soil Moisture: {sensor_data['soil_moisture']}%")
    print(f"☀️  Light Level: {sensor_data['light_level']} Lux")
    print(f"🌧️  Rainfall (24h): {sensor_data['rainfall_last_24h']}mm")
    print(f"🕒 Timestamp: {sensor_data['timestamp']}")
    print("==================================\n")

def main():
    """Main application loop"""
    print("="*60)
    print("🌱 Welcome to AgriGuardian - Your AI Farming Assistant 🌱")
    print("="*60)
    print("\nAgriGuardian helps farmers get AI-powered advice on crops and conditions.")
    
    # Get initial farm conditions from user or simulation
    sensor_data = get_user_farm_conditions()
    
    # Get crop information
    crop_info = get_crop_information()
    
    # Display the initial farm conditions
    display_sensor_data(sensor_data)
    
    print("\nAsk any farming or agriculture question, or type 'exit' to quit.")
    print("Type 'update conditions' to change farm conditions or 'update crops' to change crop information.")
    
    request_count = 0
    chat_history = []
    
    while True:
        user_input = input("\n👨‍🌾 Farmer's Question: ")
        
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Thank you for using AgriGuardian. Goodbye!")
            break
        
        if user_input.lower() == "update conditions":
            sensor_data = get_user_farm_conditions()
            display_sensor_data(sensor_data)
            continue
            
        if user_input.lower() == "update crops":
            crop_info = get_crop_information()
            continue
        
        # Add user question to chat history
        chat_history.append({"role": "user", "content": user_input})
        
        # Keep history limited to last 4 exchanges (2 questions, 2 answers)
        if len(chat_history) > 4:
            chat_history = chat_history[-4:]
        
        print("\n⏳ Consulting agricultural knowledge... Please wait...")
        
        try:
            # Send question to AI model
            response = ask_ai(user_input, sensor_data, crop_info, chat_history)
            
            # Add assistant response to chat history
            chat_history.append({"role": "assistant", "content": response})
            
            print("\n🌱 AgriGuardian Advice 🌱")
            print(response)
            
            request_count += 1
            print(f"\n(API Request Count: {request_count}/50 daily limit)")
        except KeyboardInterrupt:
            print("\nRequest cancelled by user.")
            continue
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("Please try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting AgriGuardian. Thank you for using our service!")
        sys.exit(0) 