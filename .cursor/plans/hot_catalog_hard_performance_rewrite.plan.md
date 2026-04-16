---
name: hot-catalog-hard-performance-rewrite
overview: Hard simplification and performance rewrite of hot catalog endpoints—card-only and PDP-only payloads, minimal layers, 1–2 DB round trips, no distinct/correlated-subquery list path, Supabase/pooler verification, infra vs code latency report, and evidence of deleted/merged layers. Targets sub-200ms on small datasets.
todos:
  - id: baseline-metrics
    content: Capture before metrics (wall time, query count, SQL) for GET /api/products, GET /api/products/<id>, plus connection behavior note (CONN_MAX_AGE).
    status: completed
  - id: phase1-remove-layers
    content: Document and remove/bypass use-case/repository/DTO hops on hot read paths; shortest DB→JSON path.
    status: completed
  - id: phase2-rewrite-product-list
    content: Rewrite /api/products with one optimized queryset, no distinct unless unavoidable, no correlated image subquery, values/defer, prefetch-only card needs; count strategy (fast/skip/approx).
    status: completed
  - id: phase2-rewrite-product-detail
    content: Rewrite /api/products/<id> to max 2 queries via select_related/prefetch/Prefetch; eliminate sequential get_by_ids chains.
    status: completed
  - id: phase3-supabase-connection
    content: Fix DATABASES/CONN_MAX_AGE and pooler mode (pgBouncer-compatible) for minimal per-request connection overhead.
    status: completed
  - id: phase4-cache-products
    content: Add versioned cache only for default/first-page safe product list keys; no over-cache of dynamic filters.
    status: completed
  - id: phase5-delete-dead-layers
    content: Remove unused ports, duplicate mapping, redundant DTO→serializer paths where view builds dict once.
    status: completed
  - id: phase6-validate
    content: After implementation—report before/after timing, query counts; assert list 1–2 queries, detail 1–2 queries targets.
    status: completed
  - id: payload-audit
    content: Cross-check storefront list/PDP consumers; define minimal card vs PDP field lists; remove unused hot-response fields with contract sign-off.
    status: completed
  - id: infra-latency-breakdown
    content: Separate DB query time vs connection/setup/network; verify app vs DB region; document pooler overhead; classify code-bound vs infra-bound remainder.
    status: completed
  - id: simplification-report
    content: Deliverable listing deleted files, merged/bypassed layers, and single owner of hot-path reads post-refactor.
    status: completed
isProject: true
---

# Hot catalog hard performance rewrite

## Payload rules (contract)

- **`GET /api/products`:** Return **card-grade fields only**, **exactly** what the **storefront product list / grid** consumes—no speculative enrichment. Align field names and nesting with the **actual** list UI components (audit `ProductCard` / list hooks in the frontend repo or documented contract).
- **`GET /api/products/<id>`:** Return **PDP-required data only**—variants, specs, imagery, pricing, taxonomy links the **product detail page** uses. **Remove** fields that are unused by PDP (or move to a separate non-hot endpoint if ever needed).
- **Removal process:** Inventory fields against **real usage** (grep frontend or shared OpenAPI); **drop** unused keys from hot responses after confirmation. Any slimming is a **contract change**—coordinate release with frontend or version the API if needed.

## Principles (non-negotiable)

- **DELETE** over abstract; **shortest** path from DB → HTTP response.
- **MINIMIZE** round trips: target **1–2 queries** for list and detail on hot paths.
- **NO** `distinct()` on list unless unavoidable; prefer **semijoin / EXISTS / id subquery** for M2M filters.
- **NO** correlated **per-row** image subqueries on list; use **`variant_image`** OR **one joined/prefetched “first variant”** per product.
- **NO** sequential `get_by_ids` → `get_subcategories_by_ids` chains; replace with **`select_related` / `prefetch_related` / `Prefetch`**.
- **Paginator `count`** on heavy distinct querysets is a **primary suspect**—replace with **cheap count** (e.g. `COUNT(*)` over a **subquery of distinct product ids**), not omit fields — **pagination JSON shape must stay** (`total`, `total_pages`, `has_next`, `has_previous`).

### Locked product decisions

- **Pagination contract:** **Keep current response shape exactly** — do not drop `total` / `total_pages`; optimize via **query shape** (cheap id subquery + count) instead of removing fields.
- **List card image:** **`Coalesce(variant_image, first_variant_image)`** using **one join or prefetch path** — **no** correlated per-row subquery; semantics aligned with PDP as much as possible without reintroducing slowness.

---

## Phase 1 — What to remove (explicit)

### Layers to treat as **candidates for bypass or deletion** on **hot reads**

