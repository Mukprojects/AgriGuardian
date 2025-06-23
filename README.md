# AgriGuardian: AI-Powered Agricultural Assistant

AgriGuardian is an intelligent assistant for farmers that leverages AI to provide personalized agricultural advice based on environmental conditions, crop information, and farmer queries.

## Features

- **Smart Agricultural Advice**: Get personalized recommendations based on real-time environmental conditions
- **Multi-Interface Access**: Access via web browser, SMS (planned), or command line
- **IoT Sensor Integration**: Uses real-time sensor data (temperature, humidity, soil moisture, etc.)
- **Crop-Specific Guidance**: Tailors advice to your specific crops and growth stages
- **Interactive Chat Interface**: Natural conversation with an AI agricultural expert

## Getting Started

### Prerequisites

- Python 3.7+
- OpenRouter API key with access to Amazon Bedrock models (Claude 3 Sonnet)

### Installation

1. Clone this repository:
```bash
git clone https://github.com/Mukprojects/AgriGuardian.git
cd AgriGuardian
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. API Key Setup:
   - You need an OpenRouter API key with access to Amazon Bedrock models
   - Get your API key at: https://openrouter.ai/keys
   - When you run the application for the first time, you'll be prompted to enter your API key
   - You can choose to save the key to a `.env` file for future use

### Running the Application

#### Web Interface

Start the web server:
```bash
python web_server.py
```

When prompted, enter your OpenRouter API key. Then open your browser and navigate to `http://localhost:5000`

#### Command Line Interface

Run the CLI version:
```bash
python main.py
```

When prompted, enter your OpenRouter API key.

## Usage

### Web Interface

1. Upon opening the web interface, you'll be prompted to enter your crop information
2. Input details about your crops, growth stage, and any issues you're experiencing
3. Ask questions in the chat interface about your agricultural concerns
4. Receive detailed, actionable advice based on simulated environmental conditions

### Command Line Interface

1. Run `python main.py`
2. Enter your OpenRouter API key when prompted
3. The CLI will simulate sensor data and ask for your query
4. Receive detailed agricultural advice from the AI

## Testing the API Connection

You can test your API key and connection with:
```bash
python test_api.py
```

This will verify that your OpenRouter API key is working correctly with the Amazon Bedrock model.

## API Limits

- The system has a default limit of 50 API requests per day to control costs
- This can be adjusted in the code if needed
- Be aware of your OpenRouter API usage limits

## Project Structure

- `web_server.py`: Flask web application with chat interface
- `main.py`: Command line interface
- `api.py`: API endpoint definitions for serverless deployment
- `aws_lambda_handler.py`: AWS Lambda integration
- `templates/`: HTML templates for web interface
- `requirements.txt`: Python dependencies

## Future Enhancements

- SMS integration for farmers without internet access
- Actual IoT sensor integration (currently simulated)
- Historical data analysis for trend-based recommendations
- Offline capabilities for remote areas

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Amazon Bedrock AI models used for agricultural knowledge
- OpenRouter for API connectivity
- Flask and Bootstrap for the web interface 