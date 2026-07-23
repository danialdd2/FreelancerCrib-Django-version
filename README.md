# Freelancercrib API

A REST API for a freelance marketplace, built with **Django** and **Django REST Framework**. Clients post projects, freelancers submit bids, and the platform handles the whole lifecycle: accepting a bid, completing a project, rating each other afterward, and notifying users along the way.

This is a Django/DRF implementation of a project I originally built with FastAPI, re-architected to use Django's ORM, auth system, and DRF's class-based views.

## FastAPI Version

- GitHub: https://github.com/danialdd2/FreelancerCrib
- Live API Docs: https://freelancercrib.up.railway.app/docs

## Features

- **JWT authentication** — custom DRF authentication backend, signed tokens carrying user role claims
- **Role-based access** — separate permissions for clients, freelancers, and admins
- **Full project lifecycle** — open → in progress (bid accepted) → completed / canceled
- **Bidding** — freelancers submit bids; clients accept one, which auto-rejects the rest
- **Ratings** — clients and freelancers rate each other after a project completes
- **Notifications** — in-app notifications for new bids, accepted bids, completed projects, and new ratings
- **Admin panel endpoints** — promote users to admin, list all users/admins
- **Per-role dashboard** — aggregate stats (open projects, active bids, average rating, etc.) tailored to clients vs. freelancers
- **Auto-generated API docs** — Swagger UI and ReDoc via `drf-spectacular`
- **Dockerized** — one command to run the API + PostgreSQL together
- **Tested** — model and API tests using DRF's `APITestCase`, run automatically via GitHub Actions

## Tech stack

`Django 5.2` · `Django REST Framework` · `PostgreSQL` · `PyJWT` · `drf-spectacular` · `Docker` / `Docker Compose`

## Getting started

```bash
git clone https://github.com/danialdd2/FreelancerCrib-Django.git
cd freelancercrib-django
cp .env.example .env
# edit .env: set real values for DJANGO_SECRET_KEY, JWT_SECRET_KEY, DB_PASS
docker compose up --build
```

The API is now running at `http://127.0.0.1:8000`.

- **Swagger UI:** http://127.0.0.1:8000/api/docs/
- **Django admin site:** http://127.0.0.1:8000/django-admin/ (create a superuser with `docker compose run --rm app python manage.py createsuperuser`)

## Running tests

Against the real Postgres service (via docker-compose):

```bash
docker compose run --rm app python manage.py test
```

Or, locally without docker, against an in-memory SQLite database:

```bash
pip install -r requirements.txt
pytest
```

Tests also run automatically on every push via GitHub Actions (see `.github/workflows/ci.yml`).

## Project structure

Each area of functionality lives in its own Django app:

```
core/           # shared models (User, Project, Bid, Rating, Notification), JWT auth, permissions
authapp/        # login / token endpoint
users/          # registration, profile
projects/       # create/list/update projects, accept bids, complete/cancel
bids/           # submit, list, update, delete bids
ratings/        # submit a rating after project completion
notifications/  # list, mark read, delete notifications
adminpanel/     # admin-only user management
dashboard/      # role-specific aggregate stats
```

## API overview

| Method | Endpoint                                       | Description                          |
|--------|-------------------------------------------------|---------------------------------------|
| POST   | `/user/`                                        | Register a new user                   |
| POST   | `/auth/token/`                                  | Log in, get a JWT                     |
| GET/PUT| `/user/me/`                                     | View/update own profile                |
| GET    | `/user/{id}/`                                   | View a public profile                  |
| GET/POST| `/projects/`                                   | List / create projects                 |
| GET    | `/projects/my/`                                 | Projects owned by the current user     |
| GET/PUT| `/projects/{id}/`                               | View / update a project                |
| PATCH  | `/projects/{id}/bids/{bid_id}/accept/`          | Accept a bid                           |
| PATCH  | `/projects/{id}/complete/`                      | Mark a project completed               |
| PATCH  | `/projects/{id}/cancel/`                        | Cancel a project                       |
| POST/GET| `/projects/{id}/bids/`                         | Submit / list bids on a project        |
| GET    | `/users/me/bids/`                               | Bids submitted by the current user     |
| PUT/DELETE| `/bids/{id}/`                                | Update / withdraw a bid                |
| POST   | `/projects/{id}/ratings/`                       | Rate the other party after completion  |
| GET    | `/notifications/`                               | List notifications                     |
| PATCH  | `/notifications/{id}/read/`                     | Mark one notification read             |
| PATCH  | `/notifications/read-all/`                      | Mark all notifications read            |
| DELETE | `/notifications/{id}/`                          | Delete a notification                  |
| GET    | `/admin/`                                       | List admins (admin only)               |
| GET    | `/admin/users/`                                 | List all users (admin only)            |
| PATCH  | `/admin/users/{id}/role/`                       | Promote a user to admin (admin only)   |
| GET    | `/dashboard/`                                   | Role-specific stats for the current user |

Full request/response schemas are available in the Swagger UI once the server is running.

## License

MIT
