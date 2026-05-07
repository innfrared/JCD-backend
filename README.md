# Jasmine Backend - Clean Architecture Django App

A Django REST API application following Clean Architecture principles with clear separation of concerns across Domain, Application, Infrastructure, and Interface layers.

## Architecture Overview

### Layers

1. **Domain Layer** (`src/domain/`)
   - Entities: Core business objects (User, Product, Category, etc.)
   - Value Objects: Immutable domain concepts (Email, Money, etc.)
   - Rules: Business rules and validations
   - **NO Django imports** - Pure Python

2. **Application Layer** (`src/application/`)
   - Use Cases: Business logic orchestration
   - DTOs: Data Transfer Objects for requests/responses
   - Ports: Repository interfaces (abstractions)

3. **Infrastructure Layer** (`src/infrastructure/`)
   - Django Models: Database persistence
   - Repository Implementations: Concrete implementations of ports
   - Services: External service integrations (password hashing, JWT tokens)

4. **Interface Layer** (`interfaces/rest/`)
   - DRF Serializers: Request/response serialization
   - DRF Views: HTTP request handling
   - URLs: Route definitions
   - **Views call Application use-cases, NOT Django models directly**

## Project Structure

```
jasmine_backend/
├── manage.py
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── src/
│   ├── domain/
│   │   ├── users/
│   │   │   ├── entities.py
│   │   │   ├── value_objects.py
│   │   │   └── rules.py
│   │   ├── catalog/
│   │   │   ├── entities.py
│   │   │   ├── value_objects.py
│   │   │   └── rules.py
│   │   └── shared/
│   │       ├── exceptions.py
│   │       └── types.py
│   ├── application/
│   │   ├── users/
│   │   │   ├── ports.py
│   │   │   ├── dto.py
│   │   │   └── use_cases.py
│   │   ├── catalog/
│   │   │   ├── ports.py
│   │   │   ├── dto.py
│   │   │   └── use_cases.py
│   │   └── shared/
│   │       ├── pagination.py
│   │       └── auth.py
│   └── infrastructure/
│       ├── db/
│       │   ├── models/
│       │   │   ├── users.py
│       │   │   └── catalog.py
│       │   ├── repositories/
│       │   │   ├── users_repo.py
│       │   │   └── catalog_repo.py
│       │   └── apps.py
│       └── services/
│           ├── password_hasher.py
│           └── token_service.py
└── interfaces/
    └── rest/
        ├── users/
        │   ├── serializers.py
        │   ├── views.py
        │   └── urls.py
        ├── catalog/
        │   ├── serializers.py
        │   ├── views.py
        │   └── urls.py
        └── shared/
            ├── permissions.py
            └── responses.py
```

## Features

### Users Module
- User registration and authentication (JWT)
- User profile management
- Address management (CRUD operations)
- Default address selection

### Catalog Module
- Categories and subcategories
- Products with variants (sizes, colors)
- EAV (Entity-Attribute-Value) specifications system
- Product filtering by category, subcategory, search, availability, and custom specs
- Pagination support

### EAV Specifications System
The catalog uses a flexible EAV system for product specifications:
- Attributes defined per category/subcategory
- Support for TEXT, NUMBER, BOOLEAN, SINGLE_SELECT, MULTI_SELECT data types
- Filterable attributes for frontend filtering
- Returns both simple key-value records and detailed specification objects

## Setup

### Quick Setup (Recommended)

Run the setup script:
```bash
./setup.sh
```

This will:
- Create a virtual environment
- Install all dependencies
- Run database migrations

### Manual Setup

1. **Create and activate virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

If `pip` is not found, use:
```bash
python3 -m pip install -r requirements.txt
```

3. **Run migrations:**
```bash
python manage.py makemigrations
python manage.py migrate
```

4. **Create superuser:**
```bash
python manage.py createsuperuser
```

5. **Run development server:**
```bash
python manage.py runserver
```

### Troubleshooting

If you get `pip NotFoundError`:
- Use `pip3` instead of `pip`
- Or use `python3 -m pip` instead
- Make sure you're in the virtual environment

### Checks and manual smoke tests

```bash
python manage.py check
python manage.py test
```

Against production (replace host if needed):

