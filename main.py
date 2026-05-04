from fastapi import FastAPI
import requests
import re

app = FastAPI()

RULE_MAP = {
    "AREA": "area",
    "GOAL": "yagura",
    "LOFT": "hoko",
    "CLAM": "asari"
}

API_URL = "https://api.lp1.av5ja.srv.nintendo.net/api/graphql"

# GitHub raw
UTILS_URL = "https://raw.githubusercontent.com/frozenpandaman/s3s/master/utils.py"

# フォールバック（最悪これで動く）
FALLBACK_HASH = "eb5996a12705c2e94813a62e05c0dc419aad2811b8d49d53e5732290105559cb"


def fetch_hash():
    try:
        res = requests.get(UTILS_URL, timeout=10)
        text = res.text

        # translate_rid 辞書から抽出（最も安全）
        match = re.search(
            r"'XBattleHistoriesQuery'\s*:\s*'([a-f0-9]{64})'",
            text
        )

        if match:
            return match.group(1)

        # 予備パターン
        match2 = re.search(
            r"XBattleHistoriesQuery[^a-f0-9]*([a-f0-9]{64})",
            text
        )

        if match2:
            return match2.group(1)

    except Exception:
        pass

    # 失敗時
    return FALLBACK_HASH


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/xpower")
def get_xpower(bullet: str):
    # =========================
    # ハッシュ取得
    # =========================
    hash_value = fetch_hash()

    # =========================
    # ヘッダ
    # =========================
    headers = {
        "Authorization": f"Bearer {bullet}",
        "Accept-Language": "ja-JP",
        "User-Agent": "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36",
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
    # APIリクエスト
    # =========================
    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=15)
    except Exception as e:
        return {"error": "request_failed", "detail": str(e)}

    if r.status_code != 200:
        return {
            "error": "http_error",
            "status": r.status_code,
            "body": r.text[:500]
        }

    # =========================
    # JSON
    # =========================
    try:
        data = r.json()
    except Exception:
        return {
            "error": "json_parse_failed",
            "raw": r.text[:500]
        }

    if "errors" in data:
        return {
            "error": "graphql_error",
            "detail": data["errors"]
        }

    if not data.get("data"):
        return {
            "error": "no_data",
            "raw": data
        }

    container = data["data"].get("xRankingContainer")

    if not container:
        return {
            "error": "no_xranking",
            "raw": data
        }

    season = container.get("currentSeason")

    if not season:
        return {
            "error": "no_season",
            "raw": data
        }

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
        "hash_used": hash_value,
        "xpower": result,
        "count": len(nodes)
    }