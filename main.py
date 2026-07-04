import os
import sys
import time
import secrets
import threading
import logging
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from flask import Flask
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from werkzeug.security import generate_password_hash

# Import local modules
from bot_instance import bot, BOT_TOKEN
from bot_handlers import router as bot_router
from app_routes import app_bp
from admin_routes import admin_bp
from database import init_db, ensure_default_admin
from notifications import start_daily_digest_scheduler
from sync_worker import start_sync_worker
import odata_service

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

# Configuration
FLASK_PORT = 5000
FLASK_HOST = "0.0.0.0"

# Initialize Flask App
flask_app = Flask(__name__)
# Секрет сессий: FLASK_SECRET_KEY из .env; иначе случайный на каждый старт
# (сессии админки инвалидируются при рестарте — вход через Telegram восстановит их)
_secret = os.getenv("FLASK_SECRET_KEY")
if not _secret:
    _secret = secrets.token_hex(32)
    logger.warning("FLASK_SECRET_KEY not set — using random per-start key. "
                   "Задайте FLASK_SECRET_KEY в .env, чтобы сессии переживали рестарт.")
flask_app.secret_key = _secret

# Ограничение размера запроса (фото и т.п.): защита от исчерпания диска/памяти
flask_app.config['MAX_CONTENT_LENGTH'] = int(os.getenv("MAX_UPLOAD_MB", "25")) * 1024 * 1024

flask_app.register_blueprint(app_bp)
flask_app.register_blueprint(admin_bp)

# Initialize Dispatcher
# Check if token is set to placeholder
if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    logger.warning("BOT_TOKEN is not set. Please export BOT_TOKEN environment variable.")

dp = Dispatcher(storage=MemoryStorage())
dp.include_router(bot_router)

def run_flask():
    """Запускает веб-сервер: waitress (прод), при его отсутствии — dev-сервер Flask."""
    try:
        from waitress import serve
        logger.info(f"Starting waitress server on {FLASK_HOST}:{FLASK_PORT}...")
        serve(flask_app, host=FLASK_HOST, port=FLASK_PORT, threads=8)
    except ImportError:
        logger.warning("waitress not installed — falling back to Flask dev server "
                       "(не для продакшена)")
        flask_app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, use_reloader=False)


def init_db_with_retry(attempts: int = 30, delay: float = 2.0):
    """Ждёт готовности Postgres (важно в Docker: БД поднимается дольше приложения)."""
    for attempt in range(1, attempts + 1):
        try:
            init_db()
            return
        except Exception as e:
            logger.warning(f"DB not ready (attempt {attempt}/{attempts}): {e}")
            time.sleep(delay)
    logger.critical("Database is unreachable — exiting.")
    sys.exit(1)

async def main():
    """Runs the Telegram Bot."""
    logger.info("Starting Telegram Bot polling...")
    # Delete webhook to ensure polling works, just in case
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Initialize database (с ожиданием готовности Postgres)
    logger.info("Initializing database...")
    init_db_with_retry()

    # Создаём первого суперадмина, если таблица admins пуста.
    # Без ADMIN_PASSWORD в .env пароль генерируется случайно и печатается в лог —
    # дефолтного admin/admin больше нет.
    admin_user = os.getenv("ADMIN_USERNAME", "admin")
    admin_pass = os.getenv("ADMIN_PASSWORD")
    if not admin_pass:
        admin_pass = secrets.token_urlsafe(10)
        logger.warning(f"ADMIN_PASSWORD not set — generated password for '{admin_user}': "
                       f"{admin_pass} (действует только если таблица admins была пуста; "
                       f"задайте ADMIN_PASSWORD в .env)")
    ensure_default_admin(admin_user, generate_password_hash(admin_pass))

    # Планировщик ежедневной сводки для админов (DAILY_DIGEST_TIME, по умолчанию 18:00)
    start_daily_digest_scheduler()

    # Воркер надёжной выгрузки в 1С (очередь one_c_sync_queue с ретраями)
    start_sync_worker()

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
