# main.py
from fastapi import FastAPI
import requests

app = FastAPI()

RULE_MAP = {
    "AREA": "area",
    "GOAL": "yagura",
    "LOFT": "hoko",
    "CLAM": "asari"
}

@app.get("/xpower")
def get_xpower(bullet: str):
    hash = "eb5996a12705c2e94813a62e05c0dc419aad2811b8d49d53e5732290105559cb"

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
                "sha256Hash": hash
            }
        }
    }

    r = requests.post(
        "https://api.lp1.av5ja.srv.nintendo.net/api/graphql",
        headers=headers,
        json=payload,
        timeout=15
    )

    data = r.json()

    nodes = data["data"]["xRankingContainer"]["currentSeason"]["xRankingEntries"]["nodes"]

    result = {v: None for v in RULE_MAP.values()}

    for n in nodes:
        rule = n.get("rule")
        if rule in RULE_MAP:
            result[RULE_MAP[rule]] = n.get("xPower")

    return result