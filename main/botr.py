from dotenv import load_dotenv
import os
from mainc import Tbot

env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv()

if __name__ == "__main__":
    bot_token = os.getenv("BOT_TOKEN")
    if bot_token is None:
        raise ValueError("Bot_TOKEN is not set")
    telegram_bot = Tbot(bot_token)
    telegram_bot.run()