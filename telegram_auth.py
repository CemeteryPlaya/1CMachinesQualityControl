# -*- coding: utf-8 -*-
"""
Валидация Telegram WebApp initData (подпись HMAC-SHA256 токеном бота).

Используется и админкой (вход по Telegram ID), и формами отправки:
telegram_user_id берётся из подписанного initData, а не из тела запроса,
поэтому подделать отправителя нельзя.

REQUIRE_TELEGRAM_AUTH=0 в .env отключает обязательную проверку на формах
(нужно только для локальной отладки вне Telegram; в проде держать включённой).
"""
import os
import hmac
import json
import hashlib
import logging
from urllib.parse import parse_qsl

from bot_instance import BOT_TOKEN

logger = logging.getLogger(__name__)

REQUIRE_TELEGRAM_AUTH = os.getenv("REQUIRE_TELEGRAM_AUTH", "1") not in ("0", "false", "False")


def validate_init_data(init_data: str):
    """Проверяет подпись initData. Возвращает dict user или None."""
    if not init_data:
        return None
    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = parsed.pop('hash', None)
        if not received_hash:
            return None
        data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(parsed.items()))
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calculated, received_hash):
            return None
        return json.loads(parsed.get('user', '{}'))
    except Exception as e:
        logger.warning(f"initData validation error: {e}")
        return None


def resolve_submit_user(data: dict):
    """Аутентификация отправки формы.

    Извлекает init_data из payload (и удаляет его, чтобы не попал в БД),
    валидирует подпись и подменяет telegram_user_id проверенным значением.

    Возвращает (ok, error_message): ok=False — отправку нужно отклонить.
    """
    init_data = data.pop('init_data', '') or ''
    user = validate_init_data(init_data)
    if user and user.get('id'):
        data['telegram_user_id'] = user['id']
        return True, None
    if REQUIRE_TELEGRAM_AUTH:
        logger.warning("Submission rejected: missing/invalid Telegram initData")
        return False, "Telegram authentication required"
    # Режим отладки: доверяем клиентскому telegram_user_id
    return True, None
