# DevTrack

A minimal Django backend for tracking engineering issues: engineers (reporters) file issues, set priorities, and track status. Data is stored in two JSON files, and every endpoint is testable in Postman.

## Tech

Python 3.12, Django 6.1. No database and no third-party packages beyond Django.

## How to run

```powershell
git clone https://github.com/abhinavk0220/DEVTRACK.git
cd DEVTRACK
python -m venv myenv
myenv\Scripts\activate
pip install django
python manage.py runserver
```

The API is served at `http://127.0.0.1:8000/`.

- `reporters.json` and `issues.json` are created in the project root on the first successful POST. You don't need to create them.
- Django prints a warning about unapplied migrations. It is harmless here, because the project doesn't use Django's database.
- All URLs end with a trailing `/`. Django does not redirect POST requests, so `/api/issues` (no slash) will fail.

## Project structure

```
devtrack/
  manage.py
  devtrack/
    settings.py      # registered issues in installed apps
    urls.py          # mounts issues.urls under /api/
  issues/
    models.py        # OOP classes: BaseEntity, Reporter, Issue, CriticalIssue, LowPriorityIssue
    storage.py       # JSON file read/write helpers
    views.py         # request handling only
    urls.py          # reporters/ and issues/ routes
  screenshots/       # Postman evidence
```

## Data model

**Reporter**: `id`, `name`, `email`, `team`

**Issue**: `id`, `title`, `description`, `status`, `priority`, `reporter_id`

- `status` is one of: `open`, `in_progress`, `resolved`, `closed`
- `priority` is one of: `low`, `medium`, `high`, `critical`
- One reporter can file many issues. `reporter_id` is stored on the issue.

## Endpoints

| Method | URL | What it does |
|---|---|---|
| POST | `/api/reporters/` | Create a reporter |
| GET | `/api/reporters/` | List all reporters |
| GET | `/api/reporters/?id=1` | Get one reporter by ID |
| POST | `/api/issues/` | Create an issue |
| GET | `/api/issues/` | List all issues |
| GET | `/api/issues/?id=1` | Get one issue by ID |
| GET | `/api/issues/?status=open` | List issues with the given status |

### Status codes

| Code | Meaning |
|---|---|
| 200 | Successful GET |
| 201 | Record created |
| 400 | Bad input: invalid JSON, wrong type, failed validation, non-integer `id`, invalid `status` filter, unknown `reporter_id` |
| 404 | `?id=` matched no record |
| 405 | HTTP method not allowed on this URL |

Errors from the API views have the shape {"error": "<message>"}. A 405 returns an empty body.

### Create a reporter

`POST /api/reporters/`

```json
{ "name": "Asha Rao", "email": "asha@example.com", "team": "backend" }
```

Response `201`:

```json
{ "id": 1, "name": "Asha Rao", "email": "asha@example.com", "team": "backend" }
```

### Create an issue

`POST /api/issues/`

```json
{
  "title": "Login button not working on mobile",
  "description": "Users on iOS 17 cannot tap the login button",
  "status": "open",
  "priority": "critical",
  "reporter_id": 1
}
```

Response `201`:

```json
{
  "id": 1,
  "title": "Login button not working on mobile",
  "description": "Users on iOS 17 cannot tap the login button",
  "status": "open",
  "priority": "critical",
  "reporter_id": 1,
  "message": "[URGENT] Login button not working on mobile — needs immediate attention"
}
```

Validation failure, `400`:

```json
{ "error": "Title cannot be empty" }
```

Not found, `404`:

```json
{ "error": "Issue not found" }
```

### Query parameter rules

- `?id=` must be an integer, otherwise `400`. No match gives `404`.
- `?status=` must be one of the four valid statuses, otherwise `400`. A typo such as `?status=opne` is reported instead of silently returning an empty list.
- If both are sent, `id` wins and `status` is ignored.

## OOP design

- `BaseEntity` is an abstract base class. `validate()` is abstract, because each entity has different rules. `to_dict()` is concrete, because serialization is identical for every entity.
- Each subclass declares a `FIELDS` allowlist. `to_dict()` returns only those fields, so adding an internal attribute later can never leak into an API response. `BaseEntity` raises `TypeError` at class-definition time if a subclass forgets `FIELDS`.
- `CriticalIssue` and `LowPriorityIssue` subclass `Issue` and override `describe()`. The POST view picks the class from the priority and calls `describe()` without caring which class it received (polymorphism). `medium` and `high` use the base `Issue`.
- `message` is computed from `describe()` for the response and is never written to `issues.json`.

## Design decisions

**Server-generated IDs (main decision).** The server assigns every ID as the highest existing ID plus one. Any `id` sent in a request body is ignored.

Why: if clients chose IDs, two clients could send the same one, a client could overwrite another record by guessing an ID, and no client can know the current maximum while others are writing. The brief's sample request includes `"id": 1`, so this is a deliberate deviation. For the first record the result is identical. After that, a client-sent ID is replaced by the server's, and the response always shows the real ID. The `screenshots/` folder demonstrates this with requests that send a different ID than the one returned.

![Client sent id 1, server returned id 3](screenshots/ISSUES/POST_Issues_System_Generated_IDs-3.png)


Other decisions:

- **Storage is isolated in `storage.py`.** Views never open files. Swapping JSON for a database would change one module.
- **Paths are anchored to `BASE_DIR`**, not the current working directory, so the server works no matter which folder it is started from.
- **Atomic writes.** Data is written to a temporary file and swapped in with `os.replace`. A crash mid-write cannot leave a corrupted JSON file.
- **`max + 1` rather than `len + 1`** for IDs, so IDs stay unique if records are ever removed.
- **Two layers of validation.** The view checks that fields are present and of the right type. The model's `validate()` enforces business rules (non-blank title, allowed status and priority, valid email). This keeps `validate()` from crashing on `null` or numbers.
- **Referential integrity is enforced in the view.** JSON files have no foreign keys, so creating an issue checks that `reporter_id` exists. An unknown reporter returns `400`, not `404`: the endpoint exists, and the problem is the content of the request body. (`422` is another common choice.)
- **CSRF protection is disabled on the API views** (`csrf_exempt`). CSRF defends cookie-based browser sessions. This is a token-less JSON API with no sessions.
- **Logic lives in the model, not the view.** The views parse requests and shape responses. They never inspect names or emails themselves.

## Postman screenshots

Success and failure cases for every endpoint are in [`screenshots/`](screenshots/).

Success, `POST /api/issues/` returns `201`:

![POST issue, 201](screenshots/ISSUES/POST_Issues.png)

Failure, `POST /api/issues/` returns `400`:

![POST issue, 400](screenshots/ISSUES/POST_Invalid_Title_Empty.png)


Success, `GET /api/issues/` returns `200`:

![GET issue, 200](screenshots/ISSUES/GET_Issues.png)

Failure, `GET /api/issues/` returns `400`:

![GET issue, 400](screenshots/ISSUES/GET_Status_Invalid_Status.png)

Success, `POST /api/reporters/` returns `201`:

![POST reporter, 201](screenshots/REPORTERS/POST_Reporters.png)

Failure, `POST /api/reporters/` returns `400`:

![POST reporter, 400](screenshots/REPORTERS/POST_Reporters_Invalid_Email.png)

Success, `GET /api/reporters/` returns `200`:

![GET reporter, 200](screenshots/REPORTERS/GET_Reporters.png)

Failure, `GET /api/reporters/` returns `404`:

![GET reporter, 404](screenshots/REPORTERS/GET_Reporters_Invalid_ID.png)

## Known limitations

- **Race condition.** Two simultaneous writes can both read the same file, and one write overwrites the other. This is acceptable for a learning project, and it is the main reason real systems use a database.
- No update or delete endpoints, because the brief doesn't ask for them.
- The whole file is read on every request, so this will not scale to large datasets.
- `created_at` (optional in the brief) is not implemented.
