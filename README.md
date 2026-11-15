# Backbone API

The backend of [Backbone](https://github.com/angeLoon77/Backbone-APP), a workout tracker for Android and desktop. A Flask REST API with token authentication that stores accounts, exercises and personal records (PRs) in PostgreSQL (Neon).

> 🚧 **Status:** in development. Built solo with Python and Flask.

## Why it exists

The Backbone app never talks to the database directly. A database connection string bundled into an Android app could be extracted by anyone, so only this API holds the credentials. The app signs in through the API, receives a signed token and sends it with each request. The API reads the user from the token, so a user can only see and change their own data.

```
Backbone app (Flet)  →  Backbone API (Flask)  →  PostgreSQL (Neon)
```

## Tech stack

- **Python** and **Flask**
- **PostgreSQL** on **Neon**, accessed with **psycopg2**
- **bcrypt** (password hashing)
- Hosted on **Render**

## Authentication

1. `POST /register` creates an account and `POST /login` returns a signed token.
2. Every other route expects the header `Authorization: Bearer <token>`.
3. A missing, invalid or expired token gets a `401`. The app reacts by sending the user back to the login screen.

Errors are JSON in the form `{"error": "message"}`.

## Endpoints

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/register` | no | Create an account. Body: `username`, `password`. `201` with `{"user_id": ...}`, or `400` / `409` with an error message |
| POST | `/login` | no | Body: `username`, `password`. `200` with `{"token": "..."}`, or `401` if the credentials are wrong |
| GET | `/exercises` | token | The exercise list: `id`, `name` and `muscle_group` for each one |
| GET | `/prs` | token | Your current PR for each exercise, keyed by exercise name (`weight`, `reps`) |
| POST | `/prs` | token | Log a PR. Body: `exercise_id`, `weight`, `reps`, `date` (`YYYY-MM-DD`). `201` with `{"pr_id": ...}`, or `400` if the data is invalid |
| GET | `/prs/group/{muscle_group}` | token | Your PRs in one muscle group: a list with `name`, `weight`, `reps` and `date` |
| DELETE | `/exercises/{exercise_id}/prs` | token | Delete all your PRs of one exercise. `200` with `{"deleted": <count>}` |
| POST | `/parser-failures` | token | Store a workout text the app's parser couldn't understand. See [Parser feedback](#parser-feedback) |

## Database

| Table | Purpose |
| --- | --- |
| `users` | Accounts |
| `exercises` | The exercise list, with the muscle group of each exercise |
| `prs` | Personal records, linked to a user and an exercise |
| `parser_failure` | Workout texts the app's parser couldn't understand |

Tables are created with `CREATE TABLE IF NOT EXISTS` functions in the data layer, for example `create_parser_failure_table()`. Run them once at setup, not on every request.

## Running locally

You need Python 3 and a PostgreSQL database (a free Neon project works).

1. Clone the repo and install the dependencies:

   ```bash
   git clone https://github.com/angeLoon77/backbone-api.git
   cd backbone-api
   python -m venv venv
   source venv/bin/activate   # on Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the project root and **never commit it**:

   ```
   DATABASE_URL=your Neon connection string
   SECRET_KEY=a long random string used to sign tokens
   ```

3. Create the tables by running the `create_..._table()` functions once.

4. Start the server:

   ```bash
   python app.py
   ```

## Trying it

Bash syntax, with `BASE_URL` pointing to your local server or to the hosted instance:

```bash
BASE_URL=http://localhost:5000

# create an account, then log in (the response has the token)
curl -X POST "$BASE_URL/register" -H "Content-Type: application/json" -d '{"username": "demo", "password": "demo123"}'
curl -X POST "$BASE_URL/login" -H "Content-Type: application/json" -d '{"username": "demo", "password": "demo123"}'

# use the token on the other routes
TOKEN="paste-the-token-here"
curl "$BASE_URL/exercises" -H "Authorization: Bearer $TOKEN"
curl "$BASE_URL/prs" -H "Authorization: Bearer $TOKEN"
```

## Parser feedback

`POST /parser-failures` receives the text of workouts that the app's parser couldn't fully understand, so the parser and the exercise list can be improved. The app calls it in the background and ignores the result, so a failure here never affects the user. The reasons the app sends (`unknown_exercise: <name>`, `no_exercises`, `no_sets: <name>`, `invalid_date` and `parse_error: ...`) are described in the [app's README](https://github.com/angeLoon77/Backbone-APP#parser-feedback).

```
POST /parser-failures
Authorization: Bearer <token>
Content-Type: application/json

{"raw_text": "11/11\n\nxyzabc\n\n10x 50kg", "reason": "unknown_exercise: xyzabc"}
```

| Status | Body | When |
| --- | --- | --- |
| `201` | `{"logged": true}` | The report was saved |
| `400` | `{"error": "raw_text and reason must be strings"}` | A field is missing or isn't a string |
| `400` | `{"error": "raw_text and reason must not be empty"}` | A field is empty or only whitespace |
| `400` | `{"error": "invalid characters"}` | A field contains a null character (`\x00`), which PostgreSQL rejects |
| `401` | `{"error": "Unauthorized"}` | Missing or invalid token |
| `413` | `{"error": "payload too large"}` | `raw_text` is over 10,000 characters or `reason` is over 200 |
| `500` | `{"error": "internal error"}` | The insert failed. The details go to the server log, never to the client |

The limits are the `MAX_RAW_TEXT` (10,000) and `MAX_REASON` (200) constants. They are checked in the route, before the database, and `MAX_RAW_TEXT` matches the app's own `MAX_WORKOUT_LENGTH`.

### The `parser_failure` table

```sql
CREATE TABLE IF NOT EXISTS parser_failure
(
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    raw_text TEXT NOT NULL,
    reason TEXT NOT NULL,
    date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
)
```

| Column | Meaning |
| --- | --- |
| `id` | Report id |
| `user_id` | Who sent it. Deleting the user deletes their reports (`ON DELETE CASCADE`) |
| `raw_text` | The text exactly as the user pasted it |
| `reason` | Why the app flagged it |
| `date` | When the report was received. It is **not** the date of the workout |

`log_parser_failure(user_id, raw_text, reason)` inserts a row with parameterized values. There is no index on `date` on purpose: the table stays small and is meant to be cleaned periodically. If the cleanup ever gets slow, add one with `CREATE INDEX idx_parser_failure_date ON parser_failure (date)`.

To read the latest reports:

```sql
SELECT date, reason, raw_text
FROM parser_failure
ORDER BY date DESC
LIMIT 20;
```

### Privacy

`raw_text` is content written by the user and can include personal notes. It is only stored in this table, only when the app couldn't fully parse a workout, and it is removed together with the user. Automatic deletion of reports older than 30 days is planned but not implemented yet.

## Deploying

The host runs the last deployed commit, so a new route only exists after a new deploy finishes. To check that a route is live, open it in a browser:

- `405 Method Not Allowed` means the route exists (the browser sends a GET and the route only accepts POST).
- `404` means the old code is still running.

## Roadmap

- [x] Flask API with token authentication (register, login, PRs, exercises)
- [x] Routes for PRs by muscle group and for deleting all PRs of an exercise
- [x] Hosted on Render
- [x] Parser feedback: `POST /parser-failures` and the `parser_failure` table
- [ ] Monthly cleanup of parser feedback older than 30 days (`DELETE FROM parser_failure WHERE date < now() - interval '30 days'`)
- [ ] Limit how many parser reports one user can send per day
- [ ] Routes for the workout log, so it can move from the device's JSON file to the database

## License

All rights reserved. This code is public for viewing and evaluation only.