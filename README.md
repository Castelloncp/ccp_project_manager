# CCP Project Manager - Deployable Flask App

This package contains a deployable Flask application configured for local-disk file uploads,
role-based access (admin/pm/general), admin-only price visibility, CSV import/export,
audit logging, and user management.

## Quick start (local)
1. Create virtualenv and activate
    python -m venv venv
    source venv/bin/activate   # Windows: venv\Scripts\activate

2. Install requirements
    pip install -r requirements.txt

3. Copy .env.example to .env and set SECRET_KEY

4. Initialize DB and create admin via flask shell or run app and create via UI

5. Run
    python app.py

App will be available at http://127.0.0.1:5000
