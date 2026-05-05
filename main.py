from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
import json

app = FastAPI()

# =========================
# CORS（Worker / TurboWarp用）
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_URL = "https://api.lp1.av5ja.srv.nintendo.net/api/graphql"

# =========================
# ルール対応
# =========================
RULE_MAP = {
    "AREA": "area",
    "GOAL": "yagura",
    "LOFT": "hoko",
    "CLAM": "clam"
}

# =========================
# エンドポイント
# =========================
@app.post("/xpower")
async def xpower(req: Request):
    body = await req.json()
    session_token = body.get("sessionToken")

    if not session_token:
        return {"ok": False, "error": "missing sessionToken"}

    try:
        # =========================
        # STEP1: access_token取得
        # =========================
        access_token = get_access_token(session_token)

        # =========================
        # STEP2: SplatNet GraphQL
        # =========================
        data = fetch_xpower(access_token)

        # =========================
        # STEP3: 整形
        # =========================
        result = parse_xpower(data)

        return {
            "ok": True,
            **result,
            "raw": data
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }

# =========================
# Nintendo認証
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
        raise Exception(f"auth failed: {data}")

    return data["access_token"]

# =========================
# Xパワー取得（GraphQL）
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

    res = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "User-Agent": "s3s-python"
        },
        json=payload
    )

    data = res.json()

    return data

# =========================
# XP整形
# =========================
def parse_xpower(data):

    try:
        nodes = (
            data["data"]["xRankingContainer"]["currentSeason"]["xRankingEntries"]["nodes"]
        )

        result = {
            "area": None,
            "yagura": None,
            "hoko": None,
            "clam": None
        }

        for n in nodes:
            rule = n.get("rule")
            power = n.get("xPower")

            if rule in RULE_MAP:
                result[RULE_MAP[rule]] = power

        return result

    except Exception:
        return {
            "area": None,
            "yagura": None,
            "hoko": None,
            "clam": None
        }