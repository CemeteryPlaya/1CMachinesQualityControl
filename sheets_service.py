import os
import logging
from typing import List, Dict, Any, Optional
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from importlib import import_module

load_dotenv()

FORM_CONFIG_MODULES = {
    "lv": "lv_form_config",
    "lv_oa": "lv_oa_form_config",
    "sv": "sv_form_config",
    "sv_oa": "sv_oa_form_config",
}


def _load_form_config(form_type: str = "lv") -> List[Dict[str, Any]]:
    """Loads form config for the given form type."""
    if form_type not in FORM_CONFIG_MODULES:
        form_type = "lv"
    module_name = FORM_CONFIG_MODULES[form_type]
    config_module = import_module(module_name)
    return config_module.get_form_config("ru")

logger = logging.getLogger(__name__)

# Scopes required for the API
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

_client = None

def get_service():
    global _client
    if _client:
        return _client
        
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        logger.error(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
        return None
    
    try:
        credentials = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        _client = gspread.authorize(credentials)
        return _client
    except Exception as e:
        logger.error(f"Failed to authorize Google Sheets: {e}")
        return None

def get_field_label_map(form_type: str = "lv") -> Dict[str, str]:
    """Returns a map of {field_id: field_label} from form_config."""
    mapping = {}
    for item in _load_form_config(form_type):
        if 'id' not in item or 'label' not in item:
            continue
        if item.get('type') == 'odometer_group':
            # Группа декоративная — маппим только подпункты, не сам "Одометр"
            for field in item.get('fields', []):
                if 'id' in field and 'label' in field:
                    mapping[field['id']] = field['label']
        else:
            mapping[item['id']] = item['label']
    return mapping

def append_inspection_data(data: Dict[str, Any], sheet_name: str = 'Ответы на форму (1)') -> bool:
    client = get_service()
    if not client: return False

    try:
        # Открываем таблицу и лист
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        sheet = spreadsheet.worksheet(sheet_name)

        # Читаем заголовки
        header_row = sheet.row_values(1)
        form_type = data.get('form_type', 'lv')
        field_map = get_field_label_map(form_type)
        header_index_map = {title.strip(): i for i, title in enumerate(header_row)}
        
        row_values = [""] * len(header_row)
        
        for field_id, value in data.items():
            label = field_map.get(field_id)
            if label and label.strip() in header_index_map:
                index = header_index_map[label.strip()]
                row_values[index] = str(value)

        # append_row добавляет данные в ПЕРВУЮ абсолютно пустую строку в конце таблицы
        # table_cascade=True помогает избежать конфликтов с форматированными таблицами
        sheet.append_row(
            row_values, 
            value_input_option='USER_ENTERED',
            insert_data_option='INSERT_ROWS' 
        )
        
        logger.info(f"Successfully added row to {sheet_name}")
        return True

    except Exception as e:
        logger.error(f"Error appending data to Google Sheets: {e}")
        return False
