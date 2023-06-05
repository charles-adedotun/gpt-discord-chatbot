import requests
from config import setup_logging, get_flask_port

# Set up logging
logger = setup_logging()

# Get flask port
FLASK_PORT = get_flask_port()

def send_message_to_chain(username, message_input, input_type='text'):
    url = f'http://127.0.0.1:{FLASK_PORT}/process'
    data = {
        'username': username,
        'message_input': message_input,
        'input_type': input_type
    }

    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        return result
    except requests.exceptions.RequestException as e:
        logger.error(f'Error occurred during the request: {e}')
        return None
