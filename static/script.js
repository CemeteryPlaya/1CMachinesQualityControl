const tg = window.Telegram.WebApp;

// Функция для получения перевода
function t(key) {
    return window.TRANSLATIONS && window.TRANSLATIONS[key] ? window.TRANSLATIONS[key] : key;
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

    // Listen to MainButton click
    tg.MainButton.onClick(() => {
        submitForm();
    });

    // Add input listeners to remove error styles
    const inputs = document.querySelectorAll('input');
    inputs.forEach(input => {
        input.addEventListener('input', () => {
            const card = input.closest('.question-card');
            if (card) {
                card.classList.remove('error');
            }
        });
    });
});

let machinesData = [];
let driversData = [];
let mechanicsData = [];

async function loadMachines() {
    try {
        const response = await fetch('/api/machines');
        const machines = await response.json();
        machinesData = machines; // Cache for filtering
        renderDropdownList(machines, 'machine_uid', formatMachine);
    } catch (e) {
        console.error("Failed to load machines:", e);
        showError(t('loading_machines_error'));
    }
}

async function loadDrivers() {
    try {
        const response = await fetch('/api/drivers');
        const drivers = await response.json();
        driversData = drivers; // Cache for filtering
        renderDropdownList(drivers, 'driver_uid', formatEmployee);
    } catch (e) {
        console.error("Failed to load drivers:", e);
        showError(t('loading_drivers_error'));
    }
}

async function loadMechanics() {
    try {
        const response = await fetch('/api/mechanics');
        const mechanics = await response.json();
        mechanicsData = mechanics; // Cache for filtering
        renderDropdownList(mechanics, 'mechanic_uid', formatEmployee);
    } catch (e) {
        console.error("Failed to load mechanics:", e);
        showError(t('loading_mechanics_error'));
    }
}

function formatMachine(machine) {
    return `Модель: ${machine.model} | ГРНЗ: ${machine.license_plate || 'Нет ГРНЗ'} | ИН: ${machine.inventory_number}`;
}

function formatEmployee(employee) {
    return employee.full_name;
}

function renderDropdownList(items, fieldId, formatFunction) {
    const listContainer = document.getElementById(`dropdown_${fieldId}`);
    const searchInput = document.getElementById(`search_${fieldId}`);
    const hiddenInput = document.getElementById(fieldId);

    if (!listContainer || !searchInput) return;

    // Clear list
    listContainer.innerHTML = '';

    items.forEach(item => {
        const dropdownItem = document.createElement('div');
        dropdownItem.className = 'dropdown-item';
        dropdownItem.textContent = formatFunction(item);
        dropdownItem.dataset.uid = item.id;

        dropdownItem.addEventListener('click', () => {
            searchInput.value = dropdownItem.textContent;
            hiddenInput.value = item.id;
            listContainer.style.display = 'none';
            searchInput.closest('.question-card').classList.remove('error');
        });

        listContainer.appendChild(dropdownItem);
    });

    // Search Logic - attach once
    if (!searchInput.hasAttribute('data-initialized')) {
        searchInput.setAttribute('data-initialized', 'true');

        searchInput.addEventListener('focus', () => {
            listContainer.style.display = 'block';
        });

        // Hide when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest(`#search_${fieldId}`) && !e.target.closest(`#dropdown_${fieldId}`)) {
                listContainer.style.display = 'none';
            }
        });

        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            const dropdownItems = listContainer.querySelectorAll('.dropdown-item');
            listContainer.style.display = 'block';

            dropdownItems.forEach(dropdownItem => {
                if (dropdownItem.textContent.toLowerCase().includes(term)) {
                    dropdownItem.style.display = 'block';
                } else {
                    dropdownItem.style.display = 'none';
                }
            });
        });
    }
}

function validateForm() {
    const cards = document.querySelectorAll('.question-card[data-required="True"]');
    let isValid = true;
    let firstErrorCard = null;

    cards.forEach(card => {
        const input = card.querySelector('input[type="text"], input[type="date"], input[type="number"]');
        const radios = card.querySelectorAll('input[type="radio"]');
        let filled = false;

        if (input) {
            if (input.value.trim() !== '') {
                filled = true;
            }
        } else if (radios.length > 0) {
            radios.forEach(radio => {
                if (radio.checked) {
                    filled = true;
                }
            });
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

    // Add Telegram user_id and language for confirmation message
    console.log('Telegram WebApp object:', tg);
    console.log('initDataUnsafe:', tg.initDataUnsafe);
    console.log('initData (raw):', tg.initData);

    // Try multiple methods to get user_id
    let userId = null;

    // Method 1: initDataUnsafe.user.id (standard way)
    if (tg.initDataUnsafe && tg.initDataUnsafe.user && tg.initDataUnsafe.user.id) {
        userId = tg.initDataUnsafe.user.id;
        console.log('✅ Method 1: user_id from initDataUnsafe:', userId);
    }

    // Method 2: Parse initData string
    if (!userId && tg.initData) {
        try {
            const urlParams = new URLSearchParams(tg.initData);
            const userJson = urlParams.get('user');
            if (userJson) {
                const user = JSON.parse(decodeURIComponent(userJson));
                userId = user.id;
                console.log('✅ Method 2: user_id parsed from initData:', userId);
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

    console.log('📤 Submitting data:', JSON.stringify(data, null, 2));

    try {
        const response = await fetch('/submit', {
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
