from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_URL = "https://api.lp1.av5ja.srv.nintendo.net/api/graphql"

# =========================
# 確認用
# =========================
@app.get("/")
def root():
    return {"ok": True, "message": "XP API running"}

@app.get("/whoami")
def whoami():
    return {"ok": True, "file": "main.py active"}

# =========================
# XP取得
# =========================
@app.post("/xpower")
async def xpower(req: Request):

    body = await req.json()
    session_token = body.get("sessionToken")

    if not session_token:
        return {"ok": False, "error": "missing sessionToken"}

    access_token = get_access_token(session_token)

    raw = fetch_xpower(access_token)

    return {
        "ok": True,
        "raw": raw,
        "debug": {
            "has_data": isinstance(raw, dict) and "data" in raw,
            "has_errors": isinstance(raw, dict) and "errors" in raw
        }
    }

# =========================
# 認証
# =========================
def get_access_token(session_token):

    res = requests.post(
        "https://accounts.nintendo.com/connect/1.0.0/api/token",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "OnlineLounge/2.5.1 NASDKAPI Android"
        },
        json={
            "client_id": "71b963c1b7b6d119",
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer-session-token",
            "session_token": session_token
        }
    )

    data = res.json()

    if "access_token" not in data:
        raise Exception(data)

    return data["access_token"]

# =========================
# GraphQL（安全版）
# =========================
def fetch_xpower(access_token):

    query_hash = "eb5996a12705c2e94813a62e05c0dc419aad2811b8d49d53e5732290105559cb"

    payload = {
        "variables": {},
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": query_hash
            }
        }
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*",
        "Origin": "https://api.lp1.av5ja.srv.nintendo.net",
        "Referer": "https://api.lp1.av5ja.srv.nintendo.net/"
    }

    res = requests.post(API_URL, headers=headers, json=payload, timeout=15)

    return {
        "status": res.status_code,
        "text": res.text,
        "json": safe_json(res)
    }