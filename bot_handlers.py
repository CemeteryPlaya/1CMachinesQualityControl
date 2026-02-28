import os
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import WebAppInfo, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import logging
from dotenv import load_dotenv
from translations import BOT_MESSAGES, LANGUAGE_NAMES, get_bot_message

load_dotenv()

# Initialize router
router = Router()

# URL of the Mini App (Flask server)
WEB_APP_URL = os.getenv("WEB_APP_URL")

# FSM states
class InspectionForm(StatesGroup):
    waiting_for_vehicle_type = State()

# Текст для кнопки смены языка на всех языках
CHANGE_LANGUAGE_TEXT = {
    "ru": "🔄 Изменить язык",
    "en": "🔄 Change language",
    "kk": "🔄 Тілді өзгерту",
    "uz": "🔄 Tilni o'zgartirish"
}

# Маппинг типов техники на ключи конфигов
VEHICLE_TYPES = ["lv", "lv_oa", "sv", "sv_oa"]


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """
    Handler for /start command.
    Sends a message with language selection keyboard.
    """
    await state.clear()

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=LANGUAGE_NAMES["ru"]),
                KeyboardButton(text=LANGUAGE_NAMES["en"])
            ],
            [
                KeyboardButton(text=LANGUAGE_NAMES["kk"]),
                KeyboardButton(text=LANGUAGE_NAMES["uz"])
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

    welcome_text = (
        f"🇷🇺 {get_bot_message('welcome', 'ru')}\n\n"
        f"🇬🇧 {get_bot_message('welcome', 'en')}\n\n"
        f"🇰🇿 {get_bot_message('welcome', 'kk')}\n\n"
        f"🇺🇿 {get_bot_message('welcome', 'uz')}"
    )

    await message.answer(welcome_text, reply_markup=kb)


@router.message(F.text.in_([LANGUAGE_NAMES["ru"], LANGUAGE_NAMES["en"], LANGUAGE_NAMES["kk"], LANGUAGE_NAMES["uz"]]))
async def process_language_selection(message: types.Message, state: FSMContext):
    """
    Handler for language selection from keyboard.
    Shows vehicle type selection buttons.
    """
    lang_map = {
        LANGUAGE_NAMES["ru"]: "ru",
        LANGUAGE_NAMES["en"]: "en",
        LANGUAGE_NAMES["kk"]: "kk",
        LANGUAGE_NAMES["uz"]: "uz"
    }

    lang_code = lang_map.get(message.text, "ru")

    # Сохраняем язык в FSM
    await state.set_state(InspectionForm.waiting_for_vehicle_type)
    await state.update_data(lang=lang_code)

    # Показываем кнопки выбора типа техники
    change_lang_text = CHANGE_LANGUAGE_TEXT.get(lang_code, CHANGE_LANGUAGE_TEXT["ru"])

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_bot_message("vehicle_lv", lang_code)),
                KeyboardButton(text=get_bot_message("vehicle_lv_oa", lang_code))
            ],
            [
                KeyboardButton(text=get_bot_message("vehicle_sv", lang_code)),
                KeyboardButton(text=get_bot_message("vehicle_sv_oa", lang_code))
            ],
            [KeyboardButton(text=change_lang_text)]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

    message_text = get_bot_message("language_selected", lang_code)
    await message.answer(message_text, reply_markup=kb)


@router.message(InspectionForm.waiting_for_vehicle_type)
async def process_vehicle_type_selection(message: types.Message, state: FSMContext):
    """
    Handler for vehicle type selection.
    Opens the Mini App with selected language and form type.
    """
    data = await state.get_data()
    lang_code = data.get("lang", "ru")

    # Проверяем, не нажал ли пользователь "Изменить язык"
    change_lang_texts = list(CHANGE_LANGUAGE_TEXT.values())
    if message.text in change_lang_texts:
        await state.clear()
        await cmd_start(message, state)
        return

    # Определяем тип формы по тексту кнопки
    vehicle_type_map = {}
    for lang in ["ru", "en", "kk", "uz"]:
        vehicle_type_map[get_bot_message("vehicle_lv", lang)] = "lv"
        vehicle_type_map[get_bot_message("vehicle_lv_oa", lang)] = "lv_oa"
        vehicle_type_map[get_bot_message("vehicle_sv", lang)] = "sv"
        vehicle_type_map[get_bot_message("vehicle_sv_oa", lang)] = "sv_oa"

    form_type = vehicle_type_map.get(message.text)

    if not form_type:
        # Неизвестная кнопка — повторяем выбор
        message_text = get_bot_message("select_vehicle_type", lang_code)
        await message.answer(message_text)
        return

    # Формируем URL с параметрами языка, типа формы и user_id
    user_id = message.from_user.id
    app_url = f"{WEB_APP_URL}?lang={lang_code}&form_type={form_type}&tg_user_id={user_id}"

    logging.info(f"Opening Mini App for user {user_id} with language {lang_code}, form_type {form_type}")

    # Создаем клавиатуру с кнопкой для открытия Mini App + смена типа + смена языка
    button_text = get_bot_message("fill_form_button", lang_code)
    change_lang_text = CHANGE_LANGUAGE_TEXT.get(lang_code, CHANGE_LANGUAGE_TEXT["ru"])

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=button_text, web_app=WebAppInfo(url=app_url))],
            [KeyboardButton(text=change_lang_text)],
            [KeyboardButton(text=get_bot_message("change_vehicle_type", lang_code))]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

    await state.clear()
    await state.update_data(lang=lang_code)
    await message.answer(get_bot_message("fill_form_button", lang_code), reply_markup=kb)


@router.message(F.text.in_([
    get_bot_message("change_vehicle_type", "ru"),
    get_bot_message("change_vehicle_type", "en"),
    get_bot_message("change_vehicle_type", "kk"),
    get_bot_message("change_vehicle_type", "uz")
]))
async def process_change_vehicle_type(message: types.Message, state: FSMContext):
    """
    Handler for changing vehicle type.
    Returns to vehicle type selection, keeping the language.
    """
    data = await state.get_data()
    lang_code = data.get("lang", "ru")

    await state.set_state(InspectionForm.waiting_for_vehicle_type)
    await state.update_data(lang=lang_code)

    change_lang_text = CHANGE_LANGUAGE_TEXT.get(lang_code, CHANGE_LANGUAGE_TEXT["ru"])

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_bot_message("vehicle_lv", lang_code)),
                KeyboardButton(text=get_bot_message("vehicle_lv_oa", lang_code))
            ],
            [
                KeyboardButton(text=get_bot_message("vehicle_sv", lang_code)),
                KeyboardButton(text=get_bot_message("vehicle_sv_oa", lang_code))
            ],
            [KeyboardButton(text=change_lang_text)]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

    await message.answer(get_bot_message("select_vehicle_type", lang_code), reply_markup=kb)


@router.message(F.text.in_([
    CHANGE_LANGUAGE_TEXT["ru"],
    CHANGE_LANGUAGE_TEXT["en"],
    CHANGE_LANGUAGE_TEXT["kk"],
    CHANGE_LANGUAGE_TEXT["uz"]
]))
async def process_change_language(message: types.Message, state: FSMContext):
    """
    Handler for changing language.
    Returns to language selection.
    """
    await state.clear()
    await cmd_start(message, state)
