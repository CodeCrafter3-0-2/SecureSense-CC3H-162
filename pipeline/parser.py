from datetime import datetime
import re

from datetime import datetime
import re

def parse_log(raw_log: str):
    try:
        # 🔴 CASE 1: ARP / MITM
        if "ARP anomaly" in raw_log:
            ip_match = re.search(r'IP (\d+\.\d+\.\d+\.\d+)', raw_log)

            return {
                "timestamp": datetime.now(),
                "src_ip": ip_match.group(1) if ip_match else "unknown",
                "method": "ARP",
                "endpoint": "anomaly",
                "status": 999,
                "bytes": 0
            }

        # ⚠️ CASE 2: DNS anomaly
        if "DNS" in raw_log or "resolver" in raw_log:
            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', raw_log)

            return {
                "timestamp": datetime.now(),
                "src_ip": ip_match.group(1) if ip_match else "unknown",
                "method": "DNS",
                "endpoint": "anomaly",
                "status": 999,
                "bytes": 0
            }

        # ✅ CASE 3: Normal HTTP logs
        parts = raw_log.split()

        if len(parts) >= 5:
            ip = parts[0]
            method = parts[1]
            endpoint = " ".join(parts[2:-2])
            status = int(parts[-2])
            bytes_ = int(parts[-1])

            return {
                "timestamp": datetime.now(),
                "src_ip": ip,
                "method": method,
                "endpoint": endpoint,
                "status": status,
                "bytes": bytes_
            }

        raise ValueError("Unknown log format")

    except Exception:
        raise ValueError("Invalid log format")