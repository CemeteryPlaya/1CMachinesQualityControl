# -*- coding: utf-8 -*-
"""
Translations for the Machine Quality Control application
Supported languages: Russian (ru), English (en), Kazakh (kk), Uzbek (uz)
"""

# Базовые переводы для бота
BOT_MESSAGES = {
    "ru": {
        "welcome": "Здравствуйте! Выберите язык для заполнения формы инспекции спецтехники:",
        "language_selected": "Язык выбран: Русский\n\nНажмите кнопку ниже, чтобы открыть форму:",
        "fill_form_button": "📝 Заполнить чек-лист",
        "submission_confirmed": "✅ Чек-лист отправлен.\nДата и время отправки: {datetime}"
    },
    "en": {
        "welcome": "Hello! Select a language to fill out the equipment inspection form:",
        "language_selected": "Language selected: English\n\nClick the button below to open the form:",
        "fill_form_button": "📝 Fill out checklist",
        "submission_confirmed": "✅ Checklist submitted.\nSubmission date and time: {datetime}"
    },
    "kk": {
        "welcome": "Сәлеметсіз бе! Техника тексеру нысанын толтыру үшін тілді таңдаңыз:",
        "language_selected": "Тіл таңдалды: Қазақша\n\nНысанды ашу үшін төмендегі батырманы басыңыз:",
        "fill_form_button": "📝 Тексеру тізімін толтыру",
        "submission_confirmed": "✅ Тексеру тізімі жіберілді.\nЖіберу күні мен уақыты: {datetime}"
    },
    "uz": {
        "welcome": "Assalomu aleykum! Texnika tekshirish formasini to'ldirish uchun tilni tanlang:",
        "language_selected": "Til tanlandi: O'zbekcha\n\nFormani ochish uchun quyidagi tugmani bosing:",
        "fill_form_button": "📝 Tekshiruv ro'yxatini to'ldirish",
        "submission_confirmed": "✅ Tekshiruv ro'yxati yuborildi.\nYuborish sanasi va vaqti: {datetime}"
    }
}

# Названия языков
LANGUAGE_NAMES = {
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
    "kk": "🇰🇿 Қазақша",
    "uz": "🇺🇿 O'zbekcha"
}

# Переводы для элементов формы
FORM_TRANSLATIONS = {
    "ru": {
        "title": "Чек-лист инспекции спецтехники",
        "subtitle": "Пожалуйста, заполните форму внимательно.",
        "submit_button": "ОТПРАВИТЬ",
        "field_required": "Это поле обязательно",
        "search_machine": "Поиск машины...",
        "search_driver": "Поиск водителя...",
        "search_mechanic": "Поиск механика...",
        "select_machine_error": "Выберите машину из списка",
        "select_driver_error": "Выберите водителя из списка",
        "select_mechanic_error": "Выберите механика из списка",
        "my_answer": "Мой ответ",
        "loading_machines_error": "Не удалось загрузить список машин",
        "loading_drivers_error": "Не удалось загрузить список водителей",
        "loading_mechanics_error": "Не удалось загрузить список механиков",
        "submission_error": "Ошибка при отправке",
        "network_error": "Ошибка сети. Попробуйте еще раз."
    },
    "en": {
        "title": "Equipment Inspection Checklist",
        "subtitle": "Please fill out the form carefully.",
        "submit_button": "SUBMIT",
        "field_required": "This field is required",
        "search_machine": "Search machine...",
        "search_driver": "Search driver...",
        "search_mechanic": "Search mechanic...",
        "select_machine_error": "Select a machine from the list",
        "select_driver_error": "Select a driver from the list",
        "select_mechanic_error": "Select a mechanic from the list",
        "my_answer": "My answer",
        "loading_machines_error": "Failed to load machines list",
        "loading_drivers_error": "Failed to load drivers list",
        "loading_mechanics_error": "Failed to load mechanics list",
        "submission_error": "Submission error",
        "network_error": "Network error. Please try again."
    },
    "kk": {
        "title": "Техниканы тексеру тізімі",
        "subtitle": "Нысанды мұқият толтырыңыз.",
        "submit_button": "ЖІБЕРУ",
        "field_required": "Бұл өріс міндетті",
        "search_machine": "Машинаны іздеу...",
        "search_driver": "Жүргізушіні іздеу...",
        "search_mechanic": "Механикті іздеу...",
        "select_machine_error": "Тізімнен машинаны таңдаңыз",
        "select_driver_error": "Тізімнен жүргізушіні таңдаңыз",
        "select_mechanic_error": "Тізімнен механикті таңдаңыз",
        "my_answer": "Менің жауабым",
        "loading_machines_error": "Машиналар тізімін жүктеу мүмкін болмады",
        "loading_drivers_error": "Жүргізушілер тізімін жүктеу мүмкін болмады",
        "loading_mechanics_error": "Механиктер тізімін жүктеу мүмкін болмады",
        "submission_error": "Жіберу қатесі",
        "network_error": "Желі қатесі. Қайталап көріңіз."
    },
    "uz": {
        "title": "Texnika tekshiruv ro'yxati",
        "subtitle": "Iltimos, formani ehtiyotkorlik bilan to'ldiring.",
        "submit_button": "YUBORISH",
        "field_required": "Bu maydon majburiy",
        "search_machine": "Mashinani qidirish...",
        "search_driver": "Haydovchini qidirish...",
        "search_mechanic": "Mexanikni qidirish...",
        "select_machine_error": "Ro'yxatdan mashinani tanlang",
        "select_driver_error": "Ro'yxatdan haydovchini tanlang",
        "select_mechanic_error": "Ro'yxatdan mexanikni tanlang",
        "my_answer": "Mening javobim",
        "loading_machines_error": "Mashinalar ro'yxatini yuklash muvaffaqiyatsiz tugadi",
        "loading_drivers_error": "Haydovchilar ro'yxatini yuklash muvaffaqiyatsiz tugadi",
        "loading_mechanics_error": "Mexaniklar ro'yxatini yuklash muvaffaqiyatsiz tugadi",
        "submission_error": "Yuborish xatosi",
        "network_error": "Tarmoq xatosi. Iltimos, qayta urinib ko'ring."
    }
}

