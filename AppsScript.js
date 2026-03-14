// ============================================================
// Конфигурация
// ============================================================

// URL микросервиса (ngrok или production)
var BASE_URL = "https://sabine-unchromed-bryon.ngrok-free.dev";

// API-ключ для авторизации (должен совпадать с GSHEETS_API_KEY в .env)
var API_KEY = "chk-a7f9b2e1d4c8";

// ID Google Form (для updateAllLists)
var FORM_ID = "1VQlyVVI5LOo6viMXMx9xvlUlRYQcyss5zk896arArxg";

// Ref_Key специального подразделения
var SPECIAL_DEPT_REF_KEY = "f65d5f0a-33bb-11f0-9341-d8bbc163ec30";

// Маппинг заголовков Google Sheets → ключи для PostgreSQL
// Ключи слева — точные названия колонок в листе "Ответы на форму"
var HEADER_TO_KEY = {
  "Отметка времени": "timestamp",
  "Дата осмотра": "inspection_date",
  "Подразделение": "department",
  "Водитель": "driver_name",
  "Механик": "mechanic_name",
  "Машина": "machine",
  "Количество топлива в баке": "fuel_amount",
  "Тип топлива": "fuel_type",
  "Пробег (км)": "mileage",
  "Километраж": "mileage",
  "Моточасы": "motorhours"
};


// ============================================================
// Отправка новых ответов в PostgreSQL
// ============================================================

/**
 * Триггер: вызывается при отправке Google Form.
 * Читает ответы из FormResponse и отправляет в микросервис.
 */
function onFormSubmit(e) {
  try {
    var response = e.response;
    var itemResponses = response.getItemResponses();

    // Собираем данные
    var data = {
      "form_type": "gsheets",
      "lang": "ru",
      "source": "google_form",
      "timestamp": Utilities.formatDate(
        response.getTimestamp(),
        Session.getScriptTimeZone(),
        "dd.MM.yyyy HH:mm:ss"
      )
    };

    for (var i = 0; i < itemResponses.length; i++) {
      var title = itemResponses[i].getItem().getTitle().trim();
      var value = itemResponses[i].getResponse();

      if (!title || !value) continue;

      // Маппим заголовок → ключ, если есть в словаре
      var key = HEADER_TO_KEY[title] || title;
      data[key] = value.toString();
    }

    // Отправляем в микросервис
    var result = sendToService(data);
    Logger.log("✅ Ответ отправлен в PostgreSQL: " + JSON.stringify(result));

  } catch (err) {
    Logger.log("❌ Ошибка onFormSubmit: " + err);
  }
}

/**
 * Отправляет данные в Flask API → PostgreSQL
 */
function sendToService(data) {
  var url = BASE_URL + "/api/inspection";

  var options = {
    "method": "post",
    "contentType": "application/json",
    "headers": {
      "X-API-Key": API_KEY,
      "ngrok-skip-browser-warning": "any-value"
    },
    "payload": JSON.stringify(data),
    "muteHttpExceptions": true
  };

  var response = UrlFetchApp.fetch(url, options);
  var code = response.getResponseCode();
  var body = response.getContentText();

  if (code !== 200) {
    Logger.log("❌ HTTP " + code + ": " + body);
    throw new Error("HTTP " + code);
  }

  return JSON.parse(body);
}

/**
 * Ручной запуск: отправить все существующие ответы из листа в PostgreSQL.
 * Запускать один раз для миграции старых данных.
 */
function migrateAllRows() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Ответы на форму");
  if (!sheet) {
    Logger.log("❌ Лист 'Ответы на форму' не найден");
    return;
  }

  var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  var lastRow = sheet.getLastRow();

  if (lastRow < 2) {
    Logger.log("Нет данных для миграции");
    return;
  }

  var allData = sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).getValues();
  var success = 0;
  var errors = 0;

  for (var r = 0; r < allData.length; r++) {
    var values = allData[r];
    var data = {
      "form_type": "gsheets",
      "lang": "ru",
      "source": "google_form_migration"
    };

    for (var i = 0; i < headers.length; i++) {
      var header = headers[i].toString().trim();
      var value = values[i];

      if (!header || value === "" || value === null || value === undefined) continue;

      if (value instanceof Date) {
        value = Utilities.formatDate(value, Session.getScriptTimeZone(), "dd.MM.yyyy");
      } else {
        value = value.toString();
      }

      var key = HEADER_TO_KEY[header] || header;
      data[key] = value;
    }

    try {
      sendToService(data);
      success++;
    } catch (err) {
      Logger.log("❌ Строка " + (r + 2) + ": " + err);
      errors++;
    }
  }

  Logger.log("Миграция завершена: " + success + " успешно, " + errors + " ошибок");
}


