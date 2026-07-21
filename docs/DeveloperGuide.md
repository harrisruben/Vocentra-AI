# Vocentra AI - Developer Guide

This document describes setting up local environments, managing migrations, running tests, and binding new tools.

---

## 1. Local Development Quickstart

### Backend Setup (FastAPI)
1.  Navigate to the backend directory:
    ```bash
    cd backend
    ```
2.  Create a Python virtual environment and activate it:
    ```bash
    python -m venv .venv
    # Windows:
    .venv\Scripts\activate
    # macOS/Linux:
    source .venv/bin/activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Launch the hot-reloading development server:
    ```bash
    uvicorn app.main:app --reload
    ```

### Frontend Setup (Next.js)
1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```
2.  Install npm packages:
    ```bash
    npm install
    ```
3.  Launch the Next.js development server:
    ```bash
    npm run dev
    ```

---

## 2. Database Migrations (Alembic)

Whenever you edit database tables in `models.py`, generate a new migration revision:

```bash
cd backend
# Autogenerate revision script
alembic revision --autogenerate -m "description_of_changes"

# Apply pending upgrades to SQLite / PostgreSQL
alembic upgrade head
```

---

## 3. Running Unit Tests

Vocentra AI runs a pytest integration harness:

```bash
cd backend
# Execute the entire test suite
python -m pytest -v
```

---

## 4. Registering Custom Tools

To add a new tool execution pathway:
1.  Import `@register_tool` decorator in your tool module:
    ```python
    from app.tools.registry import register_tool
    ```
2.  Decorate your handler, defining argument models, descriptions, and access roles:
    ```python
    @register_tool(
        name="update_slack_channel",
        description="Pushes a notification message to the Slack ops channel.",
        required_role="member"
    )
    async def update_slack_channel(message: str) -> bool:
        # Implementation...
        return True
    ```
3.  The orchestration layer will dynamically register the tool and expose its parameter schema.
