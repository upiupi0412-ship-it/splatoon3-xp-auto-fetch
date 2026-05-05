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

GRAPHQL_URL = "https://api.lp1.av5ja.srv.nintendo.net/api/graphql"

# =========================
# root
# =========================
@app.get("/")
def root():
    return {"ok": True, "message": "stable splatnet api running"}

# =========================
# main
# =========================
@app.post("/xpower")
async def xpower(req: Request):

    body = await req.json()
    session_token = body.get("sessionToken")

    if not session_token:
        return {"ok": False, "error": "missing sessionToken"}

    try:
        access_token = get_access_token(session_token)

        raw = fetch_xranking(access_token)

        parsed = parse_safe(raw)

        return {
            "ok": True,
            "xpower": parsed,
            "raw": raw
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }

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
        },
        timeout=10
    )

    data = res.json()

    if "access_token" not in data:
        raise Exception(f"auth failed: {data}")

    return data["access_token"]

# =========================
# GraphQL（安定版）
# =========================
def fetch_xranking(access_token):

    # ⚠️ 重要：
    # hashは固定せず「失敗しても返す」運用にする

    payload = {
        "variables": {},
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "eb5996a12705c2e94813a62e05c0dc419aad2811b8d49d53e5732290105559cb"
            }
        }
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Nintendo Switch; OnlineLounge)",
        "Accept": "application/json"
    }

    res = requests.post(
        GRAPHQL_URL,
        headers=headers,
        json=payload,
        timeout=20
    )

    # 🔥 ここ重要：絶対に壊さない
    try:
        return {
            "status": res.status_code,
            "json": res.json()
        }
    except:
        return {
            "status": res.status_code,
            "text": res.text
        }

# =========================
# safe parser
# =========================
def parse_safe(data):

    # まだ構造が未確定なので安全処理

    if not isinstance(data, dict):
        return None

    # GraphQL成功時だけ解析
    j = data.get("json", {})

    try:
        nodes = (
            j["data"]["xRankingContainer"]["currentSeason"]["xRankingEntries"]["nodes"]
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

            if rule == "AREA":
                result["area"] = power
            elif rule == "LOFT":
                result["hoko"] = power
            elif rule == "GOAL":
                result["yagura"] = power
            elif rule == "CLAM":
                result["clam"] = power

        return result

    except:
        return {
            "error": "unexpected structure",
            "keys": list(j.keys()) if isinstance(j, dict) else None
        }