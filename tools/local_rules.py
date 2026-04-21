import re

COMMON_PASSWORDS = ["123456", "password", "qwerty", "admin", "letmein"]

def check_password(password):
    score = 0
    issues = []

    # Length check
    if len(password) >= 8:
        score += 1
    else:
        issues.append("Too short (min 8 chars)")

    # Uppercase
    if re.search(r"[A-Z]", password):
        score += 1
    else:
        issues.append("No uppercase letters")

    # Lowercase
    if re.search(r"[a-z]", password):
        score += 1
    else:        issues.append("No lowercase letters")

    # Numbers
    if re.search(r"\d", password):
        score += 1
    else:
        issues.append("No numbers")

    # Special characters
    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        score += 1
    else:
        issues.append("No special characters")

    # Common password check
    if password.lower() in COMMON_PASSWORDS:
        issues.append("Very common password")
        score = 0

    # Strength label
    if score <= 1:
        strength = "Weak"
        crack_time = "Seconds"
    elif score == 2:
        strength = "Fair"
        crack_time = "Minutes"
    elif score == 3:
        strength = "Medium"
        crack_time = "Hours"
    elif score == 4:
        strength = "Strong"
        crack_time = "Days"
    else:
        strength = "Very Strong"
        crack_time = "Years"

    return {
        "strength": strength,
        "score": f"{score}/5",
        "crack_time_estimate": crack_time,
        "issues": issues if issues else ["No major issues"]
    }