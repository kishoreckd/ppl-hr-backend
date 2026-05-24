# TeamPilot Backend

A FastAPI backend for TeamPilot, an HRMS and workforce operating system. The existing organizational chart module remains available as a feature, while the HRMS modules use PostgreSQL with SQLAlchemy 2.x and Alembic.

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
alembic upgrade head
python run.py
```

Then visit:

- API: `http://127.0.0.1:5002`
- Swagger: `http://127.0.0.1:5002/docs`

## Seed users

Seed users are created on startup if missing:

- Admin: `Admin@cxontology.com` / `Admin@123`
- Manager: `manager@cxontology.com` / `Manager@123`
- Employee: `employee@cxontology.com` / `Employee@123`

## Tests

```bash
python -m pytest -q
```

## Notes

- TeamPilot HRMS modules use PostgreSQL/SQLAlchemy models in `app/models/hr.py`.
- Org chart routes still use the existing MongoDB structure under `app/routes/char_routes.py`.
