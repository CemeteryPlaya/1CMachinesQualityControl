# -*- coding: utf-8 -*-
"""
Фоновый воркер надёжной выгрузки в 1С.

Вместо fire-and-forget потоков задачи кладутся в таблицу one_c_sync_queue
(payload = исходные данные формы) и обрабатываются здесь с ретраями
и экспоненциальной паузой. Статус каждой задачи виден в БД
(synced/attempts/last_error) — расхождения Postgres↔1С стали наблюдаемыми.

Дополнительно (опционально): очистка фотографий старше PHOTO_RETENTION_DAYS.
"""
import os
import shutil
import logging
import threading
import time
from datetime import datetime, timedelta

import odata_service
from database import fetch_due_1c_tasks, mark_1c_task

logger = logging.getLogger(__name__)

_wake = threading.Event()

# Такой же дефолт, как в app_routes.PHOTO_BASE (не импортируем во избежание цикла)
_PHOTO_BASE = os.getenv("PHOTO_STORAGE_DIR", os.path.join(os.getcwd(), "data", "photos"))
_PHOTO_RETENTION_DAYS = int(os.getenv("PHOTO_RETENTION_DAYS", "0"))  # 0 = отключено


def poke():
    """Будит воркер сразу после постановки задачи (иначе — раз в 60 сек)."""
    _wake.set()


def _process_task(task) -> tuple:
    """Выполняет одну задачу. Возвращает (ok, error_note)."""
    kind = task['kind']
    payload = task['payload'] or {}
    record_id = task['record_id']

    if kind == 'checklist':
        if not odata_service.ODATA_DOC_URL:
            return True, '1C URL not configured — skipped'
        result = odata_service.post_checklist_to_1c(payload, record_id)
    elif kind == 'to_report':
        if not odata_service.ODATA_TO_DOC_URL:
            return True, '1C URL not configured — skipped'
        result = odata_service.post_to_report_to_1c(payload, record_id)
    elif kind == 'mileage':
        if not odata_service.ODATA_MILEAGE_REGISTER_URL:
            return True, '1C URL not configured — skipped'
        result = odata_service.post_mileage_to_1c(
            machine_ref_key=payload.get('machine_ref_key'),
            mileage=payload.get('mileage', 0),
            motorhours=payload.get('motorhours', 0),
            source=payload.get('source', 'checklist'),
            vehicle_type=payload.get('vehicle_type', 'lv'),
        )
    else:
        return True, f'unknown kind {kind} — skipped'

    if result is not None:
        return True, None
    return False, '1C post failed (см. лог odata_service)'


def _cleanup_old_photos():
    """Удаляет папки с фото старше PHOTO_RETENTION_DAYS (если включено)."""
    if _PHOTO_RETENTION_DAYS <= 0:
        return
    cutoff = time.time() - _PHOTO_RETENTION_DAYS * 86400
    for subdir in ('daily', 'to'):
        root = os.path.join(_PHOTO_BASE, subdir)
        if not os.path.isdir(root):
            continue
        for name in os.listdir(root):
            path = os.path.join(root, name)
            try:
                if os.path.isdir(path) and os.path.getmtime(path) < cutoff:
                    shutil.rmtree(path, ignore_errors=True)
                    logger.info(f"Photo retention: removed {path}")
            except OSError as e:
                logger.warning(f"Photo retention: cannot process {path}: {e}")


def _loop():
    logger.info("1C sync worker started")
    last_cleanup = 0.0
    while True:
        _wake.wait(timeout=60)
        _wake.clear()
        try:
            tasks = fetch_due_1c_tasks(limit=20)
            for task in tasks:
                ok, note = _process_task(task)
                mark_1c_task(task['id'], ok, note)
                if ok:
                    logger.info(f"1C task #{task['id']} ({task['kind']}) synced"
                                + (f" ({note})" if note else ""))
                else:
                    logger.warning(f"1C task #{task['id']} ({task['kind']}) failed, "
                                   f"attempt {task['attempts'] + 1}: {note}")
        except Exception as e:
            logger.error(f"1C sync worker iteration failed: {e}")

        # Ретеншн фото — не чаще раза в сутки
        if time.time() - last_cleanup > 86400:
            last_cleanup = time.time()
            try:
                _cleanup_old_photos()
            except Exception as e:
                logger.error(f"Photo retention failed: {e}")


def start_sync_worker():
    threading.Thread(target=_loop, daemon=True).start()