| Layer | Role today | Verdict |
|--------|------------|---------|
| **`ListProductsUseCase` / `GetProductUseCase`** | Orchestrate repo + build DTOs | **MERGE into view or a single `catalog_reads` module** that returns **dicts** ready for JSON—only if use cases become pass-through after rewrite. |
| **`DjangoProductRepository.get_all` / `get_by_id` + `_product_to_response`** | Many small queries + domain mapping | **REWRITE** in place first; **DELETE** duplicate mapping if view returns structured dicts once. |
| **Domain `Product` → `ProductCardResponse` / `ProductResponse` DTOs** | Extra Python objects | **KEEP** only if they enforce contract tests; otherwise **build dict** once at serialization boundary. |
| **DRF serializers for responses** | Validate outgoing shape | **KEEP** thin serializers **OR** replace with **`JsonResponse` + explicit dict** if serializers only copy fields (measure churn). |

### What **stays** (for now)

- **Models / DB tables** — no schema change unless an index is proven by `EXPLAIN ANALYZE`.
- **Versioned cache keys** in [`src/infrastructure/cache/storefront_cache.py`](/Users/inna/JCD-backend-app/src/infrastructure/cache/storefront_cache.py) — keep bump/invalidation semantics.
- **Pagination envelope** on list (`total`, `total_pages`, `has_next`, `has_previous`, `items` structure) — **unchanged**.
- **Per-field payload on list/detail** — **may shrink** per **Payload rules** (card-only / PDP-only); coordinate with storefront consumers.

### What **must go** (patterns)

- **Sequential repository calls** in [`_product_to_response`](/Users/inna/JCD-backend-app/src/application/catalog/use_cases.py) (`get_specifications_batch` + `get_by_ids` + `get_subcategories_by_ids` + `get_variant_group_products` + `get_product_variants`).
- **`with_resolved_primary_image` correlated `Subquery`** on **list** path ([`src/infrastructure/db/querysets/catalog.py`](/Users/inna/JCD-backend-app/src/infrastructure/db/querysets/catalog.py)) — replace with list-cheap rule.
- **`queryset.distinct()` + `Paginator.count`** on join-inflated product lists ([`src/infrastructure/db/repositories/catalog_repo.py`](/Users/inna/JCD-backend-app/src/infrastructure/db/repositories/catalog_repo.py)).

---

## Phase 2 — Rewrite hot paths (aggressive)

### `/api/products` (full rewrite rules)

1. **Single optimized queryset** (or **two**: ids + fetch-by-id batch) — no N+1, no distinct unless proven necessary.
2. **Fetch only card fields**: `only()` / `values()` / deferred heavy text columns if any.
3. **Subcategory filter** without row duplication: e.g. `filter(pk__in=Subquery(ThroughModel.objects.filter(subcategory_id__in=...).values('product_id')))` (exact table name from Django M2M through) — **no** `subcategories__id__in` join that multiplies rows.
4. **Image for card**: `Coalesce(F('variant_image'), <joined first variant image>)` via **annotation from joined/prefetched variants**, **not** correlated subquery per row; if business allows, **`variant_image` only** on list for v1 (fastest).
5. **Count**: replace default `Paginator` count with **`COUNT(*)` over a subquery of distinct product ids** (pagination fields **unchanged**). Optional: cached count only for **fixed** high-hit keys.
6. **Response assembly**: build **card dicts** in one loop—**only** fields required for list UI; **thin** serializer or explicit dict matching **payload rules** above.

**Files to own the rewrite:** [`interfaces/rest/catalog/views.py`](/Users/inna/JCD-backend-app/interfaces/rest/catalog/views.py), [`src/infrastructure/db/repositories/catalog_repo.py`](/Users/inna/JCD-backend-app/src/infrastructure/db/repositories/catalog_repo.py) (or new **`catalog_queries.py`** next to models if repository deleted from hot path).

### `/api/products/<id>` (max 2 queries)

1. **Query A**: `Product.objects.select_related('category', 'variant_group').prefetch_related(`  
   - `Prefetch('subcategories', queryset=Subcategory.objects.only(...)),`  
   - `Prefetch('variants' or related name, queryset=ProductVariant.objects.order_by(...)),`  
   - sibling products in variant group if needed via **one** `Prefetch` with filtered queryset **or** denormalized fields on `Product`.
2. **Query B**: `ProductAttributeValue` (+ options) for `product_id=<id>` with `select_related`/`prefetch_related` — **single** batched spec load.

**Forbidden:** separate `get_by_ids`, `get_subcategories_by_ids`, `get_variant_group_products` in sequence for one request.

**Files:** same as above + collapse [`_product_to_response`](/Users/inna/JCD-backend-app/src/application/catalog/use_cases.py) into one function next to ORM or delete it. **Trim** [`ProductResponseSerializer`](/Users/inna/JCD-backend-app/interfaces/rest/catalog/serializers.py) / DTOs to **PDP-only** fields per payload rules.

