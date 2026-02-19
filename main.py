import os
import sys
import threading
import logging
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from flask import Flask
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Import local modules
from bot_instance import bot, BOT_TOKEN
from bot_handlers import router as bot_router
from app_routes import app_bp
from database import init_db
import odata_service

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

# Configuration
FLASK_PORT = 5000
FLASK_HOST = "0.0.0.0"

# Initialize Flask App
flask_app = Flask(__name__)
flask_app.register_blueprint(app_bp)

# Initialize Dispatcher
# Check if token is set to placeholder
if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    logger.warning("BOT_TOKEN is not set. Please export BOT_TOKEN environment variable.")

dp = Dispatcher(storage=MemoryStorage())
dp.include_router(bot_router)

def run_flask():
    """Runs the Flask app."""
    logger.info(f"Starting Flask server on {FLASK_HOST}:{FLASK_PORT}...")
    flask_app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, use_reloader=False)

async def main():
    """Runs the Telegram Bot."""
    logger.info("Starting Telegram Bot polling...")
    # Delete webhook to ensure polling works, just in case
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Initialize database
    logger.info("Initializing database...")
    init_db()

    # Perform initial data synchronization
    logger.info("Performing initial data synchronization from 1C...")
    try:
        machines = odata_service.sync_machines()
        logger.info(f"Loaded {len(machines)} machines from 1C/DB")
    except Exception as e:
        logger.error(f"Failed to sync machines: {e}")

    try:
        employees = odata_service.sync_employees()
        logger.info(f"Loaded {len(employees)} employees from 1C/DB")
    except Exception as e:
        logger.error(f"Failed to sync employees: {e}")

    try:
        departments = odata_service.sync_departments()
        logger.info(f"Loaded {len(departments)} departments from 1C/DB")
    except Exception as e:
        logger.error(f"Failed to sync departments: {e}")

    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True # Daemon thread exits when main thread exits
    flask_thread.start()

    # Start Aiogram polling in the main thread (asyncio loop)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopping bot...")
