# -*- coding: utf-8 -*-
"""
Конфигурация формы "Отчет о проведенном ТО"
"""
from typing import List, Dict, Any
from translations import FIELD_LABELS, SECTION_HEADERS, get_translation


def get_form_config(lang: str = "ru") -> List[Dict[str, Any]]:
    return [
        {
            "id": "timestamp",
            "label": get_translation(FIELD_LABELS, "timestamp", lang),
            "type": "hidden",
            "required": False
        },
        {
            "id": "to_section_general",
            "type": "header",
            "label": get_translation(SECTION_HEADERS, "to_section_general", lang)
        },
        {
            "id": "to_date",
            "label": get_translation(FIELD_LABELS, "to_date", lang),
            "type": "date",
            "required": True
        },
        {
            "id": "department_uid",
            "label": get_translation(FIELD_LABELS, "department_uid", lang),
            "type": "select",
            "required": True,
            "options": []
        },
        {
            "id": "machine_uid",
            "label": get_translation(FIELD_LABELS, "machine_uid", lang),
            "type": "select",
            "required": True,
            "options": []
        },
        {
            "id": "last_mileage_display",
            "label": get_translation(FIELD_LABELS, "last_mileage", lang),
            "type": "readonly",
            "required": False
        },
        {
            "id": "to_mileage",
            "label": get_translation(FIELD_LABELS, "to_mileage", lang),
            "type": "number",
            "required": False
        },
        {
            "id": "to_motorhours",
            "label": get_translation(FIELD_LABELS, "to_motorhours", lang),
            "type": "number",
            "required": False
        },
        {
            "id": "responsible_person_uid",
            "label": get_translation(FIELD_LABELS, "responsible_person", lang),
            "type": "select",
            "required": True,
            "options": []
        },
        {
            "id": "to_section_repair",
            "type": "header",
            "label": get_translation(SECTION_HEADERS, "to_section_repair", lang)
        },
        {
            "id": "repair_type_uid",
            "label": get_translation(FIELD_LABELS, "repair_type", lang),
            "type": "select",
            "required": True,
            "options": []
        },
        {
            "id": "breakdown_reason",
            "label": get_translation(FIELD_LABELS, "breakdown_reason", lang),
            "type": "textarea",
            "required": False,
            "maxlength": 2000,
            "initially_hidden": True
        },
        {
            "id": "repair_start_date",
            "label": get_translation(FIELD_LABELS, "repair_start_date", lang),
            "type": "date",
            "required": True
        },
        {
            "id": "repair_end_date",
            "label": get_translation(FIELD_LABELS, "repair_end_date", lang),
            "type": "date",
            "required": True
        },
        {
            "id": "to_section_downtime",
            "type": "header",
            "label": get_translation(SECTION_HEADERS, "to_section_downtime", lang)
        },
        {
            "id": "downtime_days",
            "label": get_translation(FIELD_LABELS, "downtime_days", lang),
            "type": "number",
            "required": True
        },
        {
            "id": "downtime_hours",
            "label": get_translation(FIELD_LABELS, "downtime_hours", lang),
            "type": "number",
            "required": True
        },
        # --- Табличные части ---
        {
            "id": "to_section_materials",
            "type": "header",
            "label": get_translation(SECTION_HEADERS, "to_section_materials", lang)
        },
        {
            "id": "materials_table",
            "type": "repeater",
            "required": False,
            "fields": [
                {"id": "nomenclature", "label": get_translation(FIELD_LABELS, "nomenclature", lang), "type": "select", "select_source": "nomenclature"},
                {"id": "quantity", "label": get_translation(FIELD_LABELS, "quantity", lang), "type": "number"},
                {"id": "unit", "label": get_translation(FIELD_LABELS, "unit", lang), "type": "select", "select_source": "units"},
                {"id": "cost", "label": get_translation(FIELD_LABELS, "cost", lang), "type": "number"},
            ]
        },
        {
            "id": "to_section_works",
            "type": "header",
            "label": get_translation(SECTION_HEADERS, "to_section_works", lang)
        },
        {
            "id": "works_table",
            "type": "repeater",
            "required": False,
            "fields": [
                {"id": "work_type", "label": get_translation(FIELD_LABELS, "work_type", lang), "type": "text"},
                {"id": "performer", "label": get_translation(FIELD_LABELS, "performer", lang), "type": "text"},
                {"id": "duration", "label": get_translation(FIELD_LABELS, "duration", lang), "type": "text"},
                {"id": "note", "label": get_translation(FIELD_LABELS, "note", lang), "type": "text"},
            ]
        },
        # --- Результат проверки ---
        {
            "id": "inspection_result",
            "label": get_translation(FIELD_LABELS, "inspection_result", lang),
            "type": "textarea",
            "required": False,
            "maxlength": 2000,
            "initially_hidden": True
        },
        # --- Комментарии ---
        {
            "id": "comments",
            "label": get_translation(FIELD_LABELS, "comments", lang),
            "type": "textarea",
            "required": False,
            "maxlength": 5000
        },
    ]
