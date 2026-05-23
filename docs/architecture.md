# Architecture Overview

## Project structure

- `run.py` — application entrypoint using Uvicorn.
- `app/main.py` — FastAPI app setup and route registration.
- `app/config.py` — environment settings using Pydantic Settings.
- `app/database.py` — MongoDB connection wrapper using Motor.
- `app/routes/` — API routes for users and charts.
- `app/schema/` — Pydantic request/validation models.
- `app/models/` — Pydantic data models with MongoDB ObjectId support.
- `app/services/` — auth helper functions.
- `app/utils/` — JWT creation and verification.

## Current database implementation

- The backend currently uses MongoDB for persistence.
- Database connection is configured in `app/database.py`.
- `app/routes/user_routes.py` and `app/routes/char_routes.py` access the database via `app.database.get_db()`.

### MongoDB collections

- `users`
- `charts`

### Data models

- `ChartModel` — represents organizational chart nodes, including `department` and `employee` types.
- `UserModel` — current user model for MongoDB documents with `ObjectId` support.

## Authentication

- JWT access tokens are created with `app.utils.jwt.create_access_token`.
- Share tokens are created with `app.utils.jwt.create_share_token`.
- Google OAuth verification uses `google.oauth2.id_token`.
- Additional bearer token protection is enforced by `verify_BEARER_TOKEN` in `app.schema.user_schema.py`.

## Notes on PostgreSQL

- The `.env` file includes optional PostgreSQL/Aiven settings, but the app code has not been migrated to PostgreSQL yet.
- A full PostgreSQL migration would require rewriting the database layer and MongoDB-specific route logic.
