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
# status
# =========================
@app.get("/")
def root():
    return {"ok": True, "message": "s3s-like API running"}

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

        raw = fetch_splatnet(access_token)

        return {
            "ok": True,
            "raw": raw
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }

# =========================
# Nintendo login
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
        raise Exception(data)

    return data["access_token"]

# =========================
# s3s風GraphQL（重要）
# =========================
def fetch_splatnet(access_token):

    # ⚠️ s3sは本来複数queryを使うが
    # 今は最小構成で安定確認

    payload = {
        "variables": {},
        "extensions": {
            "persistedQuery": {
                "version": 1,
                # ⚠️ ここは「死んでもログ出す」
                "sha256Hash": "eb5996a12705c2e94813a62e05c0dc419aad2811b8d49d53e5732290105559cb"
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

    res = requests.post(
        GRAPHQL_URL,
        headers=headers,
        json=payload,
        timeout=20
    )

    # 🔥 s3s風：生データそのまま返す
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