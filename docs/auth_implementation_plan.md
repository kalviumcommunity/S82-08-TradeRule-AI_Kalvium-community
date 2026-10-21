# TradeRule AI — Authentication & Production Deployment Implementation Plan

## 1. Baseline Inspection Summary

- **Existing Auth**: None found. All endpoints and pages are currently unauthenticated.
- **Frontend Architecture**: Next.js 16.3 App Router with client components, server proxy routes (`/api/chat`, `/api/health`), and mock user "Donna Kendrik" hardcoded in `layout.tsx`.
- **Backend Architecture**: FastAPI running on Uvicorn, serving RAG pipeline (`/query`, `/query/stream`, `/chat`, `/documents`, `/documents/list`, `/logs`).
- **Data Persistence**:
  - Documents stored in `uploads/`
  - Vector chunks stored in Qdrant with local fallback `embedding_store.json`
  - Audit logs written to `logs/rag_requests.jsonl`
  - Query history & shipment context stored in client `localStorage`

## 2. Architectural Risks & Mitigations

1. **Risk: Breaking RAG Flow & Next.js Proxy**
   - *Mitigation*: Support dual session authentication: HTTP-only cookies (`traderule_session`) for direct browser access AND `Authorization: Bearer <token>` headers for Next.js server-side API proxying (`/api/chat`).
2. **Risk: Role Escalation via Public API**
   - *Mitigation*: Hardcode registration role strictly to `user`. Any `role` field sent in the registration payload is ignored. Admin creation is strictly controlled via CLI bootstrap script or secure environment variables.
3. **Risk: CORS / Cross-Origin Cookie Dropping in Production**
   - *Mitigation*: Configure dynamic CORS origin validation from `ALLOWED_ORIGINS` environment variable, set cookie `SameSite=Lax`, `Secure=True` in production, `HttpOnly=True`.
4. **Risk: Storage Incompatibility on Render / Cloud**
   - *Mitigation*: Use SQLAlchemy ORM with SQLite for local development (`traderule.db`) and auto-detect `DATABASE_URL` (PostgreSQL) in production.
5. **Risk: RAG Cache Bleed Between Users**
   - *Mitigation*: Tag cache operations with user context and maintain strict public vs tenant isolation.

## 3. Files to Create and Modify

### Backend Files to Create:
- `backend/src/db.py`: SQLAlchemy database models (`User`), engine, session management.
- `backend/src/auth.py`: Password hashing (Argon2id), JWT generation/verification, FastAPI dependencies (`get_current_user`, `require_admin`).
- `backend/src/bootstrap_admin.py`: Secure CLI bootstrap script for first administrator.
- `tests/test_auth.py`: Comprehensive test suite for auth and role-based permissions.
- `tests/test_rag_auth.py`: Integration test suite for RAG functionality with authentication.

### Backend Files to Modify:
- `backend/src/api.py`: Add `/auth/register`, `/auth/login`, `/auth/logout`, `/auth/me`. Protect `/chat`, `/query`, `/query/stream` with `get_current_user`. Protect `/documents`, `/documents/list`, `/logs` with `require_admin`. Update CORS to support production origins.
- `requirements.txt` & `backend/src/requirements.txt`: Add `argon2-cffi`, `pyjwt`, `sqlalchemy`, `psycopg2-binary`, `pytest`.

### Frontend Files to Create:
- `context/AuthContext.tsx`: Client-side Auth context, session restoration, login/register/logout handlers.
- `app/login/page.tsx`: Modern login screen matching TradeRule dark logistics aesthetic.
- `app/register/page.tsx`: Registration screen with validation.
- `components/ProtectedRoute.tsx`: Client-side route protection & role guard with unauthorized/forbidden views.

### Frontend Files to Modify:
- `app/layout.tsx`: Wrap application in `AuthProvider`, make header user avatar and profile dynamic, add logout button.
- `components/Navigation.tsx`: Dynamically adjust navigation based on auth state and admin role.
- `app/api/chat/route.ts`: Forward Authorization token / cookies to FastAPI backend.
- `app/admin/review/page.tsx` & `app/admin/upload/page.tsx`: Wrap in admin protection and forward auth headers.
- `app/ask/page.tsx`: Wrap in user protection and include auth token in requests.

### Deployment & Config Files:
- `render.yaml`: Production Render configuration for backend.
- `vercel.json`: Production Vercel configuration for frontend.
- `.env.example`: Updated environment variables template.
- `README.md`: Updated setup, migration, bootstrap, and deployment documentation.
