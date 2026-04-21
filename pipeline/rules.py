def rule_based_detection(raw_log: str):
    raw = raw_log.lower()

    if "or 1=1" in raw:
        return "SQL Injection"
    if "<script>" in raw:
        return "XSS"
    if "nmap" in raw:
        return "Port Scan"

    return None
    
def rule_based_detection(log):
    if "ARP anomaly" in log:
        return "MITM Attack"

    if "OR 1=1" in log:
        return "SQL Injection"

    return None    