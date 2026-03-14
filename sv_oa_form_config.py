# -*- coding: utf-8 -*-
from typing import List, Dict, Any
from translations import FIELD_LABELS, SECTION_HEADERS, OPTION_TRANSLATIONS, get_translation

def translate_options(options: List[str], lang: str) -> List[str]:
    """Переводит варианты ответов на указанный язык"""
    return [get_translation(OPTION_TRANSLATIONS, opt, lang) for opt in options]

def get_form_config(lang: str = "ru") -> List[Dict[str, Any]]:
    """
    Возвращает конфигурацию формы с переводами на указанный язык

    Args:
        lang: Код языка (ru, en, kk, uz)

    Returns:
        Список элементов формы с переводами
    """
    return [
        {
            "id": "timestamp",
            "label": get_translation(FIELD_LABELS, "timestamp", lang),
            "type": "hidden",
            "required": False
        },
        {
            "id": "section_1",
            "type": "header",
            "label": get_translation(SECTION_HEADERS, "section_1", lang)
        },
        {
            "id": "inspection_date",
            "label": get_translation(FIELD_LABELS, "inspection_date", lang),
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
            "id": "driver_uid",
            "label": get_translation(FIELD_LABELS, "driver_uid", lang),
            "type": "select",
            "required": True,
            "options": []
        },
        {
            "id": "mechanic_uid",
            "label": get_translation(FIELD_LABELS, "mechanic_uid", lang),
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
            "id": "capacity_of_fuel_in_fueltank",
            "label": get_translation(FIELD_LABELS, "capacity_of_fuel_in_fueltank", lang),
            "type": "number",
            "required": True
        },
        {
            "id": "fuel_type",
            "label": {"ru": "Тип топлива", "en": "Fuel type", "kk": "Жанармай түрі", "uz": "Yoqilg'i turi"}[lang],
            "type": "radio",
            "options": translate_options(["Бензин", "Дизель", "Газ (Пропан)", "Газ (Метан)"], lang),
            "required": True
        },
        {
            "id": "section_2",
            "type": "header",
            "label": get_translation(SECTION_HEADERS, "section_2", lang)
        },
        {
            "id": "odometer",
            "label": get_translation(FIELD_LABELS, "motorhours", lang),
            "type": "odometer_group",
            "required": True,
            "fields": [
                {
                    "id": "motorhours",
                    "label": get_translation(FIELD_LABELS, "motorhours", lang),
                    "hint": "",
                }
            ]
        },
        {
            "id": "section_3",
            "type": "header",
            "label": get_translation(SECTION_HEADERS, "section_3", lang)
        },
        {
            "id": "body_state",
            "label": {"ru": "Состояние кузова", "en": "Body condition", "kk": "Кузовтың жағдайы", "uz": "Kuzovning holati"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "paint_state",
            "label": {"ru": "Состояние лакокрасочного покрытия", "en": "Paint condition", "kk": "Бояу жабынының жағдайы", "uz": "Bo'yoq qoplamining holati"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "body_cleanliness",
            "label": {"ru": "Чистота кузова", "en": "Body cleanliness", "kk": "Кузовтың тазалығы", "uz": "Kuzovning tozaligi"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "body_defects",
            "label": {"ru": "Какое либо повреждение", "en": "Any damage", "kk": "Кез келген зақым", "uz": "Har qanday zarar"}[lang],
            "type": "radio",
            "options": translate_options(["Отсутствует", "Имеется", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "section_4",
            "type": "header",
            "label": get_translation(SECTION_HEADERS, "section_4", lang)
        },
        {
            "id": "hydro_oil_level",
            "label": {"ru": "Уровень гидравлической жидкости", "en": "Hydraulic fluid level", "kk": "Гидравликалық сұйықтық деңгейі", "uz": "Gidravlik suyuqlik darajasi"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "hydro_oil_condition",
            "label": {"ru": "Состояние гидравлической жидкости и фильтров", "en": "Hydraulic fluid and filters condition", "kk": "Гидравликалық сұйықтық пен сүзгілердің жағдайы", "uz": "Gidravlik suyuqlik va filtrlar holati"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "hydro_oil_system_leakages",
            "label": {"ru": "Наличие какой-либо течи в системе", "en": "Any leaks in the system", "kk": "Жүйеде ағу бар ма", "uz": "Tizimda oqish bormi"}[lang],
            "type": "radio",
            "options": translate_options(["Отсутствует", "Имеется", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "section_5",
            "type": "header",
            "label": get_translation(SECTION_HEADERS, "section_5", lang)
        },
        {
            "id": "crane_boom_condition",
            "label": {"ru": "Состояние стрелы", "en": "Boom condition", "kk": "Көтергіштің жағдайы", "uz": "Kran strelkasining holati"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "slings_or_ropes_condition",
            "label": {"ru": "Состояние строп или троса", "en": "Slings or ropes condition", "kk": "Стропалар немесе арқанның жағдайы", "uz": "Bog'ichlar yoki arqonning holati"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "safety_latches_condition",
            "label": {"ru": "Состояние предохранительных щеколд", "en": "Safety latches condition", "kk": "Қауіпсіздік ілгектерінің жағдайы", "uz": "Xavfsizlik qulflari holati"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "whinch_cable_drum_condition",
            "label": {"ru": "Состояние барабана троса лебедки", "en": "Winch cable drum condition", "kk": "Лебедка арқан барабанының жағдайы", "uz": "Lebedka arqon barabanining holati"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "secondary_whinch_condition",
            "label": {"ru": "Состояние вспомогательной лебедки", "en": "Secondary winch condition", "kk": "Көмекші лебедканың жағдайы", "uz": "Yordamchi lebedkaning holati"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "section_6",
            "type": "header",
            "label": get_translation(SECTION_HEADERS, "section_6", lang)
        },
        {
            "id": "oil_level",
            "label": {"ru": "Уровень жидкостей", "en": "Fluid levels", "kk": "Сұйықтық деңгейі", "uz": "Suyuqliklar darajasi"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "filter_conditions",
            "label": {"ru": "Состояние фильтров", "en": "Filters condition", "kk": "Сүзгілердің жағдайы", "uz": "Filtrlar holati"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "belts_and_rubber_parts_and_pipes_condition",
            "label": {"ru": "Состояние ремней и шлангов и прочие резиновые изделия", "en": "Belts, hoses and other rubber parts condition", "kk": "Белдіктер мен шлангілер және басқа резеңке бұйымдарының жағдайы", "uz": "Kamarlar, shlanglar va boshqa rezina buyumlar holati"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "radiator_condition_and_cleanliness",
            "label": {"ru": "Состояние и чистота радиаторов охлаждения", "en": "Cooling radiators condition and cleanliness", "kk": "Салқындату радиаторларының жағдайы және тазалығы", "uz": "Sovutish radiatorlarining holati va tozaligi"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "other_radiators_condition_and_cleanliness",
            "label": {"ru": "Состояние и чистота прочих радиаторов", "en": "Other radiators condition and cleanliness", "kk": "Басқа радиаторлардың жағдайы және тазалығы", "uz": "Boshqa radiatorlarning holati va tozaligi"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "electrical_wires_condition",
            "label": {"ru": "Состояние электропроводки", "en": "Electrical wiring condition", "kk": "Электр сымдарының жағдайы", "uz": "Elektr simlarining holati"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "starter_and_alternator_condition",
            "label": {"ru": "Состояние стартера и генератора", "en": "Starter and alternator condition", "kk": "Стартер мен генератордың жағдайы", "uz": "Starter va generatorning holati"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "section_7",
            "type": "header",
            "label": get_translation(SECTION_HEADERS, "section_7", lang)
        },
        {
            "id": "final_gear_drive_condition",
            "label": {"ru": "Состояние главной пары редуктора", "en": "Final gear drive condition", "kk": "Редуктор негізгі жұптың жағдайы", "uz": "Reduktor asosiy juftligining holati"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "lower_body_condition",
            "label": {"ru": "Состояние нижней части кузова", "en": "Lower body condition", "kk": "Кузовтың төменгі бөлігінің жағдайы", "uz": "Kuzovning pastki qismining holati"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "suspension_condition",
            "label": {"ru": "Состояние подвески", "en": "Suspension condition", "kk": "Аспаның жағдайы", "uz": "Osma tizimning holati"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "gears_and_synchronizers_condition",
            "label": {"ru": "Состояние шестерен и синхронизаторов КПП", "en": "Gears and synchronizers condition", "kk": "КПП тістегілері мен синхронизаторларының жағдайы", "uz": "KPP tishli g'ildiraklari va sinxronizatorlarining holati"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "tracks_gears_wheels_driveshafts_condition",
            "label": {"ru": "Состояние гусеницы, шестерен, колес и приводных валов", "en": "Tracks, gears, wheels and driveshafts condition", "kk": "Шынжырлар, тістегілер, дөңгелектер және жетек білігінің жағдайы", "uz": "Zanjirlar, tishli g'ildiraklar, g'ildiraklar va haydovchi vallarning holati"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "section_8",
            "type": "header",
            "label": get_translation(SECTION_HEADERS, "section_8", lang)
        },
        {
            "id": "protective_equipment",
            "label": {"ru": "Наличие средств защиты в кабине", "en": "Protective equipment in cabin", "kk": "Кабинада қорғаныс құралдарының болуы", "uz": "Kabinada himoya vositalari mavjudligi"}[lang],
            "type": "radio",
            "options": translate_options(["Имеется", "Отсутствует", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "windshield_condition",
            "label": {"ru": "Состояние ветрового стекла", "en": "Windshield condition", "kk": "Алдыңғы әйнектің жағдайы", "uz": "Old oynaning holati"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "seat_condition",
            "label": {"ru": "Состояние сидений", "en": "Seats condition", "kk": "Отырғыштардың жағдайы", "uz": "O'rindiqlar holati"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "belt_condition",
            "label": {"ru": "Состояние ремня безопасности", "en": "Seat belt condition", "kk": "Қауіпсіздік белдігінің жағдайы", "uz": "Xavfsizlik kamarining holati"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "signals_and_lights_functionality",
            "label": {"ru": "Работоспособность звукового сигнала, сигнала заднего хода, фар и фонарей", "en": "Horn, reverse signal, headlights and lights functionality", "kk": "Дыбыстық сигнал, артқа жүру сигналы, фаралар мен шамдардың жұмыс істеуі", "uz": "Ovozli signal, orqaga harakat signali, faralar va chiroqlar ishlashi"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "cabine_cleanliness",
            "label": {"ru": "Чистота кабины", "en": "Cabin cleanliness", "kk": "Кабинаның тазалығы", "uz": "Kabinaning tozaligi"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "section_9",
            "type": "header",
            "label": get_translation(SECTION_HEADERS, "section_9", lang)
        },
        {
            "id": "side_mirrors_and_rear_view_condition",
            "label": {"ru": "Состояние боковых зеркал и заднего вида", "en": "Side and rear view mirrors condition", "kk": "Бүйірлік және артқы көрініс айналарының жағдайы", "uz": "Yon va orqa ko'rish oynalarining holati"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "battery_condition",
            "label": {"ru": "Состояние аккумулятора", "en": "Battery condition", "kk": "Аккумулятордың жағдайы", "uz": "Akkumulyatorning holati"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "windshield_guards_condition",
            "label": {"ru": "Состояние дворников ветрового стекла", "en": "Windshield wipers condition", "kk": "Әйнек тазартқыштардың жағдайы", "uz": "Oyna tozalagichlarning holati"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "warning_signs",
            "label": {"ru": "Наличие предупреждающих знаков", "en": "Warning signs presence", "kk": "Ескерту белгілерінің болуы", "uz": "Ogohlantirish belgilarining mavjudligi"}[lang],
            "type": "radio",
            "options": translate_options(["Имеется", "Отсутствует", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "sensors_and_indicators_functionality",
            "label": {"ru": "Работоспособность и корректность датчиков и индикаторов", "en": "Sensors and indicators functionality", "kk": "Датчиктер мен индикаторлардың жұмыс істеуі және дұрыстығы", "uz": "Datchiklar va indikatorlarning ishlashi va to'g'riligi"}[lang],
            "type": "radio",
            "options": translate_options(["Нормальное", "Не нормальное", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "fire_extinguisher",
            "label": {"ru": "Наличие и работоспособность огнетушителя", "en": "Fire extinguisher presence and functionality", "kk": "Өрт сөндіргіштің болуы және жұмыс істеуі", "uz": "O't o'chiruvchining mavjudligi va ishlashi"}[lang],
            "type": "radio",
            "options": translate_options(["Имеется", "Отсутствует", "Другое"], lang),
            "required": True,
            "warning_text": {"ru": "Ваш текст предупреждения", "en": "Your warning text", "kk": "...", "uz": "..."}[lang]
        },
        {
            "id": "section_10",
            "type": "header",
            "label": get_translation(SECTION_HEADERS, "section_10", lang)
        },
        {
            "id": "registration_certificate",
            "label": {"ru": "Наличие техпаспорта", "en": "Registration certificate presence", "kk": "Техпаспорттың болуы", "uz": "Texpassportning mavjudligi"}[lang],
            "type": "radio",
            "options": translate_options(["Имеется", "Отсутствует"], lang),
            "required": True
        },
        {
            "id": "insurance",
            "label": {"ru": "Наличие страхового полиса", "en": "Insurance policy presence", "kk": "Сақтандыру полисінің болуы", "uz": "Sug'urta polisining mavjudligi"}[lang],
            "type": "radio",
            "options": translate_options(["Имеется", "Отсутствует"], lang),
            "required": True
        },
        {
            "id": "insurance_end_date",
            "label": {"ru": "Дата окончания страхового полиса", "en": "Insurance policy end date", "kk": "Сақтандыру полисінің аяқталу күні", "uz": "Sug'urta polisi tugash sanasi"}[lang],
            "type": "date",
            "required": True,
            "initially_hidden": True
        },
        {
            "id": "technical_inspection",
            "label": {"ru": "Наличие документа технического осмотра", "en": "Technical inspection document presence", "kk": "Техникалық тексеру құжатының болуы", "uz": "Texnik ko'rik hujjatining mavjudligi"}[lang],
            "type": "radio",
            "options": translate_options(["Имеется", "Отсутствует"], lang),
            "required": True
        },
        {
            "id": "technical_inspection_date",
            "label": {"ru": "Дата окончания документа технического осмотра", "en": "Technical inspection document end date", "kk": "Техникалық тексеру құжатының аяқталу күні", "uz": "Texnik ko'rik hujjati tugash sanasi"}[lang],
            "type": "date",
            "required": True,
            "initially_hidden": True
        },
    ]
