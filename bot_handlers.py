import os
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import logging
from dotenv import load_dotenv
from translations import BOT_MESSAGES, LANGUAGE_NAMES, get_bot_message

load_dotenv()

# Initialize router
router = Router()

# URL of the Mini App (Flask server)
WEB_APP_URL = os.getenv("WEB_APP_URL")

# Текст для кнопки смены языка на всех языках
CHANGE_LANGUAGE_TEXT = {
    "ru": "🔄 Изменить язык",
    "en": "🔄 Change language",
    "kk": "🔄 Тілді өзгерту",
    "uz": "🔄 Tilni o'zgartirish"
}

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """
    Handler for /start command.
    Sends a message with language selection keyboard.
    """
    # Создаем обычную клавиатуру (Reply Keyboard) 2x2 для выбора языка + кнопка /start
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

    # Отправляем сообщение на всех языках
    welcome_text = (
        f"🇷🇺 {get_bot_message('welcome', 'ru')}\n\n"
        f"🇬🇧 {get_bot_message('welcome', 'en')}\n\n"
        f"🇰🇿 {get_bot_message('welcome', 'kk')}\n\n"
        f"🇺🇿 {get_bot_message('welcome', 'uz')}"
    )

    await message.answer(welcome_text, reply_markup=kb)


@router.message(F.text.in_([LANGUAGE_NAMES["ru"], LANGUAGE_NAMES["en"], LANGUAGE_NAMES["kk"], LANGUAGE_NAMES["uz"]]))
async def process_language_selection(message: types.Message):
    """
    Handler for language selection from keyboard.
    Opens the Mini App with selected language.
    """
    # Определяем код языка по тексту кнопки
    lang_map = {
        LANGUAGE_NAMES["ru"]: "ru",
        LANGUAGE_NAMES["en"]: "en",
        LANGUAGE_NAMES["kk"]: "kk",
        LANGUAGE_NAMES["uz"]: "uz"
    }

    lang_code = lang_map.get(message.text, "ru")

    # Формируем URL с параметром языка
    app_url = f"{WEB_APP_URL}?lang={lang_code}"

    # Создаем клавиатуру с кнопкой для открытия Mini App + кнопка смены языка
    button_text = get_bot_message("fill_form_button", lang_code)
    change_lang_text = CHANGE_LANGUAGE_TEXT.get(lang_code, CHANGE_LANGUAGE_TEXT["ru"])

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=button_text, web_app=WebAppInfo(url=app_url))],
            [KeyboardButton(text=change_lang_text)]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

    # Отправляем сообщение на выбранном языке
    message_text = get_bot_message("language_selected", lang_code)

    await message.answer(message_text, reply_markup=kb)


@router.message(F.text.in_([
    CHANGE_LANGUAGE_TEXT["ru"],
    CHANGE_LANGUAGE_TEXT["en"],
    CHANGE_LANGUAGE_TEXT["kk"],
    CHANGE_LANGUAGE_TEXT["uz"]
]))
async def process_change_language(message: types.Message):
    """
    Handler for changing language.
    Returns to language selection.
    """
    # Возвращаем к выбору языка
    await cmd_start(message)
