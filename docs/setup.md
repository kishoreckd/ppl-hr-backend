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

Required values:

- `BEARER_TOKEN`
- `JWT_SECRET`
- `MONGO_URI`
- `DB_NAME`
- `DOMAIN_URL`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

Optional PostgreSQL/Aiven values (currently not used by application code):

- `POSTGRES_URI`
- `POSTGRES_DB`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `PGSSLMODE`

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