```bash
curl -i https://jcd-backend.onrender.com/api/health
curl -i "https://jcd-backend.onrender.com/api/products?page=1&page_size=18"
curl -i "https://jcd-backend.onrender.com/api/categories"
```

Expect `HTTP 200` on `/api/health` with small JSON (no DB). Public catalog responses should include `Cache-Control: public, max-age=60` … `/api/products?page=1&page_size=18` must **not** attach product-list edge caching headers from this backend (non-default `page_size` → internal `cache=skip`). Timing logs for listings appear when `/api/products` runs—in Render logs, grep `products.list`.

For the **default** listing (`GET /api/products?page=1&page_size=20`, no filters): first request logs `cache=miss`; immediate repeat may log `cache=hit` if the same Gunicorn worker still holds LocMem (not guaranteed across workers).

If Postgres prompts about an existing test database, run ``python manage.py test --keepdb --noinput`` or drop the stale ``test_*`` DB.

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/refresh` - Refresh access cookie (`200` on success). Returns `401` when refresh token is missing/expired/invalid; returns `403` only when CSRF/origin checks deny the request (send `X-CSRFToken` matching the CSRF cookie).

### User Profile
- `GET /api/me` - Current user profile (`200`). Anonymous visitors receive `{ "user": null }` (not `401`). Invalid or malformed credentials (e.g. bad Bearer token or bad access cookie when present) return `401`.
- `PATCH /api/me` - Update user profile

### Addresses
- `GET /api/addresses` - List user addresses
- `POST /api/addresses` - Create new address
- `PATCH /api/addresses/<id>` - Update address
- `DELETE /api/addresses/<id>` - Delete address
- `POST /api/addresses/<id>/set-default` - Set default address

### Catalog
- `GET /api/health` - Liveness probe (`{"status":"ok"}`); no database access. Use for uptime pings (e.g. keep Render warm).
- `GET /api/categories` - List all categories
- `GET /api/categories/all` - List public categories with nested public subcategories
- `GET /api/products` - List products (with filters)
  - Supported query params: `category_id`, `subcategory_id`, `subcategory_ids`, `search`, `availability`, `page`, `page_size`, `spec_<key>=<value>`
- `GET /api/products/<id>` - Get product details

Public catalog GET responses above send `Cache-Control: public, max-age=60, s-maxage=600, stale-while-revalidate=300` for CDN/browser caching. Filtered `GET /api/products` responses omit that header (only the default unfiltered first page is marked cacheable at the edge). Those responses use `Vary: Accept-Encoding` only—never `Vary: Cookie`, so shared CDN caches stay viable.

**Product list Django cache (internal):** Only one snapshot is cached under a stable key: `GET /api/products` with `page=1`, `page_size=20`, and no category/subcategory/search/availability/spec filters (see `_is_default_product_list_cacheable`). Any other query string—including `page_size=18`—never uses that key, so there is no cross-talk from undocumented params (`color`, `sort`, etc.). Catalog mutations bump the storefront product version so this snapshot and product-detail entries invalidate (see `src/infrastructure/db/signals.py`).

### Production notes (Render + Vercel)

- **Warm the API**: On Render Free, the service sleeps after idle periods; first requests can take many seconds. Ping `GET /api/health` every ~10 minutes (UptimeRobot, cron-job.org, etc.) or upgrade to a paid Render instance so the service does not spin down.
- **Database connections**: Default `DB_CONN_MAX_AGE` is `600` seconds when unset (override with env `DB_CONN_MAX_AGE`).
- **In-process cache**: Default cache is **LocMemCache**: separate heap **per Gunicorn worker process**—entries are **not** shared across workers or hosts. Acceptable for current scale; use Redis (`CACHE_BACKEND`) when you need a shared cache layer.
- **Vercel timeouts**: If the frontend calls this API from a Server Action or Route Handler, set `export const maxDuration = 30` (or higher on Pro) so serverless functions do not exit before a cold Render response.
- **Next.js caching**: Prefer `fetch(url, { next: { revalidate: 600 } })` for catalog data so edge/CDN serves cached JSON between revalidations.
- **Observability**: `GET /api/products` emits INFO logs on logger `catalog.timing` (`products.list ...`) with `cache`, `total_ms`, `db_ms`, `serialize_ms`, and counts—useful to separate cold start vs DB vs serialization.

### Catalog Contract
- `GET /api/categories/all` is the source of truth for category and subcategory ids used by the frontend.
- `GET /api/categories/all` returns:
  - category: `id`, `name`, `slug`, `created_at`, `subcategories`
  - subcategory: `id`, `category_id`, `name`, `slug`, `description`, `created_at`
- `subcategory.description` is always present in `GET /api/categories/all` as a string or `null`.
- Public catalog taxonomy excludes legacy migration rows whose slugs contain `-old-`.
- Canonical public slugs are:
  - categories: `bags`
  - subcategories: `crossbody-bags`, `shoulder-bags`, `handbags`, `clutches`
- Frontend resolves canonical slug -> id from `GET /api/categories/all`, then calls `GET /api/products` with ids.
- Frontend never hardcodes ids.
- Frontend curated label mapping stays client-side:
  - `Top Handle` -> `handbags`
  - `Evening` -> `clutches`
- `Belts` and `Accessories` are unavailable until backend taxonomy exists.
- `GET /api/products` does not support `ordering`, `category_slug`, or `subcategory_slug`.
- `GET /api/products` returns:
  - top-level: `items`, `total`, `page`, `page_size`, `total_pages`, `has_next`, `has_previous`
  - each product item includes `category_id`, `subcategory_ids`, nested `category`, nested `subcategories`, prices, availability, variant fields, and `specifications`

Example frontend flow:
```js
const categories = await fetch('/api/categories/all').then((res) => res.json());
const bags = categories.find((category) => category.slug === 'bags');
const crossbody = bags?.subcategories.find(
  (subcategory) => subcategory.slug === 'crossbody-bags'
);

