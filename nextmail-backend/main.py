from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random
import string

app = FastAPI(title="NextMail API", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temporary emails aur unke messages store karne ke liye database
inboxes_db = {}

@app.get("/")
def home():
    return {"status": "online", "message": "NextMail is running smoothly!"}

# 1. New Temporary Email Generate karna
@app.get("/api/generate")
def generate_email():
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    email = f"{username}@nextmail.site"
    
    # Shuru mein aik welcome message rakh dete hain taake inbox khali na lage
    inboxes_db[email] = [
        {
            "sender": "welcome@nextmail.site",
            "subject": "Welcome to NextMail!",
            "body": "Aapka temporary inbox active hai. Yahan aapko naye emails milenge!"
        }
    ]
    return {"email": email}

# 2. Us Email ka Inbox check karna (Messages dekhne ke liye)
@app.get("/api/inbox/{email}")
def get_inbox(email: str):
    if email not in inboxes_db:
        return {"messages": []}
    return {"messages": inboxes_db[email]}
