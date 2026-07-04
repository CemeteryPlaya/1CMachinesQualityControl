# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Telegram bot + Flask Mini App for vehicle/special-equipment quality control (inspection checklists and maintenance reports). It is a thin front-end over a **1C** ERP system (Russian accounting/ERP): reference data is pulled from 1C via OData, and completed forms are pushed back into 1C as documents. PostgreSQL is used as a local cache + submission store. The UI is multilingual (ru/en/kk/uz). Code comments and most domain strings are in Russian.

## Commands

```bash
# Run the whole stack (app + Postgres) — note the non-standard compose filename
docker compose -f docker_compose.yml up --build

# Run locally (requires a reachable Postgres and a populated .env)
pip install -r requirements.txt
python main.py

# Smoke tests (no DB required)
python tests/smoke_test.py
```

- Tests: `tests/smoke_test.py` (standalone, assert-based; no pytest). No linter/formatter configured.
- `main.py` is the single entry point: waits for Postgres and initializes the DB, does an initial 1C sync, starts the web server (waitress; Flask dev server as fallback) in a daemon thread on `0.0.0.0:5000`, starts the daily-digest scheduler and the 1C sync worker, then runs aiogram bot polling in the main asyncio loop.
- All configuration is via environment variables (loaded with `python-dotenv` from `.env`). Key groups: OData URLs + credentials, `BOT_TOKEN`, `WEB_APP_URL`, `DATABASE_URL`, `GSHEETS_API_KEY`, `NOMENCLATURE_PARENT_REF_KEY`; security/ops: `FLASK_SECRET_KEY`, `ADMIN_USERNAME`/`ADMIN_PASSWORD` (first superadmin; random password logged if unset), `REQUIRE_TELEGRAM_AUTH` (default on — submits must carry valid Telegram initData), `MAX_UPLOAD_MB` (default 25), `ODATA_SYNC_TTL_SECONDS` (default 300), `DAILY_DIGEST_TIME` (default 18:00), `PHOTO_RETENTION_DAYS` (0 = keep forever), `DB_POOL_MAX`, `TZ` (compose default Asia/Tashkent). The bot polls Telegram, so `WEB_APP_URL` must be a public HTTPS URL (ngrok in dev — see `ngrok.exe`) that points back at the Flask server.

## Architecture

The app runs **two services in one process** (`main.py`):

1. **Telegram bot** (`bot_handlers.py`, aiogram FSM) — a navigation menu only. Flow: `/start` → choose language → choose category (Checklists / Maintenance report) → choose vehicle type → bot replies with a WebApp button whose URL carries the user's choices as query params: `{WEB_APP_URL}?lang=&form_type=&tg_user_id=`. The bot never collects form data itself.
2. **Flask Mini App** (`app_routes.py`, blueprint `app_bp`) — renders the form, exposes dropdown APIs, and accepts submissions. Opened inside Telegram's WebApp container.

### Form types

There are **5 form types**, mapped in `app_routes.py: FORM_CONFIG_MODULES`:

| `form_type` | Module | Meaning |
|------------|--------|---------|
| `lv` | `lv_form_config.py` | Passenger vehicle, on-site |
| `lv_oa` | `lv_oa_form_config.py` | Passenger vehicle, off-site |
| `sv` | `sv_form_config.py` | Special equipment, on-site |
| `sv_oa` | `sv_oa_form_config.py` | Special equipment, off-site |
| `to` | `to_form_config.py` | Maintenance report (ТО) |

Each `*_form_config.py` exports `get_form_config(lang)` returning a list of field dicts (`type`: header/text/select/date/number/textarea/repeater/hidden/readonly, etc.). `app_routes.py: index()` dynamically `import_module`s the right config and renders `templates/index.html`, which builds the form from this config. The client logic lives in `static/script.js` (fetches dropdown data, handles `repeater` table rows, submits JSON).

### Request/data flow for a submission

