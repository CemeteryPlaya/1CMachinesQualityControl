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
        "to_submission_confirmed": "✅ Отчет о ТО отправлен.\nДата и время отправки: {datetime}",
        "select_checklist_period": "Выберите тип чек-листа:",
        "checklist_daily": "📅 Ежедневный",
        "checklist_weekly": "🗓 Еженедельный",
        "change_checklist_period": "🔀 Выбрать тип чек-листа",
        "fill_daily_form_button": "📝 Заполнить ежедневный чек-лист",
        "daily_submission_confirmed": "✅ Ежедневный чек-лист отправлен.\nДата и время отправки: {datetime}",
        "enter_full_name": "Для работы с ботом укажите ваше Ф.И.О (например: Иванов Иван Иванович):",
        "full_name_saved": "✅ Спасибо, {name}! Ваши данные сохранены.",
        "full_name_invalid": "⚠️ Укажите корректное Ф.И.О: минимум фамилия и имя (например: Иванов Иван)."
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
        "to_submission_confirmed": "✅ Maintenance report submitted.\nSubmission date and time: {datetime}",
        "select_checklist_period": "Select checklist type:",
        "checklist_daily": "📅 Daily",
        "checklist_weekly": "🗓 Weekly",
        "change_checklist_period": "🔀 Select checklist type",
        "fill_daily_form_button": "📝 Fill daily checklist",
        "daily_submission_confirmed": "✅ Daily checklist submitted.\nSubmission date and time: {datetime}",
        "enter_full_name": "To use the bot, please enter your full name (e.g., John Smith):",
        "full_name_saved": "✅ Thank you, {name}! Your details have been saved.",
        "full_name_invalid": "⚠️ Please enter a valid full name: at least last and first name (e.g., John Smith)."
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
        "to_submission_confirmed": "✅ ТҚ есебі жіберілді.\nЖіберу күні мен уақыты: {datetime}",
        "select_checklist_period": "Тексеру тізімінің түрін таңдаңыз:",
        "checklist_daily": "📅 Күнделікті",
        "checklist_weekly": "🗓 Апта сайын",
        "change_checklist_period": "🔀 Тексеру тізімінің түрін таңдау",
        "fill_daily_form_button": "📝 Күнделікті тексеру тізімін толтыру",
        "daily_submission_confirmed": "✅ Күнделікті тексеру тізімі жіберілді.\nЖіберу күні мен уақыты: {datetime}",
        "enter_full_name": "Ботпен жұмыс істеу үшін Т.А.Ә көрсетіңіз (мысалы: Иванов Иван Иванович):",
        "full_name_saved": "✅ Рақмет, {name}! Деректеріңіз сақталды.",
        "full_name_invalid": "⚠️ Дұрыс Т.А.Ә көрсетіңіз: кемінде тегі мен аты (мысалы: Иванов Иван)."
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
        "to_submission_confirmed": "✅ TO hisoboti yuborildi.\nYuborish sanasi va vaqti: {datetime}",
        "select_checklist_period": "Tekshiruv ro'yxati turini tanlang:",
        "checklist_daily": "📅 Kunlik",
        "checklist_weekly": "🗓 Haftalik",
        "change_checklist_period": "🔀 Tekshiruv ro'yxati turini tanlash",
        "fill_daily_form_button": "📝 Kunlik tekshiruv ro'yxatini to'ldirish",
        "daily_submission_confirmed": "✅ Kunlik tekshiruv ro'yxati yuborildi.\nYuborish sanasi va vaqti: {datetime}",
        "enter_full_name": "Bot bilan ishlash uchun F.I.Sh kiriting (masalan: Ivanov Ivan Ivanovich):",
        "full_name_saved": "✅ Rahmat, {name}! Ma'lumotlaringiz saqlandi.",
        "full_name_invalid": "⚠️ To'g'ri F.I.Sh kiriting: kamida familiya va ism (masalan: Ivanov Ivan)."
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
    "operator": {
        "ru": "Оператор",
        "en": "Operator",
        "kk": "Оператор",
        "uz": "Operator"
    },
    "project": {
        "ru": "Проект",
        "en": "Project",
        "kk": "Жоба",
        "uz": "Loyiha"
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
    },
    "engine_oil": {
        "ru": "Состояние и уровень моторного масла",
        "en": "Engine oil condition and level",
        "kk": "Моторлық майдың жағдайы мен деңгейі",
        "uz": "Motor moyining holati va darajasi"
    },
    "antifreeze": {
        "ru": "Состояние и уровень антифриза",
        "en": "Antifreeze condition and level",
        "kk": "Антифриздің жағдайы мен деңгейі",
        "uz": "Antifriz holati va darajasi"
    },
    "air_filter": {
        "ru": "Состояние воздушного фильтра",
        "en": "Air filter condition",
        "kk": "Ауа сүзгісінің жағдайы",
        "uz": "Havo filtri holati"
    },
    "check_comment": {
        "ru": "Комментарий",
        "en": "Comment",
        "kk": "Түсініктеме",
        "uz": "Izoh"
    },
    "general_photos": {
        "ru": "Фотоотчёт техники",
        "en": "Vehicle photo report",
        "kk": "Техниканың фотоесебі",
        "uz": "Texnika foto hisoboti"
    },
    "general_photos_hint": {
        "ru": "Сфотографируйте технику с разных ракурсов (спереди, сзади, по бокам), "
              "чтобы зафиксировать её общее состояние и внешний вид на момент проверки. "
              "До 5 фотографий.",
        "en": "Photograph the vehicle from different angles (front, rear, sides) "
              "to record its general condition and appearance at the time of inspection. "
              "Up to 5 photos.",
        "kk": "Техниканы әртүрлі бұрыштардан (алдынан, артынан, бүйірінен) суретке түсіріңіз, "
              "тексеру кезіндегі жалпы жағдайы мен сыртқы түрін тіркеу үшін. "
              "5 суретке дейін.",
        "uz": "Texnikani turli burchaklardan (oldindan, orqadan, yon tomonlardan) suratga oling, "
              "tekshiruv vaqtidagi umumiy holati va tashqi ko'rinishini qayd etish uchun. "
              "5 tagacha rasm."
    },
    "check_photos": {
        "ru": "Фото состояния",
        "en": "Condition photos",
        "kk": "Жағдай фотосы",
        "uz": "Holat fotosi"
    },
    "repair_photos": {
        "ru": "Фотоотчёт (поломка / использованные запчасти)",
        "en": "Photo report (breakdown / used parts)",
        "kk": "Фотоесеп (сынық / қолданылған бөлшектер)",
        "uz": "Foto hisobot (nosozlik / ishlatilgan ehtiyot qismlar)"
    },
    "repair_photos_hint": {
        "ru": "Сфотографируйте поломку и/или запчасти, использованные при ремонте. До 10 фото.",
        "en": "Photograph the breakdown and/or parts used for the repair. Up to 10 photos.",
        "kk": "Сынықты және/немесе жөндеуге қолданылған бөлшектерді суретке түсіріңіз. 10 фотоға дейін.",
        "uz": "Nosozlikni va/yoki ta'mirlashda ishlatilgan ehtiyot qismlarni suratga oling. 10 tagacha foto."
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
        "ru": "Простой техники",
        "en": "Machinery idle time",
        "kk": "Техниканың бос тұрып қалуы",
        "uz": "Texnikaning bekor turib qolishi"
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
    },
    "daily_section_photos": {
        "ru": "Фотоотчёт",
        "en": "Photo Report",
        "kk": "Фотоесеп",
        "uz": "Foto hisobot"
    },
    "daily_section_checks": {
        "ru": "Проверка узлов",
        "en": "Component Checks",
        "kk": "Тораптарды тексеру",
        "uz": "Tugunlarni tekshirish"
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


# Строки веб-приложения (Mini App): единый источник для шаблона и script.js
# (раньше дублировались inline-словарями в index.html)
WEBAPP_STRINGS = {
    "subtitle": {
        "ru": "Пожалуйста, заполните форму внимательно.",
        "en": "Please fill out the form carefully.",
        "kk": "Нысанды мұқият толтырыңыз.",
        "uz": "Iltimos, formani ehtiyotkorlik bilan to'ldiring."
    },
    "submit_button": {"ru": "ОТПРАВИТЬ", "en": "SUBMIT", "kk": "ЖІБЕРУ", "uz": "YUBORISH"},
    "my_answer": {"ru": "Мой ответ", "en": "My answer", "kk": "Менің жауабым", "uz": "Mening javobim"},
    "field_required": {
        "ru": "Это поле обязательно", "en": "This field is required",
        "kk": "Бұл өріс міндетті", "uz": "Bu maydon majburiy"
    },
    "fill_one_field": {
        "ru": "Заполните хотя бы одно поле", "en": "Fill in at least one field",
        "kk": "Кемінде бір өрісті толтырыңыз", "uz": "Kamida bitta maydonni to'ldiring"
    },
    "other_placeholder": {
        "ru": "Укажите свой вариант", "en": "Specify your option",
        "kk": "Өз нұсқаңызды көрсетіңіз", "uz": "Oz variantingizni kiriting"
    },
    "add_row": {
        "ru": "+ Добавить строку", "en": "+ Add row",
        "kk": "+ Жол қосу", "uz": "+ Qator qo'shish"
    },
    "take_photo": {
        "ru": "📷 Снять фото", "en": "📷 Take photo",
        "kk": "📷 Фото түсіру", "uz": "📷 Foto olish"
    },
    "choose_photo": {
        "ru": "🖼 Выбрать фото", "en": "🖼 Choose photo",
        "kk": "🖼 Фото таңдау", "uz": "🖼 Foto tanlash"
    },
    "add_comment": {
        "ru": "💬 Добавить комментарий", "en": "💬 Add comment",
        "kk": "💬 Түсініктеме қосу", "uz": "💬 Izoh qo'shish"
    },
    "camera_cancel": {"ru": "Отмена", "en": "Cancel", "kk": "Бас тарту", "uz": "Bekor qilish"},
    "camera_done": {"ru": "Готово", "en": "Done", "kk": "Дайын", "uz": "Tayyor"},
    "camera_error": {
        "ru": "Не удалось открыть камеру. Разрешите доступ к камере или выберите фото из галереи.",
        "en": "Could not open the camera. Allow camera access or choose a photo from the gallery.",
        "kk": "Камераны ашу мүмкін болмады. Камераға рұқсат беріңіз немесе галереядан фото таңдаңыз.",
        "uz": "Kamerani ochib bo'lmadi. Kameraga ruxsat bering yoki galereyadan foto tanlang."
    },
    "loading_machines_error": {
        "ru": "Не удалось загрузить список машин", "en": "Failed to load machines list",
        "kk": "Машиналар тізімін жүктеу мүмкін болмады",
        "uz": "Mashinalar ro'yxatini yuklash muvaffaqiyatsiz tugadi"
    },
    "loading_drivers_error": {
        "ru": "Не удалось загрузить список водителей", "en": "Failed to load drivers list",
        "kk": "Жүргізушілер тізімін жүктеу мүмкін болмады",
        "uz": "Haydovchilar ro'yxatini yuklash muvaffaqiyatsiz tugadi"
    },
    "loading_mechanics_error": {
        "ru": "Не удалось загрузить список механиков", "en": "Failed to load mechanics list",
        "kk": "Механиктер тізімін жүктеу мүмкін болмады",
        "uz": "Mexaniklar ro'yxatini yuklash muvaffaqiyatsiz tugadi"
    },
    "loading_departments_error": {
        "ru": "Не удалось загрузить список подразделений", "en": "Failed to load departments list",
        "kk": "Бөлімдер тізімін жүктеу мүмкін болмады",
        "uz": "Bo'limlar ro'yxatini yuklash muvaffaqiyatsiz tugadi"
    },
    "submission_error": {
        "ru": "Ошибка при отправке", "en": "Submission error",
        "kk": "Жіберу қатесі", "uz": "Yuborish xatosi"
    },
    "network_error": {
        "ru": "Ошибка сети. Попробуйте еще раз.", "en": "Network error. Please try again.",
        "kk": "Желі қатесі. Қайталап көріңіз.", "uz": "Tarmoq xatosi. Iltimos, qayta urinib ko'ring."
    },
}


def get_webapp_strings(lang: str = "ru") -> dict:
    """Все строки веб-приложения для указанного языка (для шаблона и JS)."""
    return {key: get_translation(WEBAPP_STRINGS, key, lang) for key in WEBAPP_STRINGS}


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
    """Получает сообщение бота на нужном языке (фолбэк: русский, затем ключ)"""
    value = BOT_MESSAGES.get(lang, {}).get(key)
    if value is None:
        value = BOT_MESSAGES["ru"].get(key, key)
    return value


def get_form_translation(key: str, lang: str = "ru") -> str:
    """Получает перевод элемента формы на нужном языке"""
    return FORM_TRANSLATIONS.get(lang, FORM_TRANSLATIONS["ru"]).get(key, key)