# Переводы полей формы
FIELD_LABELS = {
    "timestamp": {
        "ru": "Отметка времени",
        "en": "Timestamp",
        "kk": "Уақыт белгісі",
        "uz": "Vaqt belgisi"
    },
    "inspection_date": {
        "ru": "Дата инспекции",
        "en": "Inspection date",
        "kk": "Тексеру күні",
        "uz": "Tekshiruv sanasi"
    },
    "driver_uid": {
        "ru": "Водитель",
        "en": "Driver",
        "kk": "Жүргізуші",
        "uz": "Haydovchi"
    },
    "mechanic_uid": {
        "ru": "Механик",
        "en": "Mechanic",
        "kk": "Механик",
        "uz": "Mexanik"
    },
    "machine_uid": {
        "ru": "Машина",
        "en": "Machine",
        "kk": "Машина",
        "uz": "Mashina"
    },
    "motorhours": {
        "ru": "Моточасы",
        "en": "Engine hours",
        "kk": "Мотосағаттар",
        "uz": "Motor soatlari"
    },
    "mileage": {
        "ru": "Километраж",
        "en": "Mileage",
        "kk": "Жүгірген жол",
        "uz": "Kilometraj"
    }
}

# Переводы для заголовков секций
SECTION_HEADERS = {
    "section_1": {
        "ru": "Общая информация",
        "en": "General Information",
        "kk": "Жалпы ақпарат",
        "uz": "Umumiy ma'lumot"
    },
    "section_2": {
        "ru": "Показания на момент инспекции",
        "en": "Readings at inspection",
        "kk": "Тексеру кезіндегі көрсеткіштер",
        "uz": "Tekshiruv vaqtidagi ko'rsatkichlar"
    },
    "section_3": {
        "ru": "Кузов",
        "en": "Body",
        "kk": "Кузов",
        "uz": "Kuzov"
    },
    "section_4": {
        "ru": "Гидравлическая система",
        "en": "Hydraulic System",
        "kk": "Гидравликалық жүйе",
        "uz": "Gidravlik tizim"
    },
    "section_5": {
        "ru": "Вспомогательное оборудование",
        "en": "Auxiliary Equipment",
        "kk": "Көмекші жабдық",
        "uz": "Yordamchi uskunalar"
    },
    "section_6": {
        "ru": "Отсек двигателя",
        "en": "Engine Compartment",
        "kk": "Қозғалтқыш бөлімі",
        "uz": "Dvigatel bo'limi"
    },
    "section_7": {
        "ru": "Ходовая часть",
        "en": "Undercarriage",
        "kk": "Жүріс бөлігі",
        "uz": "Harakat qismi"
    },
    "section_8": {
        "ru": "Оснащение и инструменты",
        "en": "Equipment and Tools",
        "kk": "Жабдықтау және құралдар",
        "uz": "Jihozlar va asboblar"
    },
    "section_9": {
        "ru": "Прочие элементы",
        "en": "Other Elements",
        "kk": "Басқа элементтер",
        "uz": "Boshqa elementlar"
    },
    "section_10": {
        "ru": "Документация",
        "en": "Documentation",
        "kk": "Құжаттама",
        "uz": "Hujjatlar"
    }
}

# Переводы для вариантов ответов
OPTION_TRANSLATIONS = {
    "Нормальное": {
        "ru": "Нормальное",
        "en": "Normal",
        "kk": "Қалыпты",
        "uz": "Normal"
    },
    "Не нормальное": {
        "ru": "Не нормальное",
        "en": "Not normal",
        "kk": "Қалыпсыз",
        "uz": "Normal emas"
    },
    "Без ответа": {
        "ru": "Без ответа",
        "en": "No answer",
        "kk": "Жауапсыз",
        "uz": "Javobsiz"
    },
    "Отсутствует": {
        "ru": "Отсутствует",
        "en": "Absent",
        "kk": "Жоқ",
        "uz": "Yo'q"
    },
    "Имеется": {
        "ru": "Имеется",
        "en": "Present",
        "kk": "Бар",
        "uz": "Bor"
    }
}


def get_translation(translations_dict: dict, key: str, lang: str = "ru") -> str:
    """
    Получает перевод для заданного ключа и языка

    Args:
        translations_dict: Словарь с переводами
        key: Ключ для поиска перевода
        lang: Код языка (ru, en, kk, uz)

    Returns:
        Переведенная строка или оригинальный ключ если перевод не найден
    """
    if key in translations_dict:
        return translations_dict[key].get(lang, translations_dict[key].get("ru", key))
    return key


def get_bot_message(key: str, lang: str = "ru") -> str:
    """Получает сообщение бота на нужном языке"""
    return BOT_MESSAGES.get(lang, BOT_MESSAGES["ru"]).get(key, key)


def get_form_translation(key: str, lang: str = "ru") -> str:
    """Получает перевод элемента формы на нужном языке"""
    return FORM_TRANSLATIONS.get(lang, FORM_TRANSLATIONS["ru"]).get(key, key)
