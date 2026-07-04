import os
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (WebAppInfo, ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton,
                           ReplyKeyboardRemove)
import logging
from dotenv import load_dotenv
from translations import LANGUAGE_NAMES, get_bot_message
from database import get_admin_by_telegram_id, get_bot_user, upsert_bot_user

load_dotenv()

# Initialize router
router = Router()

# URL of the Mini App (Flask server)
WEB_APP_URL = os.getenv("WEB_APP_URL")

# FSM states
class InspectionForm(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_form_category = State()
    waiting_for_checklist_period = State()
    waiting_for_vehicle_type = State()


def _is_valid_full_name(name: str) -> bool:
    """Минимальная проверка Ф.И.О: 2+ слова из букв (не команда и не текст кнопки)."""
    if not name or name.startswith('/'):
        return False
    name = name.strip()
    if not (5 <= len(name) <= 100):
        return False
    parts = name.split()
    if len(parts) < 2:
        return False
    # Каждое слово — буквы (кириллица/латиница/казахские), допускаются дефис и апостроф.
    # Отсекает эмодзи и тексты кнопок вроде «🔄 Изменить язык».
    return all(p.replace('-', '').replace("'", '').replace('’', '').isalpha()
               for p in parts)


# Текст для кнопки смены языка на всех языках
CHANGE_LANGUAGE_TEXT = {
    "ru": "🔄 Изменить язык",
    "en": "🔄 Change language",
    "kk": "🔄 Тілді өзгерту",
    "uz": "🔄 Tilni o'zgartirish"
}

def _build_category_keyboard(lang_code: str) -> ReplyKeyboardMarkup:
    """Клавиатура выбора категории формы"""
    change_lang_text = CHANGE_LANGUAGE_TEXT.get(lang_code, CHANGE_LANGUAGE_TEXT["ru"])
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_bot_message("category_checklist", lang_code))],
            [KeyboardButton(text=get_bot_message("category_maintenance", lang_code))],
            [KeyboardButton(text=change_lang_text)]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )


def _build_period_keyboard(lang_code: str) -> ReplyKeyboardMarkup:
    """Клавиатура выбора типа чек-листа (ежедневный/еженедельный)"""
    change_lang_text = CHANGE_LANGUAGE_TEXT.get(lang_code, CHANGE_LANGUAGE_TEXT["ru"])
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_bot_message("checklist_daily", lang_code)),
                KeyboardButton(text=get_bot_message("checklist_weekly", lang_code))
            ],
            [KeyboardButton(text=get_bot_message("change_form_category", lang_code))],
            [KeyboardButton(text=change_lang_text)]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )


def _build_vehicle_type_keyboard(lang_code: str) -> ReplyKeyboardMarkup:
    """Клавиатура выбора типа техники (еженедельные чек-листы)"""
    change_lang_text = CHANGE_LANGUAGE_TEXT.get(lang_code, CHANGE_LANGUAGE_TEXT["ru"])
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_bot_message("vehicle_lv", lang_code)),
                KeyboardButton(text=get_bot_message("vehicle_lv_oa", lang_code))
            ],
            [
                KeyboardButton(text=get_bot_message("vehicle_sv", lang_code)),
                KeyboardButton(text=get_bot_message("vehicle_sv_oa", lang_code))
            ],
            [KeyboardButton(text=get_bot_message("change_checklist_period", lang_code))],
            [KeyboardButton(text=get_bot_message("change_form_category", lang_code))],
            [KeyboardButton(text=change_lang_text)]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )


