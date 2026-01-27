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

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/refresh` - Refresh JWT token

### User Profile
- `GET /api/me/` - Get current user profile
- `PATCH /api/me/` - Update user profile

### Addresses
- `GET /api/addresses/` - List user addresses
- `POST /api/addresses/` - Create new address
- `PATCH /api/addresses/<id>/` - Update address
- `DELETE /api/addresses/<id>/` - Delete address
- `POST /api/addresses/<id>/set-default` - Set default address

### Catalog
- `GET /api/categories` - List all categories
- `GET /api/products` - List products (with filters)
  - Query params: `category_id`, `subcategory_id`, `search`, `availability`, `spec_<key>=<value>`, `page`, `page_size`
- `GET /api/products/<id>` - Get product details

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

