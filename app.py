from flask import Flask, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
import time
from config import setup_logging, get_flask_port
from Chatbot import Chatbot

# Set up logging
logger = setup_logging()

# Get flask port
FLASK_PORT = get_flask_port()

app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app)

@app.route('/process', methods=['POST'])
def run_agent_chain():
    start_time = time.time()

    try:
        if request.content_type == 'application/json':
            data = request.get_json()
            username = data.get('username')
            message_input = data.get('message_input')
            input_type = data.get('input_type')
        else:
            raise ValueError('Invalid content type')

        # Check if username, message_input and input_type are provided
        if not username or not message_input or not input_type:
            raise ValueError('Username, message_input and input_type are required')

        logger.info(f"Received message from user {username}")
                
        # Initialize chatbot
        chatbot = Chatbot()

        # Check if user exists in DB, if not create user
        user = chatbot.get_user(username)
        if not user:
            chatbot.create_user(username)
            user = chatbot.get_user(username)

        result = None  # Initialize result to a default value

        # Handle the input based on its type
        if input_type == 'text':
            result = chatbot.ask_user_question(username, message_input)
        else:
            raise ValueError('Invalid input_type')

        end_time = time.time()
        processing_time = (end_time - start_time) * 1000  # convert to milliseconds
        logger.info(f'Successfully processed message from user {username} in {processing_time:.0f} milliseconds')

        return jsonify(result)

    except ValueError as e:
        logger.error(f'Bad request: {e}')
        return jsonify({'error': 'Bad request'}), 400
    except Exception as e:
        logger.error(f'Server error: {e}')
        return jsonify({'error': 'Server error'}), 500

if __name__ == '__main__':
    # Start the Flask app
    app.run(host='127.0.0.1', port=FLASK_PORT)
    logger.info(f'Flask is listening on port {FLASK_PORT}')
