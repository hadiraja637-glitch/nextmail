from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
import secrets
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="NextMail API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

users_db = {}
emails_db = {}


class UserSignup(BaseModel):
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class PaymentRequest(BaseModel):
    email: str
    plan: str = "pro"


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "NextMail API"}


@app.post("/api/signup")
def signup(user: UserSignup):
    if user.email in users_db:
        raise HTTPException(status_code=400, detail="User already exists.")
    users_db[user.email] = {
        "password": user.password,
        "plan": "free",
        "created_at": datetime.now(timezone.utc),
    }
    return {"status": "success", "message": "Signup successful."}


@app.post("/api/login")
def login(user: UserLogin):
    saved = users_db.get(user.email)
    if not saved or saved["password"] != user.password:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return {
        "status": "success",
        "token": secrets.token_urlsafe(24),
        "plan": saved["plan"],
    }


@app.post("/api/generate-email")
def generate_email(email: Optional[str] = None, plan_type: str = "free"):
    # Anonymous generation is allowed so the homepage works immediately.
    owner = email if email in users_db else None
    if owner and plan_type == "pro" and users_db[owner]["plan"] == "pro":
        duration = timedelta(hours=12)
        plan = "pro"
    else:
        duration = timedelta(hours=2)
        plan = "free"

    now = datetime.now(timezone.utc)
    random_id = uuid.uuid4().hex[:8]
    temp_email = f"user_{random_id}@nextmail.site"
    expires_at = now + duration

    emails_db[temp_email] = {
        "owner": owner,
        "plan": plan,
        "created_at": now,
        "expires_at": expires_at,
        "messages": [],
    }

    return {
        "temp_email": temp_email,
        "expires_at": expires_at.isoformat(),
        "plan": plan,
    }


@app.get("/api/inbox/{temp_email}")
def get_inbox(temp_email: str):
    mail_data = emails_db.get(temp_email)
    if not mail_data:
        raise HTTPException(status_code=404, detail="Email expired or does not exist.")

    if datetime.now(timezone.utc) > mail_data["expires_at"]:
        del emails_db[temp_email]
        raise HTTPException(status_code=410, detail="Email has expired.")

    return mail_data


@app.post("/api/pay-pro")
def process_payment(pay: PaymentRequest):
    if pay.email not in users_db:
        raise HTTPException(status_code=404, detail="User not found.")
    # This endpoint only changes the demo plan state. Never send raw card
    # details to this API; use a real payment provider for production.
    users_db[pay.email]["plan"] = "pro"
    return {"status": "success", "message": "Pro plan activated."}


@app.get("/")
def home():
    return FileResponse(BASE_DIR / "index.html")


# Static pages/assets are mounted after API routes so /api/* is never shadowed.
app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="frontend")
