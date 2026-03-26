const tg = window.Telegram.WebApp;

// Функция для получения перевода
function t(key) {
    return window.TRANSLATIONS && window.TRANSLATIONS[key] ? window.TRANSLATIONS[key] : key;
}

function updateConditionalNote(fieldId, selectedText) {
    const noteEl = document.getElementById(`note_${fieldId}`);
    if (!noteEl) return;

    const notes = JSON.parse(noteEl.dataset.notes);
    let matchedNote = null;

    for (const [key, text] of Object.entries(notes)) {
        if (selectedText.includes(key)) {
            matchedNote = text;
            break;
        }
    }

    if (matchedNote) {
        noteEl.textContent = matchedNote;
        noteEl.style.display = 'block';
    } else {
        noteEl.textContent = '';
        noteEl.style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Initialize Telegram WebApp
    tg.ready();
    tg.expand(); // Expand to full height

    // Set Main Button params with translation
    tg.MainButton.setText(t('submit_button'));
    tg.MainButton.show();
    tg.MainButton.enable();

    // Load data if elements present
    const machineSelect = document.getElementById('machine_uid');
    if (machineSelect) {
        loadMachines();
    }

    const driverSelect = document.getElementById('driver_uid');
    if (driverSelect) {
        loadDrivers();
    }

    const mechanicSelect = document.getElementById('mechanic_uid');
    if (mechanicSelect) {
        loadMechanics();
    }

    const departmentSelect = document.getElementById('department_uid');
    if (departmentSelect) {
        loadDepartments();
    }

    const responsibleSelect = document.getElementById('responsible_person_uid');
    if (responsibleSelect) {
        loadResponsiblePersons();
    }

    const repairTypeSelect = document.getElementById('repair_type_uid');
    if (repairTypeSelect) {
        loadRepairTypes();
    }

    // Listen to MainButton click
    tg.MainButton.onClick(() => {
        submitForm();
    });

    // Add input listeners to remove error styles
    const inputs = document.querySelectorAll('input, textarea');
    inputs.forEach(input => {
        input.addEventListener('input', () => {
            const card = input.closest('.question-card');
            if (card) {
                card.classList.remove('error');
            }
        });
    });

    // Setup "Другое" (Other) functionality for radio buttons
    setupOtherInputs();

    // Setup conditional date fields for insurance and technical_inspection
    setupConditionalDateFields();

    // Load nomenclature for TO form repeaters, then init tables
    if (window.APP_FORM_TYPE === 'to') {
        loadNomenclature().then(() => initTables());
    } else {
        initTables();
    }
});

/**
 * Настройка функционала "Другое" для radio кнопок
 * Показывает текстовое поле когда выбрано "Другое"
 */
function setupOtherInputs() {
    // Переводы слова "Другое" на всех языках
    const otherTranslations = ['Другое', 'Other', 'Басқа', 'Boshqa'];

    // Устанавливаем placeholder для всех текстовых полей "Другое"
    const otherTextInputs = document.querySelectorAll('.other-text-input');
    otherTextInputs.forEach(input => {
        input.placeholder = t('other_placeholder');
    });

    // Переводы значений, при которых показываем предупреждение
    const warningTriggers = [
        'Не нормальное', 'Not normal', 'Қалыпсыз', 'Normal emas',
        'Отсутствует', 'Absent', 'Жоқ', "Yo'q"
    ];

    // Переводы значений для альтернативного предупреждения
    const warningAltTriggers = [
        'Нормальное', 'Normal', 'Қалыпты', 'Normal',
        'Имеется', 'Present', 'Бар', 'Bor'
    ];

    const radioInputs = document.querySelectorAll('input[type="radio"]');

    radioInputs.forEach(radio => {
        radio.addEventListener('change', function() {
            const fieldId = this.name; // name совпадает с id поля
            const otherContainer = document.getElementById(`other_container_${fieldId}`);
            const otherTextInput = document.getElementById(`other_text_${fieldId}`);

            if (otherContainer && otherTextInput) {
                // Проверяем, выбрано ли "Другое" (на любом языке)
                const isOther = otherTranslations.includes(this.value);

                if (isOther) {
                    otherContainer.style.display = 'block';
                    otherTextInput.focus();
                } else {
                    otherContainer.style.display = 'none';
                    otherTextInput.value = '';
                }
            }

            // Показ/скрытие предупреждения
            const warningEl = document.getElementById(`warning_${fieldId}`);
            if (warningEl) {
                const isWarning = warningTriggers.includes(this.value);
                warningEl.style.display = isWarning ? 'block' : 'none';
            }

            // Показ/скрытие альтернативного предупреждения
            const warningAltEl = document.getElementById(`warning_alt_${fieldId}`);
            if (warningAltEl) {
                const isAltWarning = warningAltTriggers.includes(this.value);
                warningAltEl.style.display = isAltWarning ? 'block' : 'none';
            }
        });
    });
}