@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    """
    Вход в админ-панель (Mini App). Доступ только тем, чей Telegram ID
    есть среди активных администраторов.
    """
    user_id = message.from_user.id
    admin = get_admin_by_telegram_id(str(user_id))

    if not admin:
        logging.info(f"Admin panel access denied for telegram id {user_id}")
        await message.answer("⛔ У вас нет доступа к админ-панели.")
        return

    admin_url = f"{WEB_APP_URL.rstrip('/')}/admin/login"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛠 Открыть админ-панель", web_app=WebAppInfo(url=admin_url))]
    ])
    await message.answer(
        f"Здравствуйте, {admin.get('full_name') or admin['username']}!\n"
        "Нажмите кнопку, чтобы открыть админ-панель:",
        reply_markup=kb
    )


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
    Shows form category selection (Чек-листы / Отчет о ТО).
    """
    lang_map = {
        LANGUAGE_NAMES["ru"]: "ru",
        LANGUAGE_NAMES["en"]: "en",
        LANGUAGE_NAMES["kk"]: "kk",
        LANGUAGE_NAMES["uz"]: "uz"
    }

    lang_code = lang_map.get(message.text, "ru")

    # Регистрация: если пользователя нет в БД — сначала запрашиваем Ф.И.О
    if not get_bot_user(str(message.from_user.id)):
        await state.set_state(InspectionForm.waiting_for_full_name)
        await state.update_data(lang=lang_code)
        await message.answer(get_bot_message("enter_full_name", lang_code),
                             reply_markup=ReplyKeyboardRemove())
        return

    # Сохраняем язык в FSM и переходим к выбору категории
    await state.set_state(InspectionForm.waiting_for_form_category)
    await state.update_data(lang=lang_code)

    kb = _build_category_keyboard(lang_code)
    message_text = get_bot_message("select_form_category", lang_code)
    await message.answer(message_text, reply_markup=kb)


@router.message(InspectionForm.waiting_for_full_name)
async def process_full_name(message: types.Message, state: FSMContext):
    """
    Регистрация пользователя: сохраняем Ф.И.О в bot_users.
    Оно будет фиксироваться как «Отправитель» во всех отчётах.
    """
    data = await state.get_data()
    lang_code = data.get("lang", "ru")

    full_name = (message.text or '').strip()
    if not _is_valid_full_name(full_name):
        await message.answer(get_bot_message("full_name_invalid", lang_code))
        return

    upsert_bot_user(str(message.from_user.id), full_name)
    logging.info(f"Bot user registered: id={message.from_user.id}, name={full_name}")

    await message.answer(get_bot_message("full_name_saved", lang_code).format(name=full_name))

    # Продолжаем обычный поток: выбор категории формы
    await state.set_state(InspectionForm.waiting_for_form_category)
    await state.update_data(lang=lang_code)
    kb = _build_category_keyboard(lang_code)
    await message.answer(get_bot_message("select_form_category", lang_code), reply_markup=kb)


@router.message(InspectionForm.waiting_for_form_category)
async def process_form_category_selection(message: types.Message, state: FSMContext):
    """
    Handler for form category selection.
    Чек-листы → выбор типа техники.
    Отчет о ТО → сразу Mini App.
    """
    data = await state.get_data()
    lang_code = data.get("lang", "ru")

    # Проверяем, не нажал ли пользователь "Изменить язык"
    change_lang_texts = list(CHANGE_LANGUAGE_TEXT.values())
    if message.text in change_lang_texts:
        await state.clear()
        await cmd_start(message, state)
        return

    # Определяем категорию
    category_checklist_map = {}
    category_maintenance_map = {}
    for lang in ["ru", "en", "kk", "uz"]:
        category_checklist_map[get_bot_message("category_checklist", lang)] = True
        category_maintenance_map[get_bot_message("category_maintenance", lang)] = True

    if message.text in category_checklist_map:
        # Чек-листы → показываем выбор типа чек-листа (ежедневный/еженедельный)
        await state.set_state(InspectionForm.waiting_for_checklist_period)
        await state.update_data(lang=lang_code)

        kb = _build_period_keyboard(lang_code)
        message_text = get_bot_message("select_checklist_period", lang_code)
        await message.answer(message_text, reply_markup=kb)

    elif message.text in category_maintenance_map:
        # Отчет о ТО → сразу открываем Mini App
        user_id = message.from_user.id
        app_url = f"{WEB_APP_URL}?lang={lang_code}&form_type=to&tg_user_id={user_id}"

        logging.info(f"Opening TO Mini App for user {user_id} with language {lang_code}")

        button_text = get_bot_message("fill_to_form_button", lang_code)
        change_lang_text = CHANGE_LANGUAGE_TEXT.get(lang_code, CHANGE_LANGUAGE_TEXT["ru"])

        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=button_text, web_app=WebAppInfo(url=app_url))],
                [KeyboardButton(text=get_bot_message("change_form_category", lang_code))],
                [KeyboardButton(text=change_lang_text)]
            ],
            resize_keyboard=True,
            one_time_keyboard=False
        )

        await state.clear()
        await state.update_data(lang=lang_code)
        await message.answer(button_text, reply_markup=kb)

    else:
        # Неизвестная кнопка — повторяем выбор категории
        message_text = get_bot_message("select_form_category", lang_code)
        await message.answer(message_text)


@router.message(InspectionForm.waiting_for_checklist_period)
async def process_checklist_period_selection(message: types.Message, state: FSMContext):
    """
    Handler for checklist period selection (Ежедневный / Еженедельный).
    Еженедельный → выбор типа техники (4 кнопки).
    Ежедневный → сразу одна форма (Mini App, form_type=daily).
    """
    data = await state.get_data()
    lang_code = data.get("lang", "ru")

    # Смена языка
    if message.text in list(CHANGE_LANGUAGE_TEXT.values()):
        await state.clear()
        await cmd_start(message, state)
        return

    # Назад к выбору категории
    change_category_texts = [get_bot_message("change_form_category", lang)
                             for lang in ["ru", "en", "kk", "uz"]]
    if message.text in change_category_texts:
        await state.set_state(InspectionForm.waiting_for_form_category)
        await state.update_data(lang=lang_code)
        kb = _build_category_keyboard(lang_code)
        await message.answer(get_bot_message("select_form_category", lang_code), reply_markup=kb)
        return

    weekly_texts = [get_bot_message("checklist_weekly", lang) for lang in ["ru", "en", "kk", "uz"]]
    daily_texts = [get_bot_message("checklist_daily", lang) for lang in ["ru", "en", "kk", "uz"]]

    if message.text in weekly_texts:
        # Еженедельный → существующий выбор типа техники
        await state.set_state(InspectionForm.waiting_for_vehicle_type)
        await state.update_data(lang=lang_code)
        kb = _build_vehicle_type_keyboard(lang_code)
        await message.answer(get_bot_message("select_vehicle_type", lang_code), reply_markup=kb)

    elif message.text in daily_texts:
        # Ежедневный → сразу открываем Mini App с form_type=daily
        user_id = message.from_user.id
        app_url = f"{WEB_APP_URL}?lang={lang_code}&form_type=daily&tg_user_id={user_id}"

        logging.info(f"Opening daily Mini App for user {user_id} with language {lang_code}")

        button_text = get_bot_message("fill_daily_form_button", lang_code)
        change_lang_text = CHANGE_LANGUAGE_TEXT.get(lang_code, CHANGE_LANGUAGE_TEXT["ru"])

        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=button_text, web_app=WebAppInfo(url=app_url))],
                [KeyboardButton(text=get_bot_message("change_checklist_period", lang_code))],
                [KeyboardButton(text=get_bot_message("change_form_category", lang_code))],
                [KeyboardButton(text=change_lang_text)]
            ],
            resize_keyboard=True,
            one_time_keyboard=False
        )

        await state.clear()
        await state.update_data(lang=lang_code)
        await message.answer(button_text, reply_markup=kb)

    else:
        # Неизвестная кнопка — повторяем выбор
        await message.answer(get_bot_message("select_checklist_period", lang_code))


@router.message(InspectionForm.waiting_for_vehicle_type)
async def process_vehicle_type_selection(message: types.Message, state: FSMContext):
    """
    Handler for vehicle type selection (checklist forms only).
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

    # Проверяем, не нажал ли пользователь "Выбрать другую категорию"
    change_category_texts = [get_bot_message("change_form_category", lang)
                             for lang in ["ru", "en", "kk", "uz"]]
    if message.text in change_category_texts:
        await state.set_state(InspectionForm.waiting_for_form_category)
        await state.update_data(lang=lang_code)
        kb = _build_category_keyboard(lang_code)
        message_text = get_bot_message("select_form_category", lang_code)
        await message.answer(message_text, reply_markup=kb)
        return

    # Проверяем, не нажал ли пользователь "Выбрать тип чек-листа"
    change_period_texts = [get_bot_message("change_checklist_period", lang)
                           for lang in ["ru", "en", "kk", "uz"]]
    if message.text in change_period_texts:
        await state.set_state(InspectionForm.waiting_for_checklist_period)
        await state.update_data(lang=lang_code)
        kb = _build_period_keyboard(lang_code)
        await message.answer(get_bot_message("select_checklist_period", lang_code), reply_markup=kb)
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

    # Создаем клавиатуру с кнопкой для открытия Mini App + смена категории + смена языка
    button_text = get_bot_message("fill_form_button", lang_code)
    change_lang_text = CHANGE_LANGUAGE_TEXT.get(lang_code, CHANGE_LANGUAGE_TEXT["ru"])

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=button_text, web_app=WebAppInfo(url=app_url))],
            [KeyboardButton(text=get_bot_message("change_vehicle_type", lang_code))],
            [KeyboardButton(text=get_bot_message("change_form_category", lang_code))],
            [KeyboardButton(text=change_lang_text)]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

    await state.clear()
    await state.update_data(lang=lang_code)
    await message.answer(button_text, reply_markup=kb)


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

    kb = _build_vehicle_type_keyboard(lang_code)
    await message.answer(get_bot_message("select_vehicle_type", lang_code), reply_markup=kb)


