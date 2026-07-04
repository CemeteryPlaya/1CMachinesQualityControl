# -*- coding: utf-8 -*-
"""
Конфигурация формы "Ежедневный чек-лист".
Меньше еженедельного: шапка + фотоотчёт + 3 проверки (масло, антифриз, фильтр),
у каждой проверки — радио + комментарий + фото состояния.
"""
from typing import List, Dict, Any
from translations import (FIELD_LABELS, SECTION_HEADERS, OPTION_TRANSLATIONS,
                          get_translation)

# Предупреждение механику при ненормальном состоянии (как в еженедельных формах)
_WARNING_TEXT = {
    "ru": "При наличии каких-либо проблем, сообщите механику",
    "en": "If there are any problems, report to the mechanic",
    "kk": "Қандай да бір ақаулар болса, механикке хабарлаңыз",
    "uz": "Qandaydir muammolar bo'lsa, mexanikka xabar bering",
}


def _translate_options(options: List[str], lang: str) -> List[str]:
    return [get_translation(OPTION_TRANSLATIONS, opt, lang) for opt in options]


def _check_block(field_id: str, label_key: str, lang: str) -> List[Dict[str, Any]]:
    """Один узел проверки: радио + комментарий + блок фото (1-3, минимум 1)."""
    return [
        {
            "id": field_id,
            "label": get_translation(FIELD_LABELS, label_key, lang),
            "type": "radio",
            "required": True,
            "options": _translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "warning_text": _WARNING_TEXT[lang],
        },
        {
            "id": f"{field_id}_comment",
            "label": get_translation(FIELD_LABELS, "check_comment", lang),
            "type": "textarea",
            "required": False,
            "maxlength": 2000,
            "collapsible": True,
        },
        {
            "id": f"{field_id}_photos",
            "label": get_translation(FIELD_LABELS, "check_photos", lang),
            "type": "photo",
            "required": True,
            "min": 1,
            "max": 3,
        },
    ]


def get_form_config(lang: str = "ru") -> List[Dict[str, Any]]:
    config: List[Dict[str, Any]] = [
        {
            "id": "timestamp",
            "label": get_translation(FIELD_LABELS, "timestamp", lang),
            "type": "hidden",
            "required": False,
        },
        # --- Шапка ---
        {
            "id": "section_1",
            "type": "header",
            "label": get_translation(SECTION_HEADERS, "section_1", lang),
        },
        {
            "id": "inspection_date",
            "label": get_translation(FIELD_LABELS, "inspection_date", lang),
            "type": "date",
            "required": True,
        },
        {
            # "Проект" — справочник Подразделений 1С (как в других формах), с подписью «Проект»
            "id": "department_uid",
            "label": get_translation(FIELD_LABELS, "project", lang),
            "type": "select",
            "required": True,
            "options": [],
        },
        {
            # "Оператор" — справочник водителей 1С (driver_uid), с подписью «Оператор»
            "id": "driver_uid",
            "label": get_translation(FIELD_LABELS, "operator", lang),
            "type": "select",
            "required": True,
            "options": [],
        },
        {
            "id": "machine_uid",
            "label": get_translation(FIELD_LABELS, "machine_uid", lang),
            "type": "select",
            "required": True,
            "options": [],
        },
        {
            "id": "capacity_of_fuel_in_fueltank",
            "label": get_translation(FIELD_LABELS, "capacity_of_fuel_in_fueltank", lang),
            "type": "number",
            "required": True,
        },
        {
            "id": "fuel_type",
            "label": {"ru": "Тип топлива", "en": "Fuel type", "kk": "Жанармай түрі", "uz": "Yoqilg'i turi"}[lang],
            "type": "radio",
            "required": True,
            "options": _translate_options(["Бензин", "Дизель", "Газ (Пропан)", "Газ (Метан)"], lang),
        },
        {
            "id": "motorhours",
            "label": get_translation(FIELD_LABELS, "motorhours", lang),
            "type": "number",
            "required": True,
            "hint": get_translation(FIELD_LABELS, "motorhours_hint", lang),
        },
        # --- Фотоотчёт (между шапкой и проверками) ---
        {
            "id": "daily_section_photos",
            "type": "header",
            "label": get_translation(SECTION_HEADERS, "daily_section_photos", lang),
        },
        {
            "id": "general_photos",
            "label": get_translation(FIELD_LABELS, "general_photos", lang),
            "hint": get_translation(FIELD_LABELS, "general_photos_hint", lang),
            "type": "photo",
            "required": True,
            "min": 1,
            "max": 5,
        },
        # --- Проверка узлов ---
        {
            "id": "daily_section_checks",
            "type": "header",
            "label": get_translation(SECTION_HEADERS, "daily_section_checks", lang),
        },
    ]

    config += _check_block("engine_oil", "engine_oil", lang)
    config += _check_block("antifreeze", "antifreeze", lang)
    config += _check_block("air_filter", "air_filter", lang)

    return config
