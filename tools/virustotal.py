import requests
import os
from dotenv import load_dotenv

load_dotenv()

VT_API_KEY = os.getenv("VIRUS_TOTAL_API")
BASE_URL = "https://www.virustotal.com/api/v3"


def vt_headers():
    return {"x-apikey": VT_API_KEY}


# 🔗 URL Scan
def scan_url(url):
    try:
        # 🔹 Step 1: Submit URL
        submit = requests.post(
            f"{BASE_URL}/urls",
            headers=vt_headers(),
            data={"url": url}
        )

        if submit.status_code != 200:
            return {"error": submit.text}

        analysis_id = submit.json()["data"]["id"]

        # 🔹 Step 2: Get analysis result
        result = requests.get(
            f"{BASE_URL}/analyses/{analysis_id}",
            headers=vt_headers()
        )

        if result.status_code != 200:
            return {"error": result.text}

        stats = result.json()["data"]["attributes"]["stats"]

        return {
            "malicious": stats.get("malicious", 0),
            "suspicious": stats.get("suspicious", 0),
            "status": "Malicious" if stats.get("malicious", 0) > 0 else "Safe"
        }

    except Exception as e:
        return {"error": str(e)}


# 🌐 IP Check
def check_ip(ip):
    try:
        res = requests.get(
            f"{BASE_URL}/ip_addresses/{ip}",
            headers=vt_headers()
        )

        data = res.json()["data"]["attributes"]["last_analysis_stats"]

        return {
            "malicious": data["malicious"],
            "status": "Malicious" if data["malicious"] > 0 else "Clean"
        }

    except Exception as e:
        return {"error": str(e)}


# 🧬 Hash Check
def check_hash(hash_value):
    try:
        res = requests.get(
            f"{BASE_URL}/files/{hash_value}",
            headers=vt_headers()
        )

        data = res.json()["data"]["attributes"]["last_analysis_stats"]

        return {
            "malicious": data["malicious"],
            "status": "Malicious" if data["malicious"] > 0 else "Clean"
        }

    except Exception as e:
        return {"error": str(e)}