@router.message(F.text.in_([
    get_bot_message("change_checklist_period", "ru"),
    get_bot_message("change_checklist_period", "en"),
    get_bot_message("change_checklist_period", "kk"),
    get_bot_message("change_checklist_period", "uz")
]))
async def process_change_checklist_period(message: types.Message, state: FSMContext):
    """
    Handler for changing checklist period (daily/weekly).
    Returns to period selection, keeping the language.
    """
    data = await state.get_data()
    lang_code = data.get("lang", "ru")

    await state.set_state(InspectionForm.waiting_for_checklist_period)
    await state.update_data(lang=lang_code)

    kb = _build_period_keyboard(lang_code)
    await message.answer(get_bot_message("select_checklist_period", lang_code), reply_markup=kb)


@router.message(F.text.in_([
    get_bot_message("change_form_category", "ru"),
    get_bot_message("change_form_category", "en"),
    get_bot_message("change_form_category", "kk"),
    get_bot_message("change_form_category", "uz")
]))
async def process_change_form_category(message: types.Message, state: FSMContext):
    """
    Handler for changing form category.
    Returns to category selection, keeping the language.
    """
    data = await state.get_data()
    lang_code = data.get("lang", "ru")

    await state.set_state(InspectionForm.waiting_for_form_category)
    await state.update_data(lang=lang_code)

    kb = _build_category_keyboard(lang_code)
    await message.answer(get_bot_message("select_form_category", lang_code), reply_markup=kb)


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


@router.message()
async def process_unmatched(message: types.Message, state: FSMContext):
    """
    Catch-all: сообщение не подошло ни одному хэндлеру (например, состояние
    потеряно после рестарта бота — FSM в памяти). Возвращаем пользователя
    к началу вместо молчания.
    """
    current_state = await state.get_state()
    if current_state is None:
        logging.info(f"Unmatched message from {message.from_user.id}, restarting flow")
        await cmd_start(message, state)