---

## Phase 3 — Database + connection (Supabase) + infrastructure verification

### Config changes (same as before)

- **Audit** [`config/settings.py`](/Users/inna/JCD-backend-app/config/settings.py): `CONN_MAX_AGE = 0` when using `pooler.supabase.com` — confirm whether each HTTP request pays **new connection** cost (major on 4–6s TTFB).
- **Align** with Supabase pooler mode (transaction vs session): use documented Django/`dj-database-url` options (e.g. `OPTIONS`, `DISABLE_SERVER_SIDE_CURSORS`, `conn_max_age`, `sslmode`, `pgbouncer` flags as per current Supabase docs).
- **Goal:** stable connections per worker, **minimal** connect/handshake overhead.

### Mandatory verification (report in Phase 6 deliverables)

| Item | How |
|------|-----|
| **Separate DB time vs connection/setup vs network** | In staging/prod-like env: log **`django.db.backends`** query duration sum per request vs **total request time**; use **`connection.connection.time`** / pool metrics if available; optional **`pg_stat_statements`** or **`EXPLAIN (ANALYZE, BUFFERS)`** for SQL-only time. Document **TLS + pooler** as separate from query execution. |
| **App region vs database region** | Compare **Render (or host) region** to **Supabase project region** in dashboard; flag **cross-region RTT** (often ~50–200ms+ per round trip × query count). |
| **Pooler / connection overhead** | A/B: same endpoint with **`CONN_MAX_AGE=0`** vs **persistent** (where safe for pooler mode); compare **first vs subsequent** request on same worker. |
| **Code-bound vs infra-bound** | After rewrite: if **query count ≤2** and **SQL time &lt;50ms** but **wall time &gt;500ms**, attribute remainder to **network/TLS/pooler/region**. If **SQL time** dominates, **code/query shape** is still the bottleneck. |

---

## Phase 4 — Caching (realistic only)

- **`GET /api/products`**: versioned cache for **safe, high-hit** keys only — e.g. **default storefront list** (no search / no spec filters / first page / fixed `page_size`). Key must include **taxonomy version** (reuse [`bump_product_version`](/Users/inna/JCD-backend-app/src/infrastructure/cache/storefront_cache.py) or taxonomy bump as appropriate).
- **`/api/categories/all`**, **`/api/home`**: **keep** current caching; verify **cache backend** is not file-I/O bound in production (prefer Redis if deploy env is slow disk).

---

## Phase 5 — Delete overkill

- Remove **pass-through** use cases and **duplicate** DTO mapping after hot path writes dicts once.
- Remove **unused** catalog ports / duplicate URL modules if still present.
- **Collapse** “repository that only wraps `.objects.filter`” into **one module** of query functions if it reduces files without hiding SQL.

---

## Phase 6 — Validation (mandatory)

| Endpoint | Target | Query target |
|----------|--------|----------------|
| `GET /api/products` | **&lt;200ms** (warm DB, prod-like network) | **1–2** |
| `GET /api/products/<id>` | **&lt;200ms** | **1–2** |

**Deliverables:**

- **Performance:** Before/after **wall time** (median/p95), **per-request SQL time** (sum of logged query durations where possible), **query count** (`assertNumQueries` + `django.db.connection.queries` in dev).
- **SQL:** **EXPLAIN ANALYZE** on worst SQL **before** and **after** (staging).
- **Infrastructure:** Short written **verdict**: remaining latency **code-bound** (ORM/query/payload) vs **infra-bound** (region, pooler, TLS, connection churn); include **region alignment** note.
- **Simplification evidence (required):**
  - **Deleted:** list of **files/modules removed** (or marked deprecated removed).
  - **Merged/bypassed:** what replaced **use cases / repositories / DTO hops** (e.g. “list reads owned by `catalog/views.py` + `catalog_queries.py` only”).
  - **Hot-path ownership after refactor:** one short paragraph—**single place** responsible for list SQL + response shape, **single place** for detail SQL + PDP payload (file paths).

---

## Risks

- **API contract**: pagination fields are fixed; **field list** slimming on list/detail still needs **frontend alignment** or version bump.
- **Image parity**: list may use **simpler** rule than PDP; document behavior.
- **Supabase pooler**: wrong `CONN_MAX_AGE`/cursor settings can cause subtle bugs—test in staging.

---

## Execution order (when implementation is approved)

1. Baseline metrics + `EXPLAIN` worst query.
2. Connection + cache backend fix if baseline shows connect/file-cache overhead.
3. Rewrite **list** queryset + count strategy.
4. Rewrite **detail** prefetch + spec batch (2 queries max).
5. Surgical **HTTP cache** for safe product list keys.
6. Delete dead layers + re-run metrics and query-count tests.
