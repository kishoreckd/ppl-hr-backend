# PPL HR Backend Documentation

This folder contains documentation for the `ppl-hr-backend` FastAPI project.

## Contents

- `setup.md` — environment setup, dependency installation, and startup instructions.
- `api.md` — documented API endpoints and request examples.
- `architecture.md` — project architecture, data model overview, and current database implementation.
- `postman_collection.json` — Postman import collection for API testing.

## Notes

This backend is currently implemented using MongoDB/Motor for persistence. The `.env` file also includes optional PostgreSQL/Aiven connection settings, but the application code still requires a migration to use PostgreSQL.
