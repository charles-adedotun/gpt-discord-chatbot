import os
import openai

# Set the OpenAI API key and language model ID
openai.api_key = os.getenv("OPENAI_API_KEY")
model_id = 'gpt-3.5-turbo'

# Define the default system message and maximum number of tokens for the GPT-3.5 API call
system = 'You are πGPT. You will make sure you always think through your responses step-by-step and reiterate till you are certain you did not make any mistakes. Do not make any assumptions.'
max_tokens = 2030

# Create a dictionary to store conversation history for each user
conversation_dict = {}

# Function to generate a response using the GPT-3.5 language model based on the conversation history so far
def ChatGPT_conversation(conversation):
    
    global response
    
    # Call the OpenAI API to generate a response based on the conversation history
    response = openai.ChatCompletion.create(
        model=model_id,
        max_tokens = max_tokens,
        messages=conversation
    )
    
    # Add the new response to the conversation history
    conversation.append({'role': response.choices[0].message.role, 'content': response.choices[0].message.content})
    
    return conversation

# Function to get a response from the chatbot given the user ID and message
def get_response(user_id: str, message: str) -> str:
    
    global conversation_dict
    
    # Check if the user has an existing conversation history, and create one if not
    if user_id not in conversation_dict:
        conversation_dict[user_id] = [{'role': 'system', 'content': system}]
    
    # Add the user's message to the conversation history and generate a response using the GPT-3.5 model
    conversation = conversation_dict[user_id]
    conversation.append({'role': 'user', 'content': message})
    conversation = ChatGPT_conversation(conversation)
    
    # Check the API usage to see if the maximum token limit has been exceeded
    api_usage = response['usage']
    tokens_used = api_usage['total_tokens']
    
    # Get the latest GPT-3.5 response and store the updated conversation history for the user
    gpt_response = conversation[-1]['content'].strip()
    if tokens_used < max_tokens:
        conversation_dict[user_id] = conversation
        return gpt_response
    else:
        # If the maximum token limit has been exceeded, clear the conversation history for the user and return an error message
        conversation_dict[user_id] = [{'role': 'system', 'content': system}]
        return f'`{tokens_used} tokens used. Conversation history has now been cleared. Last response:\n{gpt_response}`'
