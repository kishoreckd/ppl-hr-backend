# Setup Instructions

## Requirements

- Python 3.10+
- pip
- MongoDB or a MongoDB-compatible connection URI
- Optional: Aiven PostgreSQL settings for future migration

## Install dependencies

```bash
python -m pip install -r requirements.txt
```

## Environment variables

Copy the `.env` file and update values as needed.

### Required application keys

- `BEARER_TOKEN` — internal bearer token used by protected signup/login/profile endpoints.
- `JWT_SECRET` — secret string used to sign JWT access, guest, and share tokens.
- `MONGO_URI` — MongoDB connection URI (e.g. `mongodb://localhost:27017`).
- `DB_NAME` — MongoDB database name.
- `DOMAIN_URL` — application base domain, used for image URL generation.
- `GOOGLE_CLIENT_ID` — Google OAuth client ID.
- `GOOGLE_CLIENT_SECRET` — Google OAuth client secret.

### Optional PostgreSQL/Aiven keys

The app currently uses MongoDB, but the `.env` file also includes optional PostgreSQL/Aiven keys for future migration.

- `POSTGRES_URI` — full PostgreSQL connection string (e.g. Aiven URI).
- `POSTGRES_DB` — PostgreSQL database name.
- `POSTGRES_HOST` — PostgreSQL host.
- `POSTGRES_PORT` — PostgreSQL port.
- `POSTGRES_USER` — PostgreSQL username.
- `POSTGRES_PASSWORD` — PostgreSQL password.
- `PGSSLMODE` — PostgreSQL SSL mode (e.g. `require`).

### Example `.env` keys

```env
BEARER_TOKEN="<your bearer token>"
JWT_SECRET="<your jwt secret>"
MONGO_URI="mongodb://<host>:<port>"
DB_NAME="<your-db-name>"
DOMAIN_URL="https://example.com"
GOOGLE_CLIENT_ID="<google-client-id>"
GOOGLE_CLIENT_SECRET="<google-client-secret>"

POSTGRES_URI="postgres://<user>:<pass>@<host>:<port>/<db>?sslmode=require"
POSTGRES_DB="<db>"
POSTGRES_HOST="<host>"
POSTGRES_PORT="<port>"
POSTGRES_USER="<user>"
POSTGRES_PASSWORD="<pass>"
PGSSLMODE="require"
```

## Run the application

Start the FastAPI server using the project entrypoint:

```bash
python run.py
```

The application will run locally on `http://127.0.0.1:5002` by default.

## Developer notes

- The app loads environment variables from `.env` using `python-dotenv`.
- FastAPI routes are registered in `app/main.py`.
- MongoDB connection is created in `app/database.py`.