await fetch(
  `/api/products?category_id=${bags.id}&subcategory_id=${crossbody.id}&page=1&page_size=20`
);
```

## Cookie-Based Auth (Next.js SSR)

This backend issues JWT access + refresh tokens in HTTP-only cookies for SSR-friendly authentication.

### Endpoints
- `POST /api/auth/login` - Sets access/refresh cookies and returns user
- `POST /api/auth/refresh` - Rotates refresh, sets new access (and refresh) cookies
- `POST /api/auth/logout` - Clears auth cookies
- `GET /api/auth/me` - Returns current user

### Required env vars
See `.env.example` for the full list. Key values:
- `FRONTEND_ORIGINS=http://localhost:5173`
- `AUTH_COOKIE_SECURE=False`
- `AUTH_COOKIE_SAMESITE=Lax` (use `None` + `AUTH_COOKIE_SECURE=True` for cross-domain prod)
- `AUTH_COOKIE_DOMAIN=` (optional parent domain)

### Frontend usage
Use credentials in browser requests:
```js
fetch('http://localhost:8000/api/auth/me', { credentials: 'include' })
```

### CSRF behavior
JWT cookies are protected with double-submit CSRF.
- Login sets a `csrftoken` cookie.
- For unsafe requests (POST/PUT/PATCH/DELETE), send:
  - `X-CSRFToken: <csrftoken cookie value>`

For Next.js SSR, read the `csrftoken` cookie from the incoming request and forward it as the `X-CSRFToken` header.

## Database Schema

### Users
- `User`: email, password_hash, first_name, last_name, phone, is_active, is_staff
- `Address`: user, label, full_name, phone, country, city, street, apartment, postal_code, is_default

### Catalog
- `Category`: name, slug
- `Subcategory`: category, name, slug
- `Product`: name, brand, price, price_new, price_old, availability, category, subcategory, currency
- `ProductVariant`: product, name, value, image_url, color_palette, sort_order
- `VariantSize`: variant, size
- `Attribute`: scope_type, scope_id, key, label, data_type, unit, is_filterable, is_required
- `AttributeOption`: attribute, value, label
- `ProductAttributeValue`: product, attribute, value_text, value_number, value_bool
- `ProductAttributeOption`: product_attribute_value, option

## Development Notes

- All business logic is in the Application layer (use cases)
- Domain layer contains no Django dependencies
- Infrastructure layer implements repository interfaces from Application layer
- Views only call use cases, never access models directly
- EAV system allows dynamic product specifications per category

## License

MIT