/**
 * Управляет видимостью полей дат для страховки и техосмотра.
 * Дата показывается только при выборе "Имеется" (первый вариант).
 */
function setupConditionalDateFields() {
    // Переводы "Имеется" на всех языках (первый вариант = Да)
    const yesTranslations = ['Имеется', 'Present', 'Бар', 'Bor'];

    const conditionals = [
        { radioName: 'insurance', dateCardId: 'card_insurance_end_date' },
        { radioName: 'technical_inspection', dateCardId: 'card_technical_inspection_date' }
    ];

    conditionals.forEach(({ radioName, dateCardId }) => {
        const radios = document.querySelectorAll(`input[name="${radioName}"]`);
        const dateCard = document.getElementById(dateCardId);
        if (!dateCard) return;

        radios.forEach(radio => {
            radio.addEventListener('change', function() {
                if (yesTranslations.includes(this.value)) {
                    dateCard.style.display = 'block';
                } else {
                    dateCard.style.display = 'none';
                    const dateInput = dateCard.querySelector('input[type="date"]');
                    if (dateInput) dateInput.value = '';
                }
            });
        });
    });
}

let machinesData = [];
let driversData = [];
let mechanicsData = [];
let departmentsData = [];
let responsiblePersonsData = [];
let repairTypesData = [];
let nomenclatureData = [];

async function loadMachines() {
    try {
        let category = 'all';
        const formType = window.APP_FORM_TYPE || '';
        if (formType === 'lv' || formType === 'lv_oa') category = 'lv';
        else if (formType === 'sv' || formType === 'sv_oa') category = 'sv';

        const response = await fetch(`api/machines?category=${category}`);
        machinesData = await response.json();
        setupModalSelect(machinesData, 'machine_uid', formatMachine, (item) => {
            if (window.APP_FORM_TYPE === 'to') onMachineSelectedTO(item);
        });
    } catch (e) {
        console.error("Failed to load machines:", e);
        showError(t('loading_machines_error'));
    }
}

async function loadDrivers() {
    try {
        const response = await fetch('api/drivers');
        driversData = await response.json();
        setupModalSelect(driversData, 'driver_uid', formatEmployee);
    } catch (e) {
        console.error("Failed to load drivers:", e);
        showError(t('loading_drivers_error'));
    }
}

async function loadMechanics() {
    try {
        const response = await fetch('api/mechanics');
        mechanicsData = await response.json();
        setupModalSelect(mechanicsData, 'mechanic_uid', formatEmployee);
    } catch (e) {
        console.error("Failed to load mechanics:", e);
        showError(t('loading_mechanics_error'));
    }
}

