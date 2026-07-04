# -*- coding: utf-8 -*-
"""
Уведомления администраторов о новых отчётах:
- мгновенные push-сообщения в Telegram (флаг receive_instant_notifications);
- ежедневная сводка «кто и сколько отчётов отправил сегодня»
  (флаг receive_daily_digest), время задаётся env DAILY_DIGEST_TIME (HH:MM).
"""
import os
import logging
import threading
import time
from datetime import datetime, date

import requests

from bot_instance import BOT_TOKEN
from database import (get_admins_with_flag, get_submission_stats_for_date,
                      claim_app_state)
from time_utils import now_local, today_local

logger = logging.getLogger(__name__)

REPORT_TYPE_NAMES = {
    "daily": "Ежедневный чек-лист",
    "weekly": "Чек-лист",
    "to": "Отчет о ТО",
}


def _send_telegram(chat_id: str, text: str) -> None:
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        resp = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to send admin notification to {chat_id}: {e}")


def notify_admins_new_report(report_type: str, report_id: int, summary: dict) -> None:
    """Мгновенное push-уведомление админам о новом отчёте (в фоновом потоке).

    summary — словарь строк для тела сообщения: sender, machine, project и т.п.
    """
    def worker():
        admins = get_admins_with_flag('receive_instant_notifications')
        recipients = [a for a in admins if a.get('telegram_user_id')]
        if not recipients:
            return

        type_name = REPORT_TYPE_NAMES.get(report_type, report_type)
        lines = [f"🔔 {type_name} №{report_id}"]
        if summary.get('sender'):
            lines.append(f"👤 Отправил: {summary['sender']}")
        if summary.get('telegram_user_id'):
            lines.append(f"🆔 Telegram ID: {summary['telegram_user_id']}")
        if summary.get('machine'):
            lines.append(f"🚜 Машина: {summary['machine']}")
        if summary.get('project'):
            lines.append(f"📁 Проект: {summary['project']}")
        if summary.get('address'):
            lines.append(f"📍 Адрес: {summary['address']}")
        lines.append(f"🕓 {now_local().strftime('%d.%m.%Y %H:%M:%S')}")
        text = "\n".join(lines)

        for admin in recipients:
            _send_telegram(admin['telegram_user_id'], text)
        logger.info(f"Instant notification for {report_type} #{report_id} sent to "
                    f"{len(recipients)} admin(s)")

    threading.Thread(target=worker, daemon=True).start()


def build_daily_digest(day: date) -> str:
    """Формирует текст дневной сводки: кто и сколько отчётов отправил."""
    stats = get_submission_stats_for_date(day)
    total = stats['daily_total'] + stats['weekly_total'] + stats['to_total']

    lines = [f"📊 Сводка отчетов за {day.strftime('%d.%m.%Y')}",
             f"Всего отправлено: {total}", ""]

    sections = [
        ("📅 Ежедневные чек-листы", stats['daily'], stats['daily_total']),
        ("🗓 Еженедельные чек-листы", stats['weekly'], stats['weekly_total']),
        ("🔧 Отчеты о ТО", stats['to'], stats['to_total']),
    ]
    for title, rows, section_total in sections:
        lines.append(f"{title}: {section_total}")
        for row in rows:
            lines.append(f"  • {row['sender']}: {row['cnt']}")
        lines.append("")

    if total == 0:
        lines.append("Сегодня отчеты не отправлялись.")

    return "\n".join(lines).strip()


def send_daily_digest(day: date = None) -> int:
    """Отправляет дневную сводку админам с флагом receive_daily_digest.

    Возвращает число получателей.
    """
    day = day or today_local()
    admins = get_admins_with_flag('receive_daily_digest')
    recipients = [a for a in admins if a.get('telegram_user_id')]
    if not recipients:
        return 0

    text = build_daily_digest(day)
    for admin in recipients:
        _send_telegram(admin['telegram_user_id'], text)
    logger.info(f"Daily digest for {day} sent to {len(recipients)} admin(s)")
    return len(recipients)


def _parse_digest_time() -> tuple:
    raw = os.getenv("DAILY_DIGEST_TIME", "18:00")
    try:
        hh, mm = raw.strip().split(":")
        return int(hh) % 24, int(mm) % 60
    except Exception:
        logger.warning(f"Bad DAILY_DIGEST_TIME '{raw}', falling back to 18:00")
        return 18, 0


def _digest_loop():
    """Тик раз в минуту: если время отправки наступило и сводка за сегодня ещё
    не уходила — отправляем. Отметка хранится в БД (app_state), поэтому рестарт
    после времени отправки не теряет сводку, а второй инстанс не шлёт дубль
    (атомарный claim)."""
    hour, minute = _parse_digest_time()
    logger.info(f"Daily digest scheduler started (send time {hour:02d}:{minute:02d})")
    while True:
        try:
            now = now_local()
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            today_str = now.strftime('%Y-%m-%d')
            if now >= target and claim_app_state('daily_digest_sent', today_str):
                send_daily_digest(today_local())
        except Exception as e:
            logger.error(f"Daily digest send failed: {e}")
        time.sleep(60)


def start_daily_digest_scheduler() -> None:
    threading.Thread(target=_digest_loop, daemon=True).start()
