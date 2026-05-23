# PPL HR Backend

A FastAPI backend for an organizational chart and user authentication system.

## Project documentation

See the `docs/` folder for setup instructions, API details, and architecture notes.

- `docs/README.md`
- `docs/setup.md`
- `docs/api.md`
- `docs/architecture.md`
- `docs/postman_collection.json`

## Quick start

```bash
python -m pip install -r requirements.txt
python run.py
```

Then visit `http://127.0.0.1:5002`.

## Notes

- The backend currently uses MongoDB/Motor.
- Optional PostgreSQL/Aiven environment fields exist in `.env`, but the app has not been migrated to PostgreSQL.
