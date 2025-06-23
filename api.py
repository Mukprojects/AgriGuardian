import json
import os
import random
import boto3
from datetime import datetime
import requests
from urllib.parse import parse_qs

# OpenRouter API configuration
API_KEY = os.environ.get("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "anthropic/claude-3-sonnet-20240229"  # Amazon Bedrock model via OpenRouter

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_NAME', 'AgriGuardianUserData'))

# Track request counter in memory (would reset on Lambda cold start)
request_counter = 0

def simulate_iot_data(farmer_id=None):
    """
    Simulate IoT sensor data or fetch real data if available.
    In production, this would query a real IoT database or API.
    """
    # In production: query real IoT data based on farmer_id
    # For now: simulate the data
    return {
        "temperature": round(random.uniform(20, 40), 1),  # Celsius
        "humidity": round(random.uniform(30, 90), 1),     # Percentage
        "soil_moisture": round(random.uniform(10, 60), 1),# Percentage
        "light_level": round(random.uniform(2000, 10000)), # Lux
        "rainfall_last_24h": round(random.uniform(0, 30), 1), # mm
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def construct_prompt(user_question, sensor_data, farmer_info=None):
    """Construct a detailed prompt combining the user's question with sensor data context"""
    
    # Add personalization if farmer info is available
    farmer_context = ""
    if farmer_info:
        farmer_context = f"""
        FARMER INFORMATION:
        - Location: {farmer_info.get('location', 'Unknown')}
        - Main crops: {farmer_info.get('crops', 'Various crops')}
        - Farm size: {farmer_info.get('farm_size', 'Unknown')} hectares
        """
    
    system_prompt = """You are AgriGuardian, an AI agricultural assistant for farmers. 
    You provide practical, actionable advice based on the farmer's question and available sensor data.
    Keep responses focused, informative and practical for farmers with limited connectivity.
    Provide step-by-step solutions when applicable.
    If you don't have enough information, ask clarifying questions.
    Always consider the provided sensor data in your response.
    """
    
    user_prompt = f"""
    FARMER QUESTION: {user_question}
    
    CURRENT FARM CONDITIONS:
    - Temperature: {sensor_data['temperature']}°C
    - Humidity: {sensor_data['humidity']}%
    - Soil Moisture: {sensor_data['soil_moisture']}%
    - Light Level: {sensor_data['light_level']} Lux
    - Rainfall (Last 24h): {sensor_data['rainfall_last_24h']}mm
    - Date/Time: {sensor_data['timestamp']}
    {farmer_context}
    
    Please provide the most accurate and practical advice based on this information.
    """
    
    return system_prompt, user_prompt

def ask_ai(user_question, sensor_data=None, farmer_info=None):
    """Send a prompt to the AI model via OpenRouter API"""
    global request_counter
    
    # Check if API key is available
    if not API_KEY:
        return "Error: OpenRouter API key not configured. Please set the OPENROUTER_API_KEY environment variable."
    
    if sensor_data is None:
        sensor_data = simulate_iot_data()
    
    system_prompt, user_prompt = construct_prompt(user_question, sensor_data, farmer_info)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
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
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        request_counter += 1
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"].strip()
        else:
            return "Error processing your request. Please try again later."
            
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            return "Our system is experiencing high demand. Please try again in a few hours."
        return f"Error processing your request. Please try again later."
    except Exception as e:
        return f"Error processing your request. Please try again later."

def get_farmer_info(phone_number):
    """Retrieve farmer information from DynamoDB based on phone number"""
    try:
        response = table.get_item(Key={'phone_number': phone_number})
        if 'Item' in response:
            return response['Item']
        return None
    except Exception:
        return None

def record_interaction(phone_number, message, response):
    """Record the farmer interaction in DynamoDB for future context"""
    try:
        timestamp = datetime.now().isoformat()
        table.update_item(
            Key={'phone_number': phone_number},
            UpdateExpression="SET interactions = list_append(if_not_exists(interactions, :empty_list), :interaction)",
            ExpressionAttributeValues={
                ':empty_list': [],
                ':interaction': [{
                    'timestamp': timestamp,
                    'message': message,
                    'response': response
                }]
            }
        )
    except Exception:
        # Log error but continue processing
        pass

def ask_handler(event, context):
    """Handler for API ask endpoint"""
    try:
        global request_counter
        
        # Check if request limit exceeded
        if request_counter >= 50:
            return {
                'statusCode': 429,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'success': False,
                    'message': 'Daily API limit exceeded (50/50 requests)'
                })
            }
            
        # Parse request body
        body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        
        user_id = body.get('user_id', 'anonymous')
        user_question = body.get('question', '')
        
        # Get or generate sensor data
        sensor_data = body.get('sensor_data', simulate_iot_data(user_id))
        
        # Get farmer info if available
        farmer_info = get_farmer_info(user_id) if user_id != 'anonymous' else None
        
        # Get AI response
        response = ask_ai(user_question, sensor_data, farmer_info)
        
        # Record interaction if user_id is available
        if user_id != 'anonymous':
            record_interaction(user_id, user_question, response)
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'success': True,
                'response': response,
                'request_count': request_counter,
                'sensor_data': sensor_data
            })
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'success': False,
                'message': str(e)
            })
        }

def sensor_data_handler(event, context):
    """Handler for IoT sensor data endpoint"""
    try:
        # Get query parameters if any
        params = event.get('queryStringParameters', {}) or {}
        user_id = params.get('user_id')
        
        # Generate sensor data
        sensor_data = simulate_iot_data(user_id)
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps(sensor_data)
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'success': False,
                'message': str(e)
            })
        } 