async function loadResponsiblePersons() {
    try {
        const [driversRes, mechanicsRes] = await Promise.all([
            fetch('api/drivers'),
            fetch('api/mechanics')
        ]);
        const drivers = await driversRes.json();
        const mechanics = await mechanicsRes.json();
        responsiblePersonsData = [...drivers, ...mechanics];
        setupModalSelect(responsiblePersonsData, 'responsible_person_uid', formatEmployee);
    } catch (e) {
        console.error("Failed to load responsible persons:", e);
        showError(t('loading_drivers_error'));
    }
}

async function loadRepairTypes() {
    try {
        const response = await fetch('api/repair_types');
        repairTypesData = await response.json();
        setupModalSelect(repairTypesData, 'repair_type_uid', formatRepairType, (item, displayText) => {
            if (window.APP_FORM_TYPE === 'to') onRepairTypeSelected(displayText);
        });
    } catch (e) {
        console.error("Failed to load repair types:", e);
        showError('Failed to load repair types');
    }
}

async function loadDepartments() {
    try {
        const response = await fetch('api/departments');
        departmentsData = await response.json();
        setupModalSelect(departmentsData, 'department_uid', formatDepartment);
    } catch (e) {
        console.error("Failed to load departments:", e);
        showError(t('loading_departments_error') || 'Failed to load departments');
    }
}

async function loadNomenclature() {
    try {
        const response = await fetch('api/nomenclature');
        nomenclatureData = await response.json();
        console.log(`Loaded ${nomenclatureData.length} nomenclature items`);
    } catch (e) {
        console.error("Failed to load nomenclature:", e);
    }
}

function formatMachine(machine) {
    return `${machine.model} | ${machine.license_plate || 'Нет ГРНЗ'} | ${machine.inventory_number}`;
}

function formatEmployee(employee) {
    return employee.full_name;
}

function formatDepartment(department) {
    return department.name;
}

function formatRepairType(repairType) {
    return repairType.name;
}

/**
 * Настраивает модальный выбор для поля формы.
 * Кнопка trigger_${fieldId} открывает модалку, выбор записывается в hidden input.
 * @param {Array} items - массив элементов
 * @param {string} fieldId - ID скрытого поля
 * @param {Function} formatFunction - форматирование отображаемого текста
 * @param {Function} [onSelectCallback] - дополнительный callback (item, displayText)
 */
function setupModalSelect(items, fieldId, formatFunction, onSelectCallback) {
    const triggerBtn = document.getElementById(`trigger_${fieldId}`);
    const hiddenInput = document.getElementById(fieldId);
    if (!triggerBtn || !hiddenInput) return;

    const label = triggerBtn.textContent.trim();

    triggerBtn.addEventListener('click', () => {
        // Преобразуем items в формат {id, name} для модалки
        const modalItems = items.map(item => ({
            _original: item,
            id: item.id,
            name: formatFunction(item)
        }));

        openSelectionModal(label.replace('...', ''), modalItems, (selected) => {
            triggerBtn.textContent = selected.name;
            triggerBtn.classList.add('has-value');
            hiddenInput.value = selected.id;

            // Убираем ошибку
            const card = triggerBtn.closest('.question-card');
            if (card) card.classList.remove('error');

            // Conditional notes
            updateConditionalNote(fieldId, selected.name);

            // Extra callback
            if (onSelectCallback) {
                onSelectCallback(selected._original, selected.name);
            }
        });
    });
}

