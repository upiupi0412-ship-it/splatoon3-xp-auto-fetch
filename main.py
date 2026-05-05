from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests

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
# ヘルスチェック
# =========================
@app.get("/")
def root():
    return {
        "ok": True,
        "message": "XP API running"
    }

# =========================
# メインAPI
# =========================
@app.post("/xpower")
async def xpower(req: Request):

    body = await req.json()
    session_token = body.get("sessionToken")

    if not session_token:
        return {
            "ok": False,
            "error": "missing sessionToken"
        }

    try:
        access_token = get_access_token(session_token)
        raw = fetch_xpower(access_token)

        parsed = parse_xpower(raw)

        return {
            "ok": True,
            **parsed,
            "debug": {
                "has_data": "data" in raw,
                "has_errors": "errors" in raw,
            },
            "raw": raw
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }

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
        raise Exception(f"auth failed: {data}")

    return data["access_token"]

# =========================
# GraphQL取得
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

    try:
        return res.json()
    except:
        return {
            "error": "invalid_json",
            "text": res.text
        }

# =========================
# パース（壊れにくい版）
# =========================
def parse_xpower(data):

    # ❗GraphQLエラー優先検出
    if "errors" in data:
        return {
            "area": None,
            "yagura": None,
            "hoko": None,
            "clam": None,
            "error": data["errors"]
        }

    try:
        nodes = (
            data.get("data", {})
                .get("xRankingContainer", {})
                .get("currentSeason", {})
                .get("xRankingEntries", {})
                .get("nodes", [])
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

    except Exception as e:
        return {
            "area": None,
            "yagura": None,
            "hoko": None,
            "clam": None,
            "error": f"parse_error: {str(e)}",
            "raw_sample": str(data)[:500]
        }