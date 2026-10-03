import os, secrets, hmac, hashlib, re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from supabase import create_client, Client

BASE_DIR=Path(__file__).resolve().parent
app=FastAPI(title="NextMail API",version="2.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

SUPABASE_URL=os.getenv("SUPABASE_URL","")
SUPABASE_SECRET_KEY=os.getenv("SUPABASE_SECRET_KEY","")
SUPABASE_PUBLISHABLE_KEY=os.getenv("SUPABASE_PUBLISHABLE_KEY","")
MAIL_DOMAIN=os.getenv("MAIL_DOMAIN","nextmail.io").lower()
MAILGUN_SIGNING_KEY=os.getenv("MAILGUN_SIGNING_KEY","")
CRON_SECRET=os.getenv("CRON_SECRET","")

db:Optional[Client]=create_client(SUPABASE_URL,SUPABASE_SECRET_KEY) if SUPABASE_URL and SUPABASE_SECRET_KEY else None

def database():
    if not db: raise HTTPException(503,"Supabase is not configured on the server yet.")
    return db

def now(): return datetime.now(timezone.utc)

def current_user(request:Request):
    if not db: return None
    h=request.headers.get("authorization","")
    if not h.lower().startswith("bearer "): return None
    try: return db.auth.get_user(h.split(" ",1)[1]).user
    except Exception: return None

def profile(uid):
    r=database().table("profiles").select("*").eq("id",uid).maybe_single().execute()
    return r.data

def ensure_profile(user):
    p=profile(str(user.id))
    if p: return p
    return database().table("profiles").insert({"id":str(user.id),"email":user.email}).execute().data[0]

class GenerateRequest(BaseModel):
    visitor_token: Optional[str]=None

@app.get("/api/config")
def config():
    return {"supabase_url":SUPABASE_URL,"supabase_publishable_key":SUPABASE_PUBLISHABLE_KEY,"mail_domain":MAIL_DOMAIN}

@app.get("/api/health")
def health():
    return {"status":"ok","database":bool(db),"mail_domain":MAIL_DOMAIN}

@app.post("/api/generate-email")
def generate_email(payload:GenerateRequest,request:Request):
    d=database(); user=current_user(request)
    owner=str(user.id) if user else None
    visitor=None if owner else payload.visitor_token
    if not owner and visitor and not re.fullmatch(r"[A-Za-z0-9_-]{32,128}", visitor):
        raise HTTPException(400,"Invalid inbox session.")
    if not owner and not visitor: visitor=secrets.token_urlsafe(48)

    q=d.table("mailboxes").select("*").eq("active",True).gt("expires_at",now().isoformat())
    q=q.eq("owner_id",owner) if owner else q.eq("visitor_id",visitor)
    existing=q.limit(1).execute().data
    if existing:
        m=existing[0]
        return {"temp_email":m["address"],"expires_at":m["expires_at"],"plan":m["plan"],"visitor_token":visitor}

    plan="free"
    if user:
        p=ensure_profile(user)
        if p.get("pro_expires_at"):
            try:
                if datetime.fromisoformat(p["pro_expires_at"].replace("Z","+00:00"))>now(): plan="pro"
            except ValueError: pass

    expires=now()+timedelta(days=7 if plan=="pro" else 2/24)
    for _ in range(5):
        address="n"+secrets.token_hex(5)+"@"+MAIL_DOMAIN
        try:
            row=d.table("mailboxes").insert({"address":address,"owner_id":owner,"visitor_id":visitor,"plan":plan,"expires_at":expires.isoformat(),"active":True}).execute().data[0]
            return {"temp_email":row["address"],"expires_at":row["expires_at"],"plan":plan,"visitor_token":visitor}
        except Exception: continue
    raise HTTPException(500,"Could not create mailbox.")

@app.get("/api/inbox/{address}")
def inbox(address:str, request:Request):
    d=database()
    m=d.table("mailboxes").select("*").eq("address",address.lower()).maybe_single().execute().data
    if not m: raise HTTPException(404,"Email does not exist.")
    if m.get("owner_id") is None:
        visitor=request.headers.get("x-nextmail-visitor","")
        if not visitor or not hmac.compare_digest(visitor,m.get("visitor_id") or ""): raise HTTPException(403,"This inbox is not yours.")
    if datetime.fromisoformat(m["expires_at"].replace("Z","+00:00"))<=now():
        d.table("mailboxes").update({"active":False}).eq("id",m["id"]).execute()
        raise HTTPException(410,"Email has expired.")
    msgs=d.table("messages").select("id,sender,recipient,subject,body_text,body_html,received_at").eq("mailbox_id",m["id"]).order("received_at",desc=True).execute().data
    return {"temp_email":m["address"],"expires_at":m["expires_at"],"plan":m["plan"],"messages":msgs}

@app.post("/api/mailgun/inbound")
async def mailgun_inbound(request:Request):
    d=database(); form=await request.form()
    timestamp=str(form.get("timestamp","")); token=str(form.get("token","")); signature=str(form.get("signature",""))
    expected=hmac.new(MAILGUN_SIGNING_KEY.encode(),(timestamp+token).encode(),hashlib.sha256).hexdigest()
    if not MAILGUN_SIGNING_KEY or not hmac.compare_digest(expected,signature): raise HTTPException(401,"Invalid webhook signature.")
    recipient=str(form.get("recipient","")).lower().strip()
    match=re.search(r"<([^>]+)>",recipient); recipient=match.group(1) if match else recipient
    m=d.table("mailboxes").select("*").eq("address",recipient).eq("active",True).maybe_single().execute().data
    if not m: return {"status":"ignored"}
    if datetime.fromisoformat(m["expires_at"].replace("Z","+00:00"))<=now():
        d.table("mailboxes").update({"active":False}).eq("id",m["id"]).execute()
        return {"status":"expired"}
    d.table("messages").insert({"mailbox_id":m["id"],"sender":str(form.get("sender","")),"recipient":recipient,"subject":str(form.get("subject","")),"body_text":str(form.get("body-plain","")),"body_html":str(form.get("body-html",""))}).execute()
    return {"status":"received"}

@app.get("/api/cleanup")
def cleanup(authorization:Optional[str]=Header(default=None)):
    if CRON_SECRET and not authorization == "Bearer "+CRON_SECRET: raise HTTPException(401,"Unauthorized")
    d=database()
    r=d.table("mailboxes").update({"active":False}).lt("expires_at",now().isoformat()).eq("active",True).execute()
    return {"status":"ok","expired":len(r.data or [])}

@app.get("/")
def home(): return FileResponse(BASE_DIR/"index.html")

app.mount("/",StaticFiles(directory=BASE_DIR,html=True),name="frontend")
