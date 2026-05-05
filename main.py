from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_URL = "https://api.lp1.av5ja.srv.nintendo.net/api/graphql"
UTILS_URL = "https://raw.githubusercontent.com/frozenpandaman/s3s/master/utils.py"

# =========================
# debug
# =========================
@app.get("/")
def root():
    return {"ok": True, "message": "XP API running"}

@app.get("/debug/hash")
def debug_hash():
    return {"hash": get_latest_hash()}

# =========================
# main
# =========================
@app.post("/xpower")
async def xpower(req: Request):

    body = await req.json()
    session_token = body.get("sessionToken")

    if not session_token:
        return {"ok": False, "error": "missing sessionToken"}

    access_token = get_access_token(session_token)

    hash_value = get_latest_hash()
    raw = fetch_graphql(access_token, hash_value)

    return {
        "ok": True,
        "used_hash": hash_value,
        "raw": raw
    }

# =========================
# GitHubから最新hash取得
# =========================
def get_latest_hash():

    try:
        text = requests.get(UTILS_URL, timeout=10).text

        # XBattleHistoriesQuery
        match = re.search(
            r"'XBattleHistoriesQuery':\s*'([a-f0-9]{64})'",
            text
        )

        if match:
            return match.group(1)

        # fallback
        return "eb5996a12705c2e94813a62e05c0dc419aad2811b8d49d53e5732290105559cb"

    except Exception as e:
        return str(e)

# =========================
# auth
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
# GraphQL（安定ヘッダー版）
# =========================
def fetch_graphql(access_token, query_hash):

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
        "User-Agent": "Mozilla/5.0 (Nintendo Switch; OnlineLounge)",
        "Accept": "*/*",
        "Origin": "https://api.lp1.av5ja.srv.nintendo.net",
        "Referer": "https://api.lp1.av5ja.srv.nintendo.net/"
    }

    res = requests.post(API_URL, headers=headers, json=payload, timeout=20)

    return {
        "status": res.status_code,
        "text": res.text,
        "json": safe_json(res)
    }

def safe_json(res):
    try:
        return res.json()
    except:
        return None