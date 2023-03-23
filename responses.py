import os
import logging
import threading
import openai
import asyncio
import time
from collections import deque
# Set the OpenAI API key and language model ID
try:
    openai.api_key = os.environ["OPENAI_API_KEY"]
except KeyError:
    logging.error("Please set the environment variable OPENAI_API_KEY to use the OpenAI API.")
model_id = 'gpt-3.5-turbo'

# Define the default system message and maximum number of tokens for the GPT-3.5 API call
system = 'You are πGPT. You will make sure you always think through your responses step-by-step and reiterate till you are certain you did not make any mistakes. Do not make any assumptions.'
max_tokens = 1999

# Create a dictionary to store conversation history for each user
conversation_dict = {}

# Define a dictionary to store the last message timestamp for each user
last_message_dict = {}

# Define a deque to store incoming messages from all users
message_queue = deque()

# Define the maximum number of messages that can be processed per second
max_messages_per_second = 1

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Function to check if a user is allowed to send a message based on the rate limit
class UserRateLimit:
    def __init__(self, max_messages_per_second):
        """
        Initializes a UserRateLimit object

        Parameters:
        max_messages_per_second (int): Maximum number of messages allowed per second
        """
        self.mutex = threading.Lock()
        self.max_messages_per_second = max_messages_per_second
        self.user_last_message_times = {}

    def check_rate_limit(self, user_id):
        """
        Check if a user is allowed to send a message based on the rate limit.

        Parameters:
        user_id (str): The ID of the user who sent the message.

        Returns:
        bool: True if the user is allowed to send a message, False otherwise.
        """

        # Get the current time
        current_time = time.time()

        # Synchronize access to the shared dictionary
        with self.mutex:
            if user_id in self.user_last_message_times:
                # Get the time of the last message sent by the user
                last_message_time = self.user_last_message_times[user_id]
                
                # Calculate the time elapsed since the last message
                time_elapsed = current_time - last_message_time

                # Check if the time elapsed is less than the inverse of max messages per second
                # If it is less, then the user has exceeded the message limit per second and is not allowed to send another message
                if time_elapsed < 1 / self.max_messages_per_second:
                    return False
            # Update the user_last_message_times dictionary with the current time
            self.user_last_message_times[user_id] = current_time

        # Return True if the user is allowed to send another message
        return True

# Function to handle incoming messages from users
async def handle_message(user_id, message):
    """
    Handle an incoming message from a user.

    Parameters:
    user_id (str): The ID of the user.
    message (str): The message sent by the user.
    """
    global response
    # Add the user's message to the message queue
    message_queue.append((user_id, message))
    
    # Create a task to process the messages in the message queue
    response = await process_messages()
    return response

# Function to process incoming messages from the message queue
async def process_messages():
    """
    Process incoming messages from the message queue.
    """
    global response
    while True:
        if message_queue:
            # Get the next message from the queue
            user_id, message = message_queue.popleft()
            
            # Check if the user is allowed to send a message based on the rate limit
            if check_rate_limit(user_id):
                # If the user is allowed to send a message, get a response from the chatbot
                response = await get_response(user_id, message)
                # Send the response to the user
                return response
            else:
                # If the user is not allowed to send a message, add the message back to the queue
                message_queue.appendleft((user_id, message))
        
        # Wait for a short period of time before checking the message queue again
        await asyncio.sleep(1 / max_messages_per_second)

# Function to generate a response using the GPT-3.5 language model based on the conversation history so far
async def ChatGPT_conversation(conversation):
    """
    Generate a response using the GPT-3.5 language model based on the conversation history so far.

    Parameters:
    conversation (list): List of dictionaries representing the conversation history.

    Returns:
    list: Updated list of dictionaries representing the conversation history, with the new response added.
    """
    # Limit the conversation history to the last n messages (e.g. 8 messages)
    n = 8
    conversation = conversation[-n:]

    # Call the OpenAI API to generate a response based on the conversation history
    global response
    response = openai.ChatCompletion.create(
        model=model_id,
        max_tokens = max_tokens,
        messages=conversation
    )
    
    # Add the new response to the conversation history
    conversation.append({'role': response.choices[0].message.role, 'content': response.choices[0].message.content})
    
    # Log the response
    logging.info(f'Response generated: "{response.choices[0].message.content}"')
    
    return conversation

# Function to get a response from the chatbot given the user ID and message
async def get_response(user_id: str, message: str) -> str:
    """
    Get a response from the chatbot given the user ID and message.

    Parameters:
    user_id (str): The ID of the user who sent the message.
    message (str): The message sent by the user.

    Returns:
    str: The response generated by the chatbot.
    """
    # Check if the user has an existing conversation history, and create one if not
    global conversation_dict
    if user_id not in conversation_dict:
        conversation_dict[user_id] = [{'role': 'system', 'content': system}]
    
    # Add the user's message to the conversation history and generate a response using the GPT-3.5 model
    conversation = conversation_dict[user_id]
    conversation.append({'role': 'user', 'content': message})
    
    # Call the ChatGPT_conversation coroutine to generate a response
    task = asyncio.create_task(ChatGPT_conversation(conversation))
    
    # Wait for the response to be generated
    while not task.done():
        await asyncio.sleep(0)
    
    # Get the latest GPT-3.5 response and store the updated conversation history for the user
    conversation = task.result()
    gpt_response = conversation[-1]['content'].strip()
    conversation_dict[user_id] = conversation
    
    # Check the API usage to see if the maximum token limit has been exceeded
    api_usage = response['usage']
    tokens_used = api_usage['total_tokens']
    
    # Log the response
    logging.info(f'Response sent to user {user_id}: "{gpt_response}"')
    
    if tokens_used > max_tokens:
        # If the maximum token limit has been exceeded, clear the conversation history for the user
        conversation_dict[user_id] = [{'role': 'system', 'content': system}]
        return f'`{tokens_used} tokens used. Conversation history has now been cleared. Last response:\n{gpt_response}`'
    else:
        return gpt_response
