import os
import logging
from aiogram import Bot
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize Bot instance
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    logger.warning("⚠️ BOT_TOKEN not set properly!")
else:
    logger.info(f"✅ Bot token loaded (length: {len(BOT_TOKEN)} chars)")

bot = Bot(token=BOT_TOKEN)
