import asyncio
import discord
from config import setup_logging, get_discord_api_key
from process_message import send_message_to_chain

# Get Discord API key
DISCORD_API_KEY = get_discord_api_key()

# Set up logging
logger = setup_logging()

async def process_message(message):
    # Get the user ID, username, message content, and channel from the message
    username = str(message.author)
    user_id = str(message.author.id)
    user_message = str(message.content)
    channel = str(message.channel)

    # Print the user's message to the console for debugging purposes
    logger.info(f'{username} said: "{user_message}" ({channel})')

    # Check if the user's message is a private message to the bot (starting with a question mark)
    if user_message.startswith('?'):
        user_message = user_message[1:].strip()
        await send_message(message, user_id, user_message, is_private=True)
    else:
        await send_message(message, user_id, user_message, is_private=False)

# Function to send a message to the user, either as a private message or as a message in the same channel
async def send_message(message, user_id, user_message, is_private):
    """
    Send a message to the user, either as a private message or as a message in the same channel.

    Parameters:
    message (discord.Message): The message object sent by the user.
    user_id (str): The ID of the user.
    user_message (str): The message sent by the user.
    is_private (bool): True if the message is a private message to the bot, False otherwise.
    """
    try:
        # Get the bot's response to the user message
        response = send_message_to_chain(user_id, user_message)

        if response is None:
            response = "I'm sorry, but I couldn't generate a response."

        # Split the response into chunks of 2000 characters or less
        chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]

        # Send each chunk as a separate message
        for chunk in chunks:
            if is_private:
                await message.author.send(chunk)
            else:
                await message.channel.send(chunk)

        # Log the response
        logger.info(f'Response sent to user {user_id}: "{response}"')

    except discord.errors.Forbidden:
        # Handle errors if the bot doesn't have permission to send messages to the user
        error_msg = f"Error: Bot doesn't have permission to send messages to {message.author}"
        logger.error(error_msg)
        await message.channel.send(error_msg)

    except Exception as e:
        # Handle any other errors that might occur
        error_msg = f"Error: {str(e)}"
        logger.error(error_msg)
        await message.channel.send(error_msg)

# Function to run the Discord bot
def run_discord_bot():
    """
    Run the Discord bot.
    """
    # Set the appropriate intents for the bot to listen for message events
    intents = discord.Intents.default()
    intents.message_content = True
    
    # Create a new Discord client and set the event handlers
    client = discord.Client(intents=intents, heartbeat_timeout=360)

    @client.event
    async def on_ready():
        # Handle the bot's initialization when it starts running
        logger.info(f'{client.user} is now running!')

    @client.event
    async def on_message(message):
        # Handle incoming messages from users
        if message.author == client.user:
            return

        # Create an asyncio task to process the message concurrently
        asyncio.create_task(process_message(message))

    try:
        # Run the Discord bot using the API token
        client.run(DISCORD_API_KEY)
    except discord.LoginFailure:
        # Handle login errors gracefully
        logger.error("Failed to log in to Discord API. Please check your API key and try again.")
