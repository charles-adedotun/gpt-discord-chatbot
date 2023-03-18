import discord
import os
import responses

# Set the Discord API token
TOKEN = os.getenv("DISCORD_API_KEY")

# Function to send a message to the user, either as a private message or as a message in the same channel
async def send_message(message, user_id, user_message, is_private):
    try:
        # Get the bot's response to the user message
        response = responses.get_response(user_id, user_message)
        
        # Send the response either as a private message or as a message in the same channel
        if is_private:
            await message.author.send(response)
        else:
            await message.channel.send(response)

    except discord.errors.Forbidden:
        # Handle errors if the bot doesn't have permission to send messages to the user
        error_msg = f"Error: Bot doesn't have permission to send messages to {message.author}"
        print(error_msg)
        await message.channel.send(error_msg)

    except Exception as e:
        # Handle any other errors that might occur
        error_msg = f"Error: {str(e)}"
        print(error_msg)
        await message.channel.send(error_msg)

# Function to run the Discord bot
def run_discord_bot():
    # Set the appropriate intents for the bot to listen for message events
    intents = discord.Intents.default()
    intents.message_content = True
    
    # Create a new Discord client and set the event handlers
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        # Handle the bot's initialization when it starts running
        print(f'{client.user} is now running!')

    @client.event
    async def on_message(message):
        # Handle incoming messages from users
        if message.author == client.user:
            return

        # Get the user ID, username, message content, and channel from the message
        username = str(message.author)
        user_id = str(message.author.id)
        user_message = message.content.decode('utf-8') # decode the message content from bytes to a string
        channel = str(message.channel)

        # Print the user's message to the console for debugging purposes
        print(f'{username} said: "{user_message}" ({channel})')

        # Check if the user's message is a private message to the bot (starting with a question mark)
        if user_message.startswith('?'):
            user_message = user_message[1:].strip()
            await send_message(message, user_id, user_message, is_private=True)
        else:
            await send_message(message, user_id, user_message, is_private=False)
    
    # Run the Discord bot using the API token
    client.run(TOKEN)