function validateForm() {
    const cards = document.querySelectorAll('.question-card[data-required="True"]');
    const otherTranslations = ['Другое', 'Other', 'Басқа', 'Boshqa'];
    let isValid = true;
    let firstErrorCard = null;

    cards.forEach(card => {
        if (card.style.display === 'none') return; // пропускаем скрытые условные поля

        const isOdometerGroup = card.classList.contains('odometer-group');
        const input = card.querySelector('input[type="text"], input[type="date"], input[type="number"], textarea');
        const hiddenSelect = card.querySelector('.custom-select-container input[type="hidden"]');
        const radios = card.querySelectorAll('input[type="radio"]');
        let filled = false;

        if (hiddenSelect) {
            // Modal-based select — check hidden input has a value
            if (hiddenSelect.value.trim() !== '') filled = true;
        } else if (isOdometerGroup) {
            // Одометр: достаточно заполнить хотя бы одно поле
            card.querySelectorAll('.odometer-input').forEach(inp => {
                if (inp.value.trim() !== '') filled = true;
            });
        } else if (input && !input.classList.contains('other-text-input')) {
            // Обычные текстовые поля (не "Другое")
            if (input.value.trim() !== '') {
                filled = true;
            }
        } else if (radios.length > 0) {
            // Radio кнопки
            let selectedRadio = null;
            radios.forEach(radio => {
                if (radio.checked) {
                    filled = true;
                    selectedRadio = radio;
                }
            });

            // Если выбрано "Другое", проверяем заполнение текстового поля
            if (selectedRadio && otherTranslations.includes(selectedRadio.value)) {
                const fieldId = selectedRadio.name;
                const otherTextInput = document.getElementById(`other_text_${fieldId}`);
                if (!otherTextInput || otherTextInput.value.trim() === '') {
                    filled = false;
                }
            }
        }

        if (!filled) {
            isValid = false;
            card.classList.add('error');
            if (!firstErrorCard) firstErrorCard = card;
        } else {
            card.classList.remove('error');
        }
    });

    if (firstErrorCard) {
        firstErrorCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
        tg.HapticFeedback.notificationOccurred('error');
    }

    return isValid;
}

async function submitForm() {
    if (!validateForm()) {
        return;
    }

    tg.MainButton.showProgress();

    // Collect data
    const formData = new FormData(document.getElementById('inspectionForm'));
    const data = {};
    formData.forEach((value, key) => {
        data[key] = value;
    });

    // Удаляем поля дат скрытых условных блоков, чтобы не отправлять их в Google Sheets
    ['insurance_end_date', 'technical_inspection_date'].forEach(fieldId => {
        const card = document.getElementById(`card_${fieldId}`);
        if (card && card.style.display === 'none') {
            delete data[fieldId];
        }
    });

    // Обработка полей с "Другое" - заменяем на текст из текстового поля
    const otherTranslations = ['Другое', 'Other', 'Басқа', 'Boshqa'];
    Object.keys(data).forEach(key => {
        if (otherTranslations.includes(data[key])) {
            const otherTextInput = document.getElementById(`other_text_${key}`);
            if (otherTextInput && otherTextInput.value.trim()) {
                data[key] = otherTextInput.value.trim();
            }
        }
    });

    // Add Telegram user_id and language for confirmation message
    console.log('Telegram WebApp object:', tg);
    console.log('initDataUnsafe:', tg.initDataUnsafe);
    console.log('initData (raw):', tg.initData);

    // Try multiple methods to get user_id
    let userId = null;

    // Method 1: From URL parameter (fallback for Desktop/problematic versions)
    const urlParams = new URLSearchParams(window.location.search);
    const urlUserId = urlParams.get('tg_user_id');
    if (urlUserId) {
        userId = parseInt(urlUserId);
        console.log('✅ Method 1: user_id from URL parameter:', userId);
    }

    // Method 2: initDataUnsafe.user.id (standard way)
    if (!userId && tg.initDataUnsafe && tg.initDataUnsafe.user && tg.initDataUnsafe.user.id) {
        userId = tg.initDataUnsafe.user.id;
        console.log('✅ Method 2: user_id from initDataUnsafe:', userId);
    }

    // Method 3: Parse initData string
    if (!userId && tg.initData) {
        try {
            const initDataParams = new URLSearchParams(tg.initData);
            const userJson = initDataParams.get('user');
            if (userJson) {
                const user = JSON.parse(decodeURIComponent(userJson));
                userId = user.id;
                console.log('✅ Method 3: user_id parsed from initData:', userId);
            }
        } catch (e) {
            console.error('Failed to parse initData:', e);
        }
    }

    if (userId) {
        data['telegram_user_id'] = userId;
        console.log('✅ Final telegram_user_id captured:', userId);
    } else {
        console.error('❌ Telegram user data not available!');
        console.log('Full Telegram WebApp data:', JSON.stringify({
            initData: tg.initData,
            initDataUnsafe: tg.initDataUnsafe,
            version: tg.version,
            platform: tg.platform,
            isExpanded: tg.isExpanded,
            viewportHeight: tg.viewportHeight,
            colorScheme: tg.colorScheme
        }, null, 2));
    }

    if (window.APP_LANG) {
        data['lang'] = window.APP_LANG;
        console.log('✅ Language captured:', window.APP_LANG);
    }

    if (window.APP_FORM_TYPE) {
        data['form_type'] = window.APP_FORM_TYPE;
        console.log('✅ Form type captured:', window.APP_FORM_TYPE);
    }

    // Collect dynamic table data
    const materialsData = collectRepeaterData('materials_table');
    if (materialsData.length > 0) {
        data['materials_table'] = materialsData;
    }
    const worksData = collectRepeaterData('works_table');
    if (worksData.length > 0) {
        data['works_table'] = worksData;
    }

    console.log('📤 Submitting data:', JSON.stringify(data, null, 2));

    // Определяем endpoint по типу формы
    const submitUrl = (window.APP_FORM_TYPE === 'to') ? 'submit_to' : 'submit';

    try {
        const response = await fetch(submitUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            tg.HapticFeedback.notificationOccurred('success');
            tg.close();
        } else {
            console.error('Submission failed:', result.error);
            showError(t('submission_error') + ': ' + (result.error || ''));
            tg.HapticFeedback.notificationOccurred('error');
            tg.MainButton.hideProgress();
        }
    } catch (e) {
        console.error('Network error:', e);
        showError(t('network_error'));
        tg.HapticFeedback.notificationOccurred('error');
        tg.MainButton.hideProgress();
    }
}

