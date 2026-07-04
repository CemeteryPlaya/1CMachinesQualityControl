# -*- coding: utf-8 -*-
"""
Локальное время приложения (по умолчанию Asia/Tashkent, UTC+5).

datetime.now() без зоны зависит от ОС: в Docker-контейнере это UTC,
на Windows переменная TZ игнорируется вовсе. Все пользовательские
timestamp'ы (отчёты, уведомления, сводка, документы 1С) должны идти
через now_local()/today_local(), а не через голый datetime.now().

Настройка: APP_TIMEZONE (имя зоны IANA) или APP_UTC_OFFSET (часы,
фолбэк, если база зон недоступна).
"""
import os
import logging
from datetime import datetime, date, timezone, timedelta

logger = logging.getLogger(__name__)

TZ_NAME = os.getenv("APP_TIMEZONE", "Asia/Tashkent")

try:
    from zoneinfo import ZoneInfo
    APP_TZ = ZoneInfo(TZ_NAME)
    # Имя зоны валидно — его же используем для session timezone в Postgres
    PG_TIMEZONE = TZ_NAME
except Exception as e:
    _offset = int(os.getenv("APP_UTC_OFFSET", "5"))
    APP_TZ = timezone(timedelta(hours=_offset))
    # POSIX-нотация 'UTC+5' в Postgres означает противоположный знак —
    # чтобы не ошибиться, в фолбэке session timezone не задаём
    PG_TIMEZONE = None
    logger.warning(f"Timezone '{TZ_NAME}' unavailable ({e}) — "
                   f"using fixed offset UTC+{_offset}")


def now_local() -> datetime:
    """Текущее время в зоне приложения (aware)."""
    return datetime.now(APP_TZ)


def today_local() -> date:
    """Текущая дата в зоне приложения."""
    return now_local().date()
