# -*- coding: utf-8 -*-
"""
Translations for the Machine Quality Control application
Supported languages: Russian (ru), English (en), Kazakh (kk), Uzbek (uz)
"""

# Базовые переводы для бота
BOT_MESSAGES = {
    "ru": {
        "welcome": "Здравствуйте! Выберите язык для заполнения формы инспекции спецтехники:",
        "language_selected": "Язык выбран: Русский\n\nВыберите тип техники и вид работы:",
        "select_vehicle_type": "Выберите тип техники и вид работы:",
        "fill_form_button": "📝 Заполнить чек-лист",
        "submission_confirmed": "✅ Чек-лист отправлен.\nДата и время отправки: {datetime}",
        "other_placeholder": "Укажите свой вариант",
        "vehicle_lv": "🚗 Легковые — на территории",
        "vehicle_lv_oa": "🚗 Легковые — выезд",
        "vehicle_sv": "🚜 Спецтехника — на территории",
        "vehicle_sv_oa": "🚜 Спецтехника — выезд",
        "change_vehicle_type": "🔀 Выбрать другой тип техники",
        "select_form_category": "Выберите категорию формы:",
        "category_checklist": "📋 Чек-листы",
        "category_maintenance": "🔧 Отчет о проведенном ТО",
        "change_form_category": "🔀 Выбрать другую категорию",
        "fill_to_form_button": "📝 Заполнить отчет о ТО",
        "to_submission_confirmed": "✅ Отчет о ТО отправлен.\nДата и время отправки: {datetime}"
    },
    "en": {
        "welcome": "Hello! Select a language to fill out the equipment inspection form:",
        "language_selected": "Language selected: English\n\nSelect vehicle type and work location:",
        "select_vehicle_type": "Select vehicle type and work location:",
        "fill_form_button": "📝 Fill out checklist",
        "submission_confirmed": "✅ Checklist submitted.\nSubmission date and time: {datetime}",
        "other_placeholder": "Specify your option",
        "vehicle_lv": "🚗 Passenger — on-site",
        "vehicle_lv_oa": "🚗 Passenger — off-site",
        "vehicle_sv": "🚜 Special equipment — on-site",
        "vehicle_sv_oa": "🚜 Special equipment — off-site",
        "change_vehicle_type": "🔀 Select different vehicle type",
        "select_form_category": "Select form category:",
        "category_checklist": "📋 Checklists",
        "category_maintenance": "🔧 Maintenance Report",
        "change_form_category": "🔀 Select different category",
        "fill_to_form_button": "📝 Fill maintenance report",
        "to_submission_confirmed": "✅ Maintenance report submitted.\nSubmission date and time: {datetime}"
    },
    "kk": {
        "welcome": "Сәлеметсіз бе! Техника тексеру нысанын толтыру үшін тілді таңдаңыз:",
        "language_selected": "Тіл таңдалды: Қазақша\n\nТехника түрін және жұмыс түрін таңдаңыз:",
        "select_vehicle_type": "Техника түрін және жұмыс түрін таңдаңыз:",
        "fill_form_button": "📝 Тексеру тізімін толтыру",
        "submission_confirmed": "✅ Тексеру тізімі жіберілді.\nЖіберу күні мен уақыты: {datetime}",
        "other_placeholder": "Өз нұсқаңызды көрсетіңіз",
        "vehicle_lv": "🚗 Жеңіл көлік — аумақта",
        "vehicle_lv_oa": "🚗 Жеңіл көлік — шығу",
        "vehicle_sv": "🚜 Арнайы техника — аумақта",
        "vehicle_sv_oa": "🚜 Арнайы техника — шығу",
        "change_vehicle_type": "🔀 Басқа техника түрін таңдау",
        "select_form_category": "Форма санатын таңдаңыз:",
        "category_checklist": "📋 Тексеру тізімдері",
        "category_maintenance": "🔧 ТҚ есебі",
        "change_form_category": "🔀 Басқа санатты таңдау",
        "fill_to_form_button": "📝 ТҚ есебін толтыру",
        "to_submission_confirmed": "✅ ТҚ есебі жіберілді.\nЖіберу күні мен уақыты: {datetime}"
    },
    "uz": {
        "welcome": "Assalomu aleykum! Texnika tekshirish formasini to'ldirish uchun tilni tanlang:",
        "language_selected": "Til tanlandi: O'zbekcha\n\nTexnika turini va ish joyini tanlang:",
        "select_vehicle_type": "Texnika turini va ish joyini tanlang:",
        "fill_form_button": "📝 Tekshiruv ro'yxatini to'ldirish",
        "submission_confirmed": "✅ Tekshiruv ro'yxati yuborildi.\nYuborish sanasi va vaqti: {datetime}",
        "other_placeholder": "Oz variantingizni kiriting",
        "vehicle_lv": "🚗 Yengil avtomobil — hududda",
        "vehicle_lv_oa": "🚗 Yengil avtomobil — tashqarida",
        "vehicle_sv": "🚜 Maxsus texnika — hududda",
        "vehicle_sv_oa": "🚜 Maxsus texnika — tashqarida",
        "change_vehicle_type": "🔀 Boshqa texnika turini tanlash",
        "select_form_category": "Forma toifasini tanlang:",
        "category_checklist": "📋 Tekshiruv ro'yxatlari",
        "category_maintenance": "🔧 TO hisoboti",
        "change_form_category": "🔀 Boshqa toifani tanlash",
        "fill_to_form_button": "📝 TO hisobotini to'ldirish",
        "to_submission_confirmed": "✅ TO hisoboti yuborildi.\nYuborish sanasi va vaqti: {datetime}"
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
    "department_uid": {
        "ru": "Подразделение",
        "en": "Department",
        "kk": "Бөлім",
        "uz": "Bo'lim"
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
    "motorhours_hint": {
        "ru": "(если легковое — писать 0)",
        "en": "(if passenger car — write 0)",
        "kk": "(жеңіл автомобиль болса — 0 жазу)",
        "uz": "(agar yengil avtomobil bo'lsa — 0 yozing)"
    },
    "mileage": {
        "ru": "Километраж",
        "en": "Mileage",
        "kk": "Жүгірген жол",
        "uz": "Kilometraj"
    },
    "mileage_hint": {
        "ru": "(если спецтехника — писать 0)",
        "en": "(if special machinery — write 0)",
        "kk": "(арнайы техника болса — 0 жазу)",
        "uz": "(agar maxsus texnika bo'lsa — 0 yozing)"
    },
    "responsible_person": {
        "ru": "Ответственное лицо",
        "en": "Responsible person",
        "kk": "Жауапты тұлға",
        "uz": "Mas'ul shaxs"
    },
    "repair_type": {
        "ru": "Вид ремонта",
        "en": "Repair type",
        "kk": "Жөндеу түрі",
        "uz": "Ta'mirlash turi"
    },
    "breakdown_reason": {
        "ru": "Причина поломки техники",
        "en": "Breakdown reason",
        "kk": "Техниканың бұзылу себебі",
        "uz": "Buzilish sababi"
    },
    "repair_start_date": {
        "ru": "Дата начала ремонта",
        "en": "Repair start date",
        "kk": "Жөндеудің басталу күні",
        "uz": "Ta'mirlash boshlanish sanasi"
    },
    "repair_end_date": {
        "ru": "Дата окончания ремонта",
        "en": "Repair end date",
        "kk": "Жөндеудің аяқталу күні",
        "uz": "Ta'mirlash tugash sanasi"
    },
    "downtime_days": {
        "ru": "Время простоя (дней)",
        "en": "Downtime (days)",
        "kk": "Тоқтап тұру уақыты (күн)",
        "uz": "To'xtash vaqti (kunlar)"
    },
    "downtime_hours": {
        "ru": "Время простоя (часов)",
        "en": "Downtime (hours)",
        "kk": "Тоқтап тұру уақыты (сағат)",
        "uz": "To'xtash vaqti (soatlar)"
    },
    "used_parts": {
        "ru": "Использованные запчасти",
        "en": "Used parts",
        "kk": "Қолданылған бөлшектер",
        "uz": "Ishlatilgan ehtiyot qismlar"
    },
    "to_date": {
        "ru": "Дата проведения ТО",
        "en": "Maintenance date",
        "kk": "ТҚ жүргізу күні",
        "uz": "TO sanasi"
    },
    "last_mileage": {
        "ru": "Последний введенный пробег",
        "en": "Last recorded mileage",
        "kk": "Соңғы енгізілген жүгіріс",
        "uz": "Oxirgi kiritilgan yurish"
    },
    "to_mileage": {
        "ru": "Текущий пробег (км)",
        "en": "Current mileage (km)",
        "kk": "Ағымдағы жүгіріс (км)",
        "uz": "Joriy yurish (km)"
    },
    "to_motorhours": {
        "ru": "Текущие моточасы",
        "en": "Current engine hours",
        "kk": "Ағымдағы мотосағаттар",
        "uz": "Joriy motor soatlari"
    },
    "nomenclature": {
        "ru": "Номенклатура",
        "en": "Item",
        "kk": "Номенклатура",
        "uz": "Nomenklatura"
    },
    "quantity": {
        "ru": "Кол-во",
        "en": "Qty",
        "kk": "Саны",
        "uz": "Soni"
    },
    "unit": {
        "ru": "Ед. изм.",
        "en": "Unit",
        "kk": "Өлш. бір.",
        "uz": "Birlik"
    },
    "cost": {
        "ru": "Стоимость",
        "en": "Cost",
        "kk": "Құны",
        "uz": "Narxi"
    },
    "work_type": {
        "ru": "Вид работ",
        "en": "Work type",
        "kk": "Жұмыс түрі",
        "uz": "Ish turi"
    },
    "performer": {
        "ru": "Исполнитель",
        "en": "Performer",
        "kk": "Орындаушы",
        "uz": "Ijrochi"
    },
    "duration": {
        "ru": "Время выполнения",
        "en": "Duration",
        "kk": "Орындау уақыты",
        "uz": "Bajarish vaqti"
    },
    "note": {
        "ru": "Примечание",
        "en": "Note",
        "kk": "Ескертпе",
        "uz": "Izoh"
    },
    "add_row": {
        "ru": "Добавить строку",
        "en": "Add row",
        "kk": "Жол қосу",
        "uz": "Qator qo'shish"
    },
    "comments": {
        "ru": "Комментарии",
        "en": "Comments",
        "kk": "Түсініктемелер",
        "uz": "Izohlar"
    },
    "inspection_result": {
        "ru": "Результат проверки",
        "en": "Inspection result",
        "kk": "Тексеру нәтижесі",
        "uz": "Tekshiruv natijasi"
    },
    "capacity_of_fuel_in_fueltank": {
        "ru": "Объем топлива в баке на момент проверки",
        "en": "Fuel capacity in fuel tank at the time of inspection",
        "kk": "Жанармай қоймасындағы жанармай көлемі тексеру кезінде",
        "uz": "Yoqilg'i xotirasida yoqilg'i hajmi tekshiruv vaqtida"
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
    },
    "to_section_general": {
        "ru": "Общая информация",
        "en": "General Information",
        "kk": "Жалпы ақпарат",
        "uz": "Umumiy ma'lumot"
    },
    "to_section_repair": {
        "ru": "Информация о ремонте",
        "en": "Repair Information",
        "kk": "Жөндеу туралы ақпарат",
        "uz": "Ta'mirlash haqida ma'lumot"
    },
    "to_section_downtime": {
        "ru": "Простой",
        "en": "Downtime",
        "kk": "Тоқтап тұру",
        "uz": "To'xtash"
    },
    "to_section_materials": {
        "ru": "Использованные материалы",
        "en": "Used Materials",
        "kk": "Қолданылған материалдар",
        "uz": "Ishlatilgan materiallar"
    },
    "to_section_works": {
        "ru": "Выполненные работы",
        "en": "Completed Works",
        "kk": "Орындалған жұмыстар",
        "uz": "Bajarilgan ishlar"
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
    "Другое": {
        "ru": "Другое",
        "en": "Other",
        "kk": "Басқа",
        "uz": "Boshqa"
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
