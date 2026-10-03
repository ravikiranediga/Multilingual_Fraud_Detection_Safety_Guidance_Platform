def analyze_message(message: str):

    risk_score = 0

    flags = []

    category = "Unknown"

    text = message.lower()

    # --------------------------
    # Banking Scam Detection
    # --------------------------

    banking_keywords = [
    "bank",
    "account",
    "kyc",
    "verify",
    "verification",
    "customer",
    "login",
    "secure",
    "sbi",
    "hdfc",
    "icici",
    "axis",
    "debit card",
    "credit card",
    "net banking",


        # Hindi
        "बैंक",
        "खाता",
        "केवाईसी",
        "सत्यापन",

        # Telugu
        "బ్యాంక్",
        "ఖాతా",
        "కెవైసి",
        "ధృవీకరణ"
    ]

    if any(word in text for word in banking_keywords):
        risk_score += 20
        flags.append("Banking Related")
        category = "Banking Scam"

    # --------------------------
    # OTP Scam Detection
    # --------------------------

    otp_keywords = [
    "otp",
    "one time password",
    "authentication code",
    "verification code",
    "security code",
    "confirm otp",

        # Hindi
        "ओटीपी",

        # Telugu
        "ఓటిపి",
        "otp"
    ]

    if any(word in text for word in otp_keywords):
        risk_score += 40
        flags.append("OTP Request")
        category = "OTP Scam"

    # --------------------------
    # UPI Scam Detection
    # --------------------------

    upi_keywords = [
        # English
        "upi",
        "gpay",
        "phonepe",
        "paytm",
        "navi"

        # Hindi
        "यूपीआई",
        "गूगल पे",
        "फोनपे",
        "पेटीएम",

        # Telugu
        "యుపిఐ",
        "గూగుల్ పే",
        "ఫోన్ పే",
        "పేటీఎం"
    ]

    if any(word in text for word in upi_keywords):
        risk_score += 25
        flags.append("UPI Related")
        category = "UPI Scam"

    # --------------------------
    # Courier Scam Detection
    # --------------------------

    courier_keywords = [
        # English
        "parcel",
        "courier",
        "shipment",
        "delivery",

        # Hindi
        "पार्सल",
        "कूरियर",
        "डिलीवरी",

        # Telugu
        "పార్సెల్",
        "కొరియర్",
        "డెలివరీ"
    ]

    if any(word in text for word in courier_keywords):
        risk_score += 25
        flags.append("Courier Related")
        category = "Courier Scam"

    # --------------------------
    # Job Scam Detection
    # --------------------------

    job_keywords = [
        # English
        "job",
        "work from home",
        "salary",
        "interview",

        # Hindi
        "नौकरी",
        "घर बैठे काम",
        "वेतन",
        "इंटरव्यू",

        # Telugu
        "ఉద్యోగం",
        "ఇంటినుంచి పని",
        "జీతం",
        "ఇంటర్వ్యూ"
    ]

    if any(word in text for word in job_keywords):
        risk_score += 25
        flags.append("Job Offer")
        category = "Job Scam"

    # --------------------------
    # Government Scam Detection
    # --------------------------

    govt_keywords = [
        # English
        "government",
        "scheme",
        "subsidy",
        "benefit",
        "aadhaar",

        # Hindi
        "सरकार",
        "योजना",
        "सब्सिडी",
        "आधार",

        # Telugu
        "ప్రభుత్వం",
        "పథకం",
        "సబ్సిడీ",
        "ఆధార్"
    ]

    if any(word in text for word in govt_keywords):
        risk_score += 25
        flags.append("Government Related")
        category = "Government Scam"

    # --------------------------
    # Urgency Detection
    # --------------------------

    urgency_words = [
    "urgent",
    "immediately",
    "blocked",
    "warning",
    "expire",
    "expired",
    "suspended",
    "limited time",
    "act now",
    "verify now",


        # Hindi
        "तुरंत",
        "अभी",
        "ब्लॉक",
        "चेतावनी",

        # Telugu
        "వెంటనే",
        "ఇప్పుడే",
        "బ్లాక్",
        "హెచ్చరిక"
    ]

    for word in urgency_words:

        if word in text:
            risk_score += 10
            flags.append("Urgency")
            break

    # --------------------------
    # Suspicious URL Detection
    # --------------------------

    suspicious_domains = [
        ".xyz",
        ".top",
        ".click"
    ]

    for domain in suspicious_domains:

        if domain in text:
            risk_score += 30
            flags.append("Suspicious URL")
            break

    # --------------------------
    # Remove Duplicate Flags
    # --------------------------

    flags = list(set(flags))

    # --------------------------
    # Risk Level
    # --------------------------

    if risk_score >= 70:
        risk_level = "High"

    elif risk_score >= 40:
        risk_level = "Medium"

    else:
        risk_level = "Low"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "category": category,
        "flags": flags
    }