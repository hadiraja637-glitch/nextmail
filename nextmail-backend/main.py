from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid

app = FastAPI()

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


class PaymentRequest(BaseModel):
    email: str
    card_number: str
    plan: str


@app.post("/api/signup")
def signup(user: UserSignup):
    if user.email in users_db:
        raise HTTPException(
            status_code=400, detail="User already exists with this email."
        )
    users_db[user.email] = {
        "password": user.password,
        "plan": "free",
        "created_at": datetime.now(),
    }
    return {"status": "success", "message": "Signup successful!"}


@app.post("/api/generate-email")
def generate_email(email: str, plan_type: str = "free"):
    if email not in users_db:
        raise HTTPException(status_code=404, detail="Please sign in first.")

    random_id = str(uuid.uuid4())[:6]
    temp_email = f"user_{random_id}@nextmail.site"
    now = datetime.now()

    if plan_type == "pro" and users_db[email]["plan"] == "pro":
        expires_at = now + timedelta(days=7)
    else:
        expires_at = now + timedelta(hours=2)

    emails_db[temp_email] = {
        "owner": email,
        "plan": plan_type,
        "created_at": now,
        "expires_at": expires_at,
        "messages": [],
    }

    return {
        "temp_email": temp_email,
        "expires_at": expires_at.strftime("%Y-%m-%d %H:%M:%S"),
        "plan": plan_type,
    }


@app.post("/api/pay-pro")
def process_payment(pay: PaymentRequest):
    if pay.email not in users_db:
        raise HTTPException(status_code=404, detail="User not found.")
    users_db[pay.email]["plan"] = "pro"
    return {"status": "success", "message": "Pro plan activated for 1 week!"}


@app.get("/api/inbox/{temp_email}")
def get_inbox(temp_email: str):
    if temp_email not in emails_db:
        raise HTTPException(
            status_code=404, detail="Email expired or does not exist."
        )
    mail_data = emails_db[temp_email]
    if datetime.now() > mail_data["expires_at"]:
        del emails_db[temp_email]
        raise HTTPException(status_code=410, detail="Email has expired.")
    return mail_data
