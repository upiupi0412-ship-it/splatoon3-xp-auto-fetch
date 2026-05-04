from fastapi import FastAPI
import requests
import re
import time

app = FastAPI()

API_URL = "https://api.lp1.av5ja.srv.nintendo.net/api/graphql"
UTILS_URL = "https://raw.githubusercontent.com/frozenpandaman/s3s/master/utils.py"

# フォールバック（確実に動く）
FALLBACK_HASH = "eb5996a12705c2e94813a62e05c0dc419aad2811b8d49d53e5732290105559cb"

RULE_MAP = {
    "AREA": "area",
    "GOAL": "yagura",
    "LOFT": "hoko",
    "CLAM": "asari"
}

# =========================
# 🔥 高速化ポイント①：Session使い回し
# =========================
session = requests.Session()

# =========================
# 🔥 高速化ポイント②：ハッシュをメモリ保持
# =========================
cached_hash = FALLBACK_HASH
last_hash_fetch = 0
HASH_TTL = 60 * 60  # 1時間だけ更新


def fetch_hash():
    global cached_hash, last_hash_fetch

    # TTL内なら再取得しない
    if time.time() - last_hash_fetch < HASH_TTL:
        return cached_hash

    try:
        res = session.get(UTILS_URL, timeout=5)
        text = res.text

        match = re.search(
            r"'XBattleHistoriesQuery'\s*:\s*'([a-f0-9]{64})'",
            text
        )

        if match:
            cached_hash = match.group(1)
            last_hash_fetch = time.time()
            return cached_hash

    except Exception:
        pass

    return cached_hash  # fallback


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/xpower")
def get_xpower(bullet: str):
    # =========================
    # ハッシュ取得（ほぼ即時）
    # =========================
    hash_value = fetch_hash()

    headers = {
        "Authorization": f"Bearer {bullet}",
        "Accept-Language": "ja-JP",
        "User-Agent": "Mozilla/5.0 (Linux; Android 11; Pixel 5)",
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
                "sha256Hash": hash_value
            }
        }
    }

    # =========================
    # API呼び出し
    # =========================
    try:
        r = session.post(API_URL, headers=headers, json=payload, timeout=10)
    except Exception as e:
        return {"error": "request_failed", "detail": str(e)}

    if r.status_code != 200:
        return {
            "error": "http_error",
            "status": r.status_code,
            "body": r.text[:300]
        }

    try:
        data = r.json()
    except Exception:
        return {
            "error": "json_parse_failed",
            "raw": r.text[:300]
        }

    # GraphQLエラー
    if "errors" in data:
        return {
            "error": "graphql_error",
            "detail": data["errors"]
        }

    # 安全に取り出し
    container = data.get("data", {}).get("xRankingContainer", {})
    season = container.get("currentSeason", {})
    nodes = season.get("xRankingEntries", {}).get("nodes", [])

    result = {
        "area": None,
        "yagura": None,
        "hoko": None,
        "asari": None
    }

    for n in nodes:
        rule = n.get("rule")
        if rule in RULE_MAP:
            result[RULE_MAP[rule]] = n.get("xPower")

    return {
        "xpower": result,
        "count": len(nodes),
        "hash": hash_value
    }