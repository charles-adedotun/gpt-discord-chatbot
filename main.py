import bot
import logging

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
  
    logging.info("Starting Discord bot...")
    bot.run_discord_bot()