// ============================================================
// Обновление списков в Google Form (из API)
// ============================================================

function updateAllLists() {
  var form = FormApp.getActiveForm();

  var listsToUpdate = [
    { questionTitle: "Машина", apiEndpoint: "/api/get_machines_form" },
    { questionTitle: "Механик", apiEndpoint: "/api/mechanics" },
    { questionTitle: "Водитель", apiEndpoint: "/api/drivers" },
    { questionTitle: "Подразделение", apiEndpoint: "/api/departments" }
  ];

  listsToUpdate.forEach(function(listConfig) {
    try {
      var url = BASE_URL + listConfig.apiEndpoint;
      var options = {
        "method": "get",
        "headers": { "ngrok-skip-browser-warning": "any-value" }
      };

      var response = UrlFetchApp.fetch(url, options);
      var data = JSON.parse(response.getContentText());

      var choices = [];

      if (listConfig.apiEndpoint === "/api/get_machines_form") {
        choices = data;
      } else if (listConfig.apiEndpoint === "/api/departments") {
        choices = data
          .filter(function(item) {
            return (item.name && item.name.indexOf("КУП") === 0) ||
                   item.ref_key === SPECIAL_DEPT_REF_KEY;
          })
          .map(function(item) { return item.name; });
      } else {
        choices = data.map(function(item) { return item.full_name; });
      }

      var updated = updateFormQuestion(form, listConfig.questionTitle, choices);
      Logger.log(updated
        ? "✅ Обновлен: " + listConfig.questionTitle + " (" + choices.length + ")"
        : "⚠️ Не найден: " + listConfig.questionTitle
      );

    } catch (e) {
      Logger.log("❌ Ошибка " + listConfig.questionTitle + ": " + e);
    }
  });
}

function updateFormQuestion(form, questionTitle, choices) {
  var items = form.getItems();

  for (var i = 0; i < items.length; i++) {
    if (items[i].getTitle() === questionTitle) {
      var itemType = items[i].getType();

      try {
        if (itemType === FormApp.ItemType.LIST) {
          items[i].asListItem().setChoiceValues(choices);
          return true;
        } else if (itemType === FormApp.ItemType.MULTIPLE_CHOICE) {
          items[i].asMultipleChoiceItem().setChoiceValues(choices);
          return true;
        } else if (itemType === FormApp.ItemType.CHECKBOX) {
          items[i].asCheckboxItem().setChoiceValues(choices);
          return true;
        }
      } catch (e) {
        Logger.log("❌ Ошибка вопроса '" + questionTitle + "': " + e);
        return false;
      }
    }
  }
  return false;
}


// ============================================================
// Утилиты и настройка
// ============================================================

/**
 * Выводит все вопросы формы (для отладки)
 */
function listAllQuestions() {
  var form = FormApp.getActiveForm();
  var items = form.getItems();

  Logger.log("=== Все вопросы ===");
  for (var i = 0; i < items.length; i++) {
    Logger.log(i + ". '" + items[i].getTitle() + "' | " + items[i].getType());
  }
}

/**
 * Настраивает триггеры:
 * - onFormSubmit: при отправке формы → PostgreSQL
 * - updateAllLists: каждые 6 часов обновляет списки в форме
 */
function setupTriggers() {
  // Удаляем старые триггеры
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) {
    ScriptApp.deleteTrigger(triggers[i]);
  }

  // Триггер на отправку формы
  ScriptApp.newTrigger('onFormSubmit')
    .forForm(FormApp.getActiveForm())
    .onFormSubmit()
    .create();

  // Автообновление списков каждые 6 часов
  ScriptApp.newTrigger('updateAllLists')
    .timeBased()
    .everyHours(6)
    .create();

  Logger.log("✅ Триггеры настроены: onFormSubmit + updateAllLists (6ч)");
}
