from fastapi import FastAPI
import requests
import os

app = FastAPI()

# =========================
# 🔐 環境変数から取得
# =========================
SESSION_TOKEN = os.getenv("SESSION_TOKEN")

if not SESSION_TOKEN:
    raise Exception("SESSION_TOKEN が設定されていません")

# =========================
# 設定
# =========================
F_API_URL = "https://nxapi-znca-api.fancy.org.uk/api/znca/f"
GRAPHQL_URL = "https://api.lp1.av5ja.srv.nintendo.net/api/graphql"

HASH = "eb5996a12705c2e94813a62e05c0dc419aad2811b8d49d53e5732290105559cb"

session = requests.Session()

# =========================
# ① session_token → id_token
# =========================
def get_id_token():
    url = "https://accounts.nintendo.com/connect/1.0.0/api/session_token"

    headers = {
        "User-Agent": "OnlineLounge/2.5.1 NASDKAPI Android"
    }

    cookies = {
        "session_token": SESSION_TOKEN
    }

    r = session.post(url, headers=headers, cookies=cookies)
    data = r.json()

    if "id_token" not in data:
        raise Exception("id_token取得失敗")

    return data["id_token"]


# =========================
# ② f API
# =========================
def get_f(id_token):
    body = {
        "token": id_token,
        "hash_method": 1
    }

    r = session.post(F_API_URL, json=body)
    data = r.json()

    if "f" not in data:
        raise Exception("f API失敗")

    return data


# =========================
# ③ gToken取得
# =========================
def get_gtoken(id_token, f_data):
    url = "https://api-lp1.znc.srv.nintendo.net/v3/Account/Login"

    body = {
        "parameter": {
            "f": f_data["f"],
            "naIdToken": id_token,
            "timestamp": f_data["timestamp"],
            "requestId": f_data["request_id"]
        }
    }

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "com.nintendo.znca/2.5.1",
        "x-productversion": "2.5.1",
        "x-platform": "Android"
    }

    r = session.post(url, json=body, headers=headers)
    data = r.json()

    try:
        return data["result"]["webApiServerCredential"]["accessToken"]
    except Exception:
        raise Exception(f"gToken取得失敗: {data}")


# =========================
# ④ bulletToken取得
# =========================
def get_bullet(gtoken):
    url = "https://api.lp1.av5ja.srv.nintendo.net/api/bullet_tokens"

    headers = {
        "Authorization": f"Bearer {gtoken}",
        "User-Agent": "com.nintendo.znca/2.5.1",
        "Content-Type": "application/json"
    }

    r = session.post(url, headers=headers)
    data = r.json()

    if "bulletToken" not in data:
        raise Exception(f"bulletToken取得失敗: {data}")

    return data["bulletToken"]


# =========================
# ⑤ Xパワー取得
# =========================
def get_xpower(bullet):
    headers = {
        "Authorization": f"Bearer {bullet}",
        "Accept-Language": "ja-JP",
        "User-Agent": "Mozilla/5.0",
        "X-Web-View-Ver": "10.0.0-88706e32",
        "Content-Type": "application/json",
        "x-nacountry": "JP",
        "x-language": "ja-JP",
        "x-timezone": "Asia/Tokyo",
    }

    payload = {
        "variables": {},
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": HASH
            }
        }
    }

    r = session.post(GRAPHQL_URL, headers=headers, json=payload)
    data = r.json()

    if "data" not in data:
        raise Exception(f"Xパワー取得失敗: {data}")

    return data


# =========================
# APIエンドポイント
# =========================
@app.get("/xpower")
def xpower():
    try:
        id_token = get_id_token()
        f_data = get_f(id_token)
        gtoken = get_gtoken(id_token, f_data)
        bullet = get_bullet(gtoken)
        data = get_xpower(bullet)

        return data

    except Exception as e:
        return {"error": str(e)}