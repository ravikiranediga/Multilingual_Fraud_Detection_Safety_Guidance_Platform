def get_safety_advice(category):

    advice = {

        "Banking Scam":
        "Never share OTPs, PINs, or banking credentials. Contact the bank directly.",

        "OTP Scam":
        "Never share OTPs with anyone. Genuine organizations never ask for OTPs.",

        "UPI Scam":
        "Do not approve unknown payment requests. Verify before paying.",

        "Courier Scam":
        "Verify parcel status using the official courier website.",

        "Job Scam":
        "Avoid paying money for job offers. Verify the company.",

        "Government Scam":
        "Check official government portals before responding."

    }

    return advice.get(
        category,
        "Be cautious and verify information from trusted sources."
    )