1. Frontend POSTs JSON to `/submit` (checklists) or `/submit_to` (maintenance).
2. Backend **resolves UIDs**: the form sends PostgreSQL integer IDs (e.g. `machine_uid`, `driver_uid`, `department_uid`). The route looks each up via `database.py`, replacing the field with a human-readable string and adding a `*_ref_key` (the 1C GUID). This ref_key resolution is the central reason reference data is cached locally.
3. Saved to PostgreSQL (`inspections`, `maintenance_reports`, or `daily_inspections`), and a mileage row is appended to `mileage_history`.
4. The 1C push is enqueued into `one_c_sync_queue` and processed by `sync_worker.py` (retries with backoff; status observable via `synced`/`attempts`/`last_error`). A Telegram confirmation is sent in a background thread via the Bot API HTTP endpoint. Submissions require a valid signed Telegram `init_data` (`telegram_auth.py`) unless `REQUIRE_TELEGRAM_AUTH=0`.

### Layers

- **`odata_service.py`** — all 1C OData I/O. For each entity there is a `sync_*`/`fetch_*` pair (GET from 1C → upsert into Postgres; falls back to cached Postgres data if `ODATA_URL` is unset or 1C is unreachable) and, for documents, a `post_*_to_1c` (builds the 1C document payload and POSTs it). Vehicle category (`lv` vs `sv`) is derived from the 1C field `бсо_ВидМашины` by `_classify_vehicle_type`.
- **`database.py`** — psycopg (PostgreSQL) access layer. `init_db()` creates all tables idempotently and runs inline `ALTER TABLE … EXCEPTION WHEN duplicate_column` migrations. Each function opens and closes its own connection. Inspection fields not in `_INSPECTION_META_KEYS` are stored in a JSONB `results` column; keys in that set go to dedicated columns.
- **`translations.py`** — i18n dictionaries (`BOT_MESSAGES`, `FIELD_LABELS`, `SECTION_HEADERS`, `LANGUAGE_NAMES`) plus `get_bot_message` / `get_translation`. Supported langs: `ru`, `en`, `kk`, `uz` (default `ru`).
- **`bot_instance.py`** — single shared `aiogram.Bot` + `BOT_TOKEN`, imported by both bot and Flask sides (Flask uses the raw token to call the Telegram HTTP API directly for confirmations).

### Schema bootstrapping (single source)

The schema lives **only** in `database.py: init_db()` (idempotent CREATEs + inline `ALTER … EXCEPTION WHEN duplicate_column` migrations), executed on every start with a wait-for-Postgres retry loop. There is no separate SQL bootstrap file anymore.

### Google Sheets / Apps Script integration (secondary)

`AppsScript.js` is Google Apps Script (deployed in Google, not run here). It forwards Google Form/Sheet responses to the Flask endpoint `POST /api/inspection`, authenticated with header `X-API-Key` matching `GSHEETS_API_KEY`. These submissions skip UID resolution (`save_inspection_from_sheets`).

## Admin panel

`/admin` (blueprint in `admin_routes.py`, templates in `templates/admin/`, styles `static/admin.css`). Login: username/password or auto-login from the Telegram Mini App (signed initData → active admin with matching `telegram_user_id`; bot command `/admin`). Per-admin flags: `can_view_reports`, `can_view_history`, `receive_instant_notifications`, `receive_daily_digest`, `is_superadmin`. Admin POST forms carry a session CSRF token (`_csrf`). `/photos/<path>` requires an active admin session. `notifications.py` sends instant pushes and the daily digest (dedup via `app_state` claim).

## Notes

- The compose file is `docker_compose.yml`, not `docker-compose.yml`, so the `-f` flag is required.
- A failed 1C post does **not** fail the user submission — the record is already in Postgres and the queue retries; inspect `one_c_sync_queue` for stuck tasks.
- `ref_key` everywhere refers to a 1C entity GUID; integer `id` refers to the local Postgres row.
- Web-app UI strings live in `translations.py: WEBAPP_STRINGS` (rendered into `window.TRANSLATIONS`); don't add inline per-language dicts to `templates/index.html`.
- Reference-data endpoints (`/api/machines`, …) sync from 1C at most once per `ODATA_SYNC_TTL_SECONDS` and serve the local cache otherwise.
