# 🌱 AgriGuardian - AI Assistant for Farmers

AgriGuardian is an AI-powered assistant designed to help farmers get real-time guidance on weather, pests, crop care, and other agricultural concerns, especially in low-connectivity zones.

## Features

- 💬 SMS-style interface for farmer questions (simulated in terminal)
- 🔌 Simulated IoT sensor data (temperature, humidity, soil moisture, etc.)
- 🧠 AI-powered responses using DeepSeek AI model via OpenRouter API
- 🌐 Works efficiently with limited connectivity (50 API calls per day limit)
- 🖥️ Multiple interfaces: CLI, Web UI (Flask), and Streamlit

## Setup Instructions

1. Clone this repository:
```
git clone https://github.com/yourusername/AgriGuardian.git
cd AgriGuardian
```

2. Install required dependencies:
```
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory and add your OpenRouter API key:
```
OPENROUTER_API_KEY=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
```

## Running Different Interfaces

### Command Line Interface
```
python main.py
```

### Streamlit UI
```
streamlit run app.py
```

### Flask Web Server
```
python web_server.py
```

## Deployment to AWS (Serverless)

AgriGuardian can be deployed as a serverless application using AWS Lambda, API Gateway, SNS, and DynamoDB:

1. Install the Serverless Framework:
```
npm install -g serverless
```

2. Configure AWS credentials:
```
serverless config credentials --provider aws --key YOUR_ACCESS_KEY --secret YOUR_SECRET_KEY
```

3. Deploy the application:
```
serverless deploy
```

## Usage

1. When prompted, type your agricultural question as if you were sending an SMS
2. The system will simulate IoT sensor data for farm conditions
3. AgriGuardian will provide tailored advice based on your question and the sensor data
4. To exit, type "exit", "quit", or "q"

## System Architecture

The AgriGuardian system consists of:

1. **Frontend Interfaces**:
   - Command-line interface (main.py)
   - Streamlit web app (app.py)
   - Flask web server (web_server.py)
   - HTML/JS web client (templates/index.html)

2. **Backend Components**:
   - OpenRouter API client for AI processing
   - IoT sensor data simulator
   - AWS Lambda handlers for serverless deployment
   - DynamoDB for user data storage

## API Usage Notes

- The free tier of OpenRouter API with deepseek/deepseek-r1-0528:free has a limit of 50 requests per day
- The application displays your current usage count during the session

## Example Questions

- "Why are my tomato leaves turning yellow?"
- "How often should I water my corn with the current soil moisture?"
- "What's the best time to plant wheat with these conditions?"
- "Is my field ready for harvesting wheat?"
- "How can I control aphids on my cabbage plants naturally?"

## Future Enhancements

- Real SMS integration using AWS SNS/Lambda
- Actual IoT sensor data integration
- Historical data tracking for better recommendations
- Multi-language support for global farmers
- Mobile app for farmers with smartphones 