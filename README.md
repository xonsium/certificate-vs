# Certificate Verification System

Minimal Flask + SQLite certificate verification system with:

- Public verification flow (`/`)
- Admin panel (`/admin`)
- Token-protected API for record creation (`/api/certificates`)

## Tech Stack

- Backend: Flask, Flask-WTF, Flask-Login, Flask-SQLAlchemy
- Database: SQLite
- Frontend: HTML/CSS/Vanilla JS with DaisyUI + Tailwind CDN
- Certificate generation: html2canvas + jsPDF

## Setup

1. Create and activate virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Copy env file:

```powershell
copy .env.example .env
```

3. Ensure MongoDB is running and `.env` has the correct URI.

4. Run app:

```powershell
.venv\Scripts\python run.py
```

## Default Admin

Default admin user is auto-created on startup (if missing):

- Username: `admin`
- Password: `changeme`

Change it from **Admin -> Settings**.

You can override bootstrap defaults in `.env` before first run:

- `DEFAULT_ADMIN_USERNAME`
- `DEFAULT_ADMIN_PASSWORD`

## Public Verification API

### `POST /api/verify`

CSRF-protected endpoint used by the frontend.

Request JSON:

```json
{
  "event": "FTMPC",
  "code": "ABC123"
}
```

## Token Auth API (for scripts)

### 1) Generate API Token in Admin

Go to **Admin -> Settings -> API access token** and click **Generate new API token**.

Copy the token immediately.

### 2) Create certificate record from script

### `POST /api/certificates`

Auth headers:

- `Authorization: Bearer <token>` **or**
- `X-API-Token: <token>`

Request JSON:

```json
{
  "event": "INIT",
  "verification_code": "A1B2C3",
  "name": "Jane Doe",
  "institution": "Example University",
  "segment": "UI/UX",
  "prize_place": "Participant",
  "installment": "2026"
}
```

`verification_code` is optional. If omitted/empty, server auto-generates one.

### Example Python

```python
import requests

token = ""

url = "http://127.0.0.1:5000/api/certificates"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

data = {
    "event": "FTMPC",
    "verification_code": "",
    "name": "John Doe",
    "institution": "ABC Institute",
    "segment": "Programming",
    "prize_place": "2nd",
    "installment": "2026"
}

response = requests.post(url, headers=headers, json=data)

print(response.status_code)
print(response.text)
```

## Certificate Templates

Templates are split by event and can be edited independently:

- `app/templates/certificates/ftmpc.html`
- `app/templates/certificates/init.html`
- `app/templates/certificates/thynk.html`
- `app/templates/certificates/pixelcon.html`

Shared styling lives in:

- `app/static/css/app.css`