function showError(msg) {
    const errorDiv = document.getElementById('submit-error');
    errorDiv.textContent = msg;
    errorDiv.style.display = 'block';
}

/**
 * Обработка выбора машины в форме ТО:
 * - Показывает километраж (lv) или моточасы (sv) в зависимости от типа машины
 * - Загружает и показывает последний введенный пробег
 */
// ============================================================
// Repeater Functions (Табличные части — каждая запись как карточка)
// ============================================================

function addRepeaterEntry(repeaterId) {
    const container = document.getElementById(`repeater_${repeaterId}`);
    const entriesContainer = document.getElementById(`entries_${repeaterId}`);
    if (!container || !entriesContainer) return;

    const fields = JSON.parse(container.dataset.fields);
    const entryIndex = entriesContainer.children.length;

    // Карточка записи (как question-card)
    const card = document.createElement('div');
    card.className = 'question-card repeater-entry';
    card.dataset.entryIndex = entryIndex;
    card.dataset.repeaterId = repeaterId;

    // Заголовок с номером и кнопкой удаления
    const header = document.createElement('div');
    header.className = 'repeater-entry-header';

    const title = document.createElement('span');
    title.className = 'repeater-entry-title';
    title.textContent = `#${entryIndex + 1}`;

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'remove-entry-btn';
    removeBtn.textContent = '✕';
    removeBtn.onclick = function() {
        card.remove();
        // Перенумеровать оставшиеся
        renumberEntries(repeaterId);
    };

    header.appendChild(title);
    header.appendChild(removeBtn);
    card.appendChild(header);

    // Поля — каждое в своём блоке
    fields.forEach(field => {
        const fieldBlock = document.createElement('div');
        fieldBlock.className = 'repeater-field';

        const label = document.createElement('label');
        label.className = 'question-label';
        label.textContent = field.label;
        fieldBlock.appendChild(label);

        if (field.type === 'select' && field.select_source) {
            // Modal-based select for repeater fields
            const triggerBtn = document.createElement('button');
            triggerBtn.type = 'button';
            triggerBtn.className = 'repeater-select-trigger';
            triggerBtn.textContent = field.label + '...';

            const hiddenUid = document.createElement('input');
            hiddenUid.type = 'hidden';
            hiddenUid.name = `${repeaterId}__${entryIndex}__${field.id}_uid`;
            hiddenUid.dataset.repeaterId = repeaterId;
            hiddenUid.dataset.fieldId = field.id + '_uid';

            const hiddenName = document.createElement('input');
            hiddenName.type = 'hidden';
            hiddenName.name = `${repeaterId}__${entryIndex}__${field.id}_name`;
            hiddenName.dataset.repeaterId = repeaterId;
            hiddenName.dataset.fieldId = field.id + '_name';

            triggerBtn.addEventListener('click', () => {
                let sourceData = [];
                if (field.select_source === 'nomenclature') sourceData = nomenclatureData;
                if (field.select_source === 'units') sourceData = unitsData;

                openSelectionModal(field.label, sourceData, (item) => {
                    triggerBtn.textContent = item.name;
                    triggerBtn.classList.add('has-value');
                    hiddenUid.value = item.id || '';
                    hiddenName.value = item.name;
                });
            });

            fieldBlock.appendChild(triggerBtn);
            fieldBlock.appendChild(hiddenUid);
            fieldBlock.appendChild(hiddenName);
        } else {
            // Regular input
            const input = document.createElement('input');
            input.type = field.type === 'number' ? 'number' : 'text';
            input.className = 'text-input';
            input.name = `${repeaterId}__${entryIndex}__${field.id}`;
            input.dataset.repeaterId = repeaterId;
            input.dataset.fieldId = field.id;
            if (field.type === 'number') {
                input.min = '0';
                input.step = 'any';
                input.placeholder = '0';
            }
            fieldBlock.appendChild(input);
        }

        card.appendChild(fieldBlock);
    });

    entriesContainer.appendChild(card);
}

