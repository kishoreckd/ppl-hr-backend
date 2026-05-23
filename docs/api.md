# API Documentation

## Base URLs

- `http://127.0.0.1:5002/users`
- `http://127.0.0.1:5002/chart`

## Authentication

- `Authorization: Bearer <BEARER_TOKEN>` is required for some endpoints.
- `User_Token` header is required for chart endpoints that verify JWT access tokens.
- `Guest_token` header is required for shared chart access when using guest sessions.

## Postman variables

The included Postman collection uses these variables:

- `base_url` — API base URL, e.g. `http://127.0.0.1:5002`
- `bearer_token` — internal bearer token from `BEARER_TOKEN`
- `user_token` — JWT access token returned after login or Google auth
- `share_token` — share token returned after login or Google auth
- `guest_token` — guest JWT token returned by `/users/check/google`
- `uid` — chart UID
- `hashid` — chart node hash ID
- `parent_hashid` — new parent node hash ID for move operations

## Users routes

### POST `/users/auth/google`

Authenticate or register a user from Google OAuth.

Request body:

```json
{
  "token": "<google-oauth-token>"
}
```

Response:

- `access_token`
- `share_token`
- `expires_in`

### POST `/users/check/google`

Validate a Google OAuth token and return a guest token.

Request body:

```json
{
  "token": "<google-oauth-token>"
}
```

Response:

- `guest_token`
- `userdata`
- `expires_in`

### POST `/users/signup`

Register a new email/password user.

Headers:

- `Authorization: Bearer <BEARER_TOKEN>`

Request body:

```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "StrongPassword123"
}
```

Response:

- `access_token`
- `share_token`
- `expires_in`

## Chart routes

### GET `/chart/`

Retrieve paginated charts for the authenticated user.

Query parameters:

- `page` (int)
- `limit` (int)

Headers:

- `User_Token: <JWT access token>`

Response fields:

- `nodes`
- `page`
- `limit`

### Notes

- The chart routes currently work with MongoDB documents stored in the `charts` collection.
- Responses include serialized `ObjectId` fields and computed counts for departments and employees.

## Postman Collection

Import the collection at `docs/postman_collection.json` into Postman for ready-to-use requests.
