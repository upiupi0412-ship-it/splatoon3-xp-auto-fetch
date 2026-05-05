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
GITHUB_URL = "https://raw.githubusercontent.com/frozenpandaman/s3s/master/utils.py"

# =========================
# debug
# =========================
@app.get("/")
def root():
    return {"ok": True, "message": "XP API running"}

@app.get("/hash")
def get_hash():
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
    raw = fetch_xpower(access_token, hash_value)

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
        text = requests.get(GITHUB_URL, timeout=10).text

        # XBattleHistoriesQuery を抽出
        match = re.search(
            r"'XBattleHistoriesQuery':\s*'([a-f0-9]{64})'",
            text
        )

        if match:
            return match.group(1)

        raise Exception("hash not found")

    except Exception as e:
        return str(e)

# =========================
# Nintendo auth
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
# GraphQL
# =========================
def fetch_xpower(access_token, query_hash):

    payload = {
        "variables": {},
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": query_hash
            }
        }
    }

    res = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
            "Accept": "*/*",
            "Origin": "https://api.lp1.av5ja.srv.nintendo.net",
            "Referer": "https://api.lp1.av5ja.srv.nintendo.net/"
        },
        json=payload,
        timeout=15
    )

    try:
        return res.json()
    except:
        return {
            "error": "invalid_json",
            "text": res.text
        }