function renumberEntries(repeaterId) {
    const entriesContainer = document.getElementById(`entries_${repeaterId}`);
    if (!entriesContainer) return;
    entriesContainer.querySelectorAll('.repeater-entry').forEach((card, i) => {
        card.dataset.entryIndex = i;
        const title = card.querySelector('.repeater-entry-title');
        if (title) title.textContent = `#${i + 1}`;
    });
}

function collectRepeaterData(repeaterId) {
    const entriesContainer = document.getElementById(`entries_${repeaterId}`);
    if (!entriesContainer) return [];

    const entries = [];
    entriesContainer.querySelectorAll('.repeater-entry').forEach(card => {
        const rowData = {};
        let hasValue = false;
        // Collect all inputs including hidden fields (uid, name for selects)
        card.querySelectorAll('input').forEach(input => {
            const fieldId = input.dataset.fieldId;
            if (!fieldId) return;
            // Skip search inputs (role=search) — they're just for UI
            if (input.dataset.role === 'search') return;
            rowData[fieldId] = input.value;
            if (input.value.trim()) hasValue = true;
        });
        if (hasValue) entries.push(rowData);
    });
    return entries;
}

// Initialize repeaters — add one empty entry by default
function initTables() {
    document.querySelectorAll('.repeater-container').forEach(container => {
        const repeaterId = container.id.replace('repeater_', '');
        addRepeaterEntry(repeaterId);
    });
}

// ============================================================
// Static units data
// ============================================================
const unitsData = [
    { id: '', name: 'шт' },
    { id: '', name: 'кг' },
    { id: '', name: 'л' },
    { id: '', name: 'м' },
    { id: '', name: 'компл' },
    { id: '', name: 'упак' },
    { id: '', name: 'п.м.' },
    { id: '', name: 'м²' },
    { id: '', name: 'м³' },
];

