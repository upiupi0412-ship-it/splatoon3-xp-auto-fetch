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

# =========================
# base
# =========================
@app.get("/")
def root():
    return {"ok": True, "message": "s3s-style API (no GraphQL)"}

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

        # 🔥 GraphQL完全廃止
        data = fetch_splatnet_history(access_token)

        result = extract_xpower(data)

        return {
            "ok": True,
            "xpower": result,
            "raw": data
        }

    except Exception as e:
        return {"ok": False, "error": str(e)}

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
# 🔥 ここが本体（GraphQLなし）
# =========================
def fetch_splatnet_history(access_token):

    # ⚠️ S3S系で使われる“実データ系エンドポイント”
    url = "https://api.lp1.av5ja.srv.nintendo.net/api/festivals"  # 安定寄りの例

    headers = {
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "Mozilla/5.0 (Nintendo Switch; OnlineLounge)",
        "Accept": "application/json",
        "Origin": "https://api.lp1.av5ja.srv.nintendo.net",
        "Referer": "https://api.lp1.av5ja.srv.nintendo.net/"
    }

    res = requests.get(url, headers=headers, timeout=20)

    try:
        return res.json()
    except:
        return {
            "status": res.status_code,
            "text": res.text
        }

# =========================
# XP抽出（安全ダミー構造）
# =========================
def extract_xpower(data):

    # ⚠️ 実データ構造は環境で変わるため防御的解析

    if not isinstance(data, dict):
        return None

    # 仮解析（s3s風）
    return {
        "note": "structure depends on SplatNet response",
        "keys": list(data.keys()) if isinstance(data, dict) else None
    }