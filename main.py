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

RULE_MAP = {
    "AREA": "area",
    "GOAL": "yagura",
    "LOFT": "hoko",
    "CLAM": "clam"
}

@app.get("/")
def root():
    return {"ok": True, "message": "XP API running"}

@app.post("/xpower")
async def xpower(req: Request):

    body = await req.json()
    session_token = body.get("sessionToken")

    if not session_token:
        return {"ok": False, "error": "missing sessionToken"}

    access_token = get_access_token(session_token)

    raw = fetch_xpower(access_token)

    # 🔥 超重要：まず生ログをそのまま返す
    return {
        "ok": True,
        "access_ok": True,
        "raw": raw
    }


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


def fetch_xpower(access_token):

    # ⚠️ここが犯人候補
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

    res = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "User-Agent": "s3s-python"
        },
        json=payload
    )

    return {
        "status_code": res.status_code,
        "text": res.text,
        "json": safe_json(res)
    }


def safe_json(res):
    try:
        return res.json()
    except:
        return None