// ============================================================
// Selection Modal
// ============================================================
function openSelectionModal(title, items, onSelect) {
    const modal = document.getElementById('selectionModal');
    const titleEl = document.getElementById('modalTitle');
    const searchEl = document.getElementById('modalSearch');
    const listEl = document.getElementById('modalList');

    titleEl.textContent = title;
    searchEl.value = '';
    listEl.innerHTML = '';

    items.forEach(item => {
        const div = document.createElement('div');
        div.className = 'modal-list-item';
        div.textContent = item.name;
        div.addEventListener('click', () => {
            onSelect(item);
            closeSelectionModal();
        });
        listEl.appendChild(div);
    });

    searchEl.oninput = (e) => {
        const term = e.target.value.toLowerCase();
        listEl.querySelectorAll('.modal-list-item').forEach(el => {
            el.style.display = el.textContent.toLowerCase().includes(term) ? '' : 'none';
        });
    };

    modal.style.display = 'flex';
}

function closeSelectionModal() {
    document.getElementById('selectionModal').style.display = 'none';
}

// Close modal on overlay click
document.addEventListener('click', (e) => {
    const modal = document.getElementById('selectionModal');
    if (modal && e.target === modal) {
        closeSelectionModal();
    }
});

// ============================================================
// Conditional: Repair type → breakdown_reason / inspection_result
// ============================================================
function onRepairTypeSelected(selectedText) {
    const isUnplanned = selectedText.toLowerCase().includes('внеплановый');
    const breakdownCard = document.getElementById('card_breakdown_reason');
    const inspectionCard = document.getElementById('card_inspection_result');

    if (breakdownCard) {
        breakdownCard.style.display = isUnplanned ? 'block' : 'none';
        breakdownCard.dataset.required = isUnplanned ? 'True' : 'False';
        if (!isUnplanned) {
            const ta = breakdownCard.querySelector('textarea');
            if (ta) ta.value = '';
        }
    }
    if (inspectionCard) {
        inspectionCard.style.display = isUnplanned ? 'none' : 'block';
        inspectionCard.dataset.required = isUnplanned ? 'False' : 'True';
        if (isUnplanned) {
            const ta = inspectionCard.querySelector('textarea');
            if (ta) ta.value = '';
        }
    }
}

// ============================================================
// TO form: Machine selection handler
// ============================================================
async function onMachineSelectedTO(machine) {
    const vehicleType = machine.vehicle_type || 'lv';
    console.log('🔧 TO machine selected:', machine.model, 'vehicle_type:', vehicleType, 'id:', machine.id);

    const mileageCard = document.getElementById('card_to_mileage');
    const motorhoursCard = document.getElementById('card_to_motorhours');
    const lastMileageCard = document.getElementById('card_last_mileage_display');

    // Показываем нужное поле, скрываем другое
    if (vehicleType === 'lv') {
        if (mileageCard) mileageCard.style.display = 'block';
        if (motorhoursCard) {
            motorhoursCard.style.display = 'none';
            const inp = motorhoursCard.querySelector('input');
            if (inp) inp.value = '';
        }
    } else {
        if (motorhoursCard) motorhoursCard.style.display = 'block';
        if (mileageCard) {
            mileageCard.style.display = 'none';
            const inp = mileageCard.querySelector('input');
            if (inp) inp.value = '';
        }
    }

    // Загружаем последний пробег
    if (lastMileageCard) {
        try {
            const resp = await fetch(`api/last_mileage/${machine.id}`);
            const data = await resp.json();
            const lastMileageInput = document.getElementById('last_mileage_display');
            if (lastMileageInput) {
                if (vehicleType === 'lv') {
                    lastMileageInput.value = `${data.mileage || 0} км`;
                } else {
                    lastMileageInput.value = `${data.motorhours || 0} м/ч`;
                }
            }
            lastMileageCard.style.display = 'block';
        } catch (e) {
            console.error('Failed to load last mileage:', e);
        }
    }
}
