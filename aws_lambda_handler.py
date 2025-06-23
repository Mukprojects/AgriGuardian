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
MODEL = "deepseek/deepseek-r1-0528:free"

# Initialize AWS clients
sns = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_NAME', 'AgriGuardianUserData'))

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
    Keep responses under 160 characters when possible for SMS compatibility.
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

def ask_deepseek(user_question, sensor_data, farmer_info=None):
    """Send a prompt to the DeepSeek model via OpenRouter API"""
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

def lambda_handler(event, context):
    """
    AWS Lambda handler for processing incoming SMS messages via SNS
    or API Gateway for testing/development
    """
    try:
        # Determine if this is coming from SNS or API Gateway
        if 'Records' in event and event['Records'][0].get('EventSource') == 'aws:sns':
            # This is an SNS event
            sns_message = json.loads(event['Records'][0]['Sns']['Message'])
            phone_number = sns_message.get('originationNumber')
            message_body = sns_message.get('messageBody')
        else:
            # Assume API Gateway/direct invocation for testing
            body = event.get('body', '{}')
            if isinstance(body, str):
                body = parse_qs(body) if '=' in body else json.loads(body)
            
            phone_number = body.get('From', ['test_phone'])[0] if isinstance(body.get('From'), list) else body.get('From', 'test_phone')
            message_body = body.get('Body', ['Hello'])[0] if isinstance(body.get('Body'), list) else body.get('Body', 'Hello')
        
        # Get farmer information if available
        farmer_info = get_farmer_info(phone_number)
        
        # Get or simulate IoT data
        sensor_data = simulate_iot_data(phone_number)
        
        # Process the message with DeepSeek
        ai_response = ask_deepseek(message_body, sensor_data, farmer_info)
        
        # Record this interaction
        record_interaction(phone_number, message_body, ai_response)
        
        # Send SMS response
        if phone_number != 'test_phone':
            sns.publish(
                PhoneNumber=phone_number,
                Message=ai_response,
                MessageAttributes={
                    'AWS.SNS.SMS.SenderID': {
                        'DataType': 'String',
                        'StringValue': 'AgrGuard'
                    }
                }
            )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Success',
                'response': ai_response
            })
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'Error: {str(e)}'
            })
        } 