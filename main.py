import discord_bot
from config import setup_logging

# Set up logging
logger = setup_logging()

if __name__ == '__main__':
    logger.info("Starting Discord bot...")
    discord_bot.run_discord_bot()