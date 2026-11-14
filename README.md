# Advanced Project & Team Management System – Backend

FastAPI + SQLAlchemy 2.0 + Alembic + JWT auth + role-based access control.
Built for the **Backend Developer** track of the assignment.

## Tech stack
FastAPI · SQLAlchemy ORM · Alembic migrations · PostgreSQL (SQLite for quick start/tests) ·
Pydantic v2 · PyJWT · bcrypt · pytest · Docker

## Folder structure
```
app/
├── main.py            # app factory, CORS, request logging, startup seeding
├── exceptions.py      # custom exceptions + global handlers (one error format)
├── core/              # config (env vars), security (JWT/bcrypt), logging, permissions, pagination
├── db/                # Base, engine/session, seed (roles + first admin)
├── models/            # Role, User, Project, ProjectMember, Task, TaskComment, ActivityLog
├── schemas/           # Pydantic request/response models
├── services/          # business logic + access rules (routers stay thin)
└── api/
    ├── deps.py        # get_current_user, require_roles, require_permission
    └── v1/            # auth, users, projects, tasks, dashboard routers
alembic/               # migrations (0001 creates schema and seeds roles)
tests/                 # pytest + FastAPI TestClient (in-memory SQLite)
docs/                  # ER_DIAGRAM.md, postman_collection.json
```

## Setup
```bash
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                # edit SECRET_KEY and DATABASE_URL
alembic upgrade head                # create tables + seed roles
uvicorn app.main:app --reload
```
- Swagger UI: http://localhost:8000/docs  ·  ReDoc: http://localhost:8000/redoc
- First admin (created on startup from `.env`): `admin@example.com` / `Admin@12345` – **change it**.
- In Swagger click **Authorize** and log in with email (or username) + password.

### PostgreSQL
Create a database, then set `DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/pm_db`
and run `alembic upgrade head`.

### Docker
```bash
docker compose up --build      # API on :8000 with PostgreSQL, migrations run automatically
```

### Tests
```bash
pytest -v
```

## Roles & permissions
| Capability | Admin | Project Manager | Team Member |
|---|:-:|:-:|:-:|
| Manage users, roles, permissions | ✅ | – | – |
| List users | ✅ | ✅ | – |
| Create project | ✅ | ✅ | – |
| Edit/delete project, manage members | ✅ (all) | ✅ (own projects) | – |
| View project | ✅ (all) | ✅ (member) | ✅ (member) |
| Create/edit/delete/assign tasks | ✅ | ✅ (projects they belong to) | – |
| Update status of own assigned task | ✅ | ✅ | ✅ |
| Comment on tasks | ✅ | ✅ | ✅ (projects they belong to) |

Self-registration always creates a **Team Member**. Only an admin can create other roles.
Each role has a `permissions` list (e.g. `task:create`) stored in the `roles` table; the admin can
edit it via `PATCH /api/v1/roles/{id}/permissions`. Endpoints check the permission
(`require_permission`) and then object-level rules (membership/ownership) in `services/access.py`.

## API overview (`/api/v1`)
| Area | Endpoints |
|---|---|
| Auth | `POST /auth/register` · `POST /auth/login` (form) · `POST /auth/login/json` · `GET /auth/me` |
| Users | `GET/POST /users` · `GET/PATCH /users/{id}` · `PATCH /users/me` · `PATCH /users/{id}/status` · `PATCH /users/{id}/role` · `GET /roles` · `PATCH /roles/{id}/permissions` |
| Projects | `GET/POST /projects` · `GET/PATCH/DELETE /projects/{id}` · `POST /projects/{id}/members` · `DELETE /projects/{id}/members/{user_id}` · `GET /projects/{id}/stats` · `GET /projects/{id}/activity` |
| Tasks | `GET/POST /tasks` · `GET /tasks/me` · `GET/PATCH/DELETE /tasks/{id}` · `PATCH /tasks/{id}/status` · `GET /tasks/{id}/activity` |
| Comments | `GET/POST /tasks/{id}/comments` · `DELETE /tasks/{id}/comments/{comment_id}` |
| Dashboard | `GET /dashboard` |

**List endpoints** return `{items, total, page, size, pages}` and accept `page`, `size`.
**Task filters:** `project_id, status, priority, assignee_id, search, overdue, sort_by (created_at|due_date), order (asc|desc)`.

**Error format** (all errors): `{"error": {"code": "...", "message": "...", "details": ...}}`

## Business rules
- Task deadlines cannot be in the past (when set/changed) and must fall inside the project's start/end dates.
- Assignees must be active members of the task's project.
- Project progress = completed tasks ÷ total tasks × 100.
- Removing a member un-assigns their tasks in that project; the owner cannot be removed.
- Every create/update/delete/assign/comment writes an `activity_logs` row (who, what, when, before/after values).
- Users are deactivated rather than deleted; deactivated users cannot log in or use existing tokens.

## Requirement checklist
Auth (register/login/JWT/hashing/RBAC) ✅ · User management ✅ · Project APIs + stats ✅ · Task APIs
(CRUD, assign, status/priority, filter/search, deadline validation, "my tasks") ✅ · Comments & activity
logs ✅ · SQLAlchemy + Alembic ✅ · Validation & exception handling ✅ · Pagination/filtering ✅ ·
Env config ✅ · Modular structure ✅ · Swagger/OpenAPI ✅ · Logging (console + `logs/app.log`) ✅ ·
Docker ✅ · Tests ✅ · Postman collection ✅ · ER diagram ✅

## Still to do before submitting
GitHub repo link, demo video, and screenshots (Swagger UI, test run, DB tables) are yours to add.
