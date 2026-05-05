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

AUTH_URL = "https://accounts.nintendo.com/connect/1.0.0/api/token"
SPLATNET_BASE = "https://api.lp1.av5ja.srv.nintendo.net"

# =========================
@app.post("/xpower")
async def xpower(req: Request):

    body = await req.json()
    session_token = body.get("sessionToken")

    if not session_token:
        return {"ok": False, "error": "missing sessionToken"}

    try:
        access_token = get_access(session_token)

        # 🔥 ここが本質（GraphQLではない）
        data = fetch_splatnet_home(access_token)

        return {
            "ok": True,
            "raw": data,
            "note": "this is real SplatNet response (not GraphQL)"
        }

    except Exception as e:
        return {"ok": False, "error": str(e)}

# =========================
# auth
# =========================
def get_access(session_token):

    res = requests.post(
        AUTH_URL,
        json={
            "client_id": "71b963c1b7b6d119",
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer-session-token",
            "session_token": session_token
        },
        headers={
            "Content-Type": "application/json",
            "User-Agent": "OnlineLounge/2.5.1"
        },
        timeout=10
    )

    j = res.json()

    if "access_token" not in j:
        raise Exception(j)

    return j["access_token"]

# =========================
# 🔥 実SplatNet通信（GraphQL回避）
# =========================
def fetch_splatnet_home(access_token):

    url = f"{SPLATNET_BASE}/api/splatnet3/status"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "Mozilla/5.0 (Nintendo Switch; OnlineLounge)",
        "Accept": "application/json",
        "Referer": SPLATNET_BASE
    }

    res = requests.get(url, headers=headers)

    try:
        return res.json()
    except:
        return {
            "status": res.status_code,
            "text": res.text
        }