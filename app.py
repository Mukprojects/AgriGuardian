import streamlit as st
import os
import random
import json
from datetime import datetime
from dotenv import load_dotenv
import requests
import time
import pandas as pd

# Load environment variables from .env file
load_dotenv()

# OpenRouter API configuration
API_KEY = os.getenv("OPENROUTER_API_KEY", "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")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-r1-0528:free"

# Initialize session state variables
if "request_count" not in st.session_state:
    st.session_state.request_count = 0
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

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

def construct_prompt(user_question, sensor_data):
    """Construct a detailed prompt combining the user's question with sensor data context"""
    
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
    
    Please provide the most accurate and practical advice based on this information.
    """
    
    return system_prompt, user_prompt

def ask_deepseek(user_question, sensor_data=None):
    """Send a prompt to the DeepSeek model via OpenRouter API"""
    
    if sensor_data is None:
        sensor_data = simulate_iot_data()
    
    system_prompt, user_prompt = construct_prompt(user_question, sensor_data)
    
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
        with st.spinner("🌱 AgriGuardian is analyzing your question..."):
            response = requests.post(API_URL, headers=headers, json=data)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
            else:
                return "Error: Unexpected response format from API."
                
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            return "Daily quota exceeded. Please try again tomorrow."
        return f"API Error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

def display_sensor_data(sensor_data):
    """Format sensor data for Streamlit display"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("🌡️ Temperature", f"{sensor_data['temperature']}°C")
        st.metric("💧 Humidity", f"{sensor_data['humidity']}%")
        st.metric("🌱 Soil Moisture", f"{sensor_data['soil_moisture']}%")
        
    with col2:
        st.metric("☀️ Light Level", f"{sensor_data['light_level']} Lux") 
        st.metric("🌧️ Rainfall (24h)", f"{sensor_data['rainfall_last_24h']}mm")
        st.write(f"🕒 **Timestamp:** {sensor_data['timestamp']}")

def main():
    st.set_page_config(
        page_title="AgriGuardian - AI Farming Assistant",
        page_icon="🌱",
        layout="wide"
    )
    
    # Sidebar with info and API usage
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/farm.png", width=100)
        st.title("🌱 AgriGuardian")
        st.subheader("AI Farming Assistant")
        st.write("Ask any farming or agriculture question, and get AI-powered advice based on your farm's conditions.")
        st.divider()
        st.write(f"**API Usage:** {st.session_state.request_count}/50 daily limit")
        
        # Option to reset chat
        if st.button("Start New Chat"):
            st.session_state.chat_history = []
            st.experimental_rerun()
        
        # Option to generate new sensor data
        if st.button("Generate New Sensor Data"):
            st.session_state.sensor_data = simulate_iot_data()
            st.experimental_rerun()
    
    # Main chat interface
    st.title("🌱 AgriGuardian - AI Farming Assistant")
    
    # Generate sensor data if not already in session
    if "sensor_data" not in st.session_state:
        st.session_state.sensor_data = simulate_iot_data()
    
    # Display sensor data and its visualization
    st.subheader("📊 Current Farm Conditions")
    display_sensor_data(st.session_state.sensor_data)
    
    # Create line chart for historical sensor data (simulated)
    if "historical_data" not in st.session_state:
        # Generate historical data for last 24 hours
        times = pd.date_range(end=datetime.now(), periods=24, freq="H")
        st.session_state.historical_data = pd.DataFrame({
            'Time': times,
            'Temperature': [round(random.uniform(18, 42), 1) for _ in range(24)],
            'Humidity': [round(random.uniform(25, 95), 1) for _ in range(24)],
            'Soil_Moisture': [round(random.uniform(8, 65), 1) for _ in range(24)]
        })
    
    st.subheader("📈 24-Hour Trends")
    chart_data = st.session_state.historical_data.melt(
        id_vars=['Time'], 
        value_vars=['Temperature', 'Humidity', 'Soil_Moisture'],
        var_name='Metric', 
        value_name='Value'
    )
    
    st.line_chart(
        chart_data, 
        x='Time', 
        y='Value', 
        color='Metric'
    )
    
    # Chat history display
    st.subheader("💬 Conversation")
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.chat_message("user", avatar="👨‍🌾").write(message["content"])
        else:
            st.chat_message("assistant", avatar="🌱").write(message["content"])
    
    # Chat input
    user_input = st.chat_input("Type your farming question here...")
    if user_input:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Display user message
        st.chat_message("user", avatar="👨‍🌾").write(user_input)
        
        # Get AI response
        response = ask_deepseek(user_input, st.session_state.sensor_data)
        
        # Add AI response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        # Display AI response
        st.chat_message("assistant", avatar="🌱").write(response)
        
        # Update request count
        st.session_state.request_count += 1
        
        # Update the sidebar with new count
        st.sidebar.write(f"**API Usage:** {st.session_state.request_count}/50 daily limit")

if __name__ == "__main__":
    main() 