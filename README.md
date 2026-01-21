# HomeStuff

HomeStuff is a Flask + PostgreSQL web application for managing household inventory by storage areas (fridge, pantry, garage, etc.). Items track on-hand quantity, minimum thresholds, and vendor preferences. A restock list surfaces items below their minimums and any manually added reminders, grouped by store to help build shopping lists.

**Features:**
- Multi-user authentication with user-isolated data
- Vendor management
- Storage area organization
- Item tracking with minimum quantity alerts
- Restock list generation and manual entry management
- Shopping list grouped by vendor

## Tech stack
- Flask 3 + Flask-SQLAlchemy + Flask-Login
- PostgreSQL (Railway-friendly)
- Flask-Migrate for schema migrations
- Werkzeug for password hashing

## Quick start
1. Create and activate a virtual env (example):
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy environment template and set values:
   ```bash
   cp .env.example .env
   ```
   - `DATABASE_URL` should point to your Postgres instance.
   - `SECRET_KEY` can be any random string (required for sessions).
4. Initialize the database (after configuring `DATABASE_URL`):
   ```bash
   flask db upgrade
   ```
5. Run the application:
   ```bash
   flask --app wsgi run --debug
   ```
6. Navigate to `http://127.0.0.1:5000` and register a new account.

## Authentication
The app uses Flask-Login for session-based authentication. All data is user-scoped - each user has their own vendors, storage areas, items, and restock entries.

**Auth routes:**
- `/auth/register` - Create a new account (username, email, password)
- `/auth/login` - Sign in with username and password
- `/auth/logout` - Sign out

## Core concepts
- **Users**: Each user has isolated data - cannot see other users' inventories.
- **Storage Areas**: Named locations (Fridge, Pantry) and optional default vendor/store.
- **Items**: Belong to a storage area, optional vendor override, track `minimum_quantity` and `on_hand`. Adjust quantities via delta updates.
- **Restock list**: Combines items below minimum with manual reminders. Shopping view is grouped by vendor/store.

## API sketch
All API routes require authentication via session cookies.

- `GET /health` – simple health check.
- `GET /storage-areas` – list areas with items (user-scoped).
- `POST /storage-areas` – create `{name, vendor_id?}`.
- `PATCH /storage-areas/<id>` – rename or set vendor.
- `DELETE /storage-areas/<id>` – remove area and items.
- `GET /items` – list items, optional `?storage_area_id=`.
- `POST /items` – create `{name, storage_area_id, minimum_quantity, on_hand, vendor_id?}`.
- `PATCH /items/<id>` – update fields or move to another area.
- `POST /items/<id>/adjust` – adjust `on_hand` by `delta` (positive or negative).
- `DELETE /items/<id>` – delete item.
- `GET /restock` – restock snapshot: auto-below-min items, manual entries, grouped shopping view.
- `POST /restock/manual` – add manual entry `{name, vendor_id?, storage_area_id?, reason?}`.
- `POST /restock/<id>/resolve` – mark a manual entry resolved.
- `DELETE /restock/<id>` – remove a manual entry.

## Railway notes
- Set `DATABASE_URL` env var to the Railway Postgres connection string.
- Typical start command: `gunicorn wsgi:app` (Railway default port env var is honored by Flask).
- Add a migration step to your deploy pipeline if schema changes occur.
