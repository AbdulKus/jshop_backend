# jshop_backend

FastAPI backend for `jshop_front` and `jshop_admin`.

## Features

- SQLite-backed catalog with 19 seeded lots from the original layout.
- Public API for storefront bootstrap and catalog listing.
- Admin CRUD API for lots, categories, and contact channels.
- Visit counter (`visits`) incremented on each storefront bootstrap call.
- Site text dictionary stored in DB and editable via admin API.
- CORS enabled for local frontend/admin development.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

By default, data is stored in `jshop.db` in the project root.

You can override DB path:

```bash
export JSHOP_DATABASE_URL="sqlite:///./jshop.db"
```

## API overview

- `GET /health`
- `GET /api/v1/bootstrap`
- `GET /api/v1/lots`
- `GET /api/v1/lots/{slug}`

Admin endpoints:

- `GET /api/v1/admin/dashboard`
- `GET /api/v1/admin/lots`
- `GET /api/v1/admin/lots/{slug}`
- `POST /api/v1/admin/lots`
- `POST /api/v1/admin/lots/bulk`
- `POST /api/v1/admin/lots/{slug}/duplicate`
- `PATCH /api/v1/admin/lots/{slug}`
- `DELETE /api/v1/admin/lots/{slug}`
- `GET/POST/PATCH/DELETE /api/v1/admin/categories`
- `GET/POST/PATCH/DELETE /api/v1/admin/contacts`
- `GET /api/v1/admin/site-texts`
- `PUT /api/v1/admin/site-texts/{key}`

Interactive docs:

- Swagger: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
