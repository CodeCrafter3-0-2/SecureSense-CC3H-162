import subprocess

blocked_ips = set()

def block_ip(ip):
    if ip in blocked_ips:
        return "Already Blocked"

    try:
        # Linux command (works on WSL / Linux)
        subprocess.run(
            ["iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"],
            check=True
        )
        blocked_ips.add(ip)
        return "Blocked"

    except Exception as e:
        return f"Error: {str(e)}"