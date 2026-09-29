import os
import re
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai import errors

from backend.services.faiss_service import search_chunks

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(
    api_key=GEMINI_API_KEY
)

# Ordered by preference, de-duplicated. The first model that succeeds wins.
# Override the head of the chain with GEMINI_MODEL in .env
# (e.g. GEMINI_MODEL=gemini-3.1-pro-preview once a paid key is available).
MODEL_CHAIN = list(
    dict.fromkeys(
        model
        for model in [
            os.getenv(
                "GEMINI_MODEL",
                "gemini-3.5-flash"
            ),
            "gemini-3.5-flash",
            "gemini-3-flash-preview",
            "gemini-2.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-flash-lite-latest"
        ]
        if model
    )
)

# Flash-lite models reject thinking_config outright, so it must be
# dropped for them. Probed: gemini-3.5-flash-lite returns
# 400 INVALID_ARGUMENT when thinking_budget is sent.
LITE_MODELS = {
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.1-flash-lite-preview",
    "gemini-flash-lite-latest"
}

# name -> (native name, 4 labels, script validation range)
LANGUAGES = {
    "English": {
        "native": "English",
        "labels": [
            "Scam Type",
            "Why Suspicious",
            "Risk",
            "Recommended Action"
        ],
        "ranges": None
    },
    "Hindi": {
        "native": "Hindi (Devanagari script)",
        "labels": [
            "घोटाले का प्रकार",
            "संदिग्ध क्यों",
            "जोखिम",
            "सुझाई गई कार्रवाई"
        ],
        "ranges": [(0x0900, 0x097F)]
    },
    "Telugu": {
        "native": "Telugu (Telugu script)",
        "labels": [
            "స్కామ్ రకం",
            "ఎందుకు అనుమానాస్పదం",
            "ప్రమాదం",
            "సూచించిన చర్య"
        ],
        "ranges": [(0x0C00, 0x0C7F)]
    }
}

FALLBACKS = {
    "English": """
1. Scam Type: {category}

2. Why Suspicious: This message contains warning signs such as {flags}.

3. Risk: It may lead to financial loss or misuse of personal information.

4. Recommended Action: Verify through official sources and never share OTPs or banking details.
""",
    "Hindi": """
1. घोटाले का प्रकार: {category}

2. संदिग्ध क्यों: इस संदेश में {flags} जैसे चेतावनी संकेत हैं।

3. जोखिम: आपकी व्यक्तिगत जानकारी या धन का नुकसान हो सकता है।

4. सुझाई गई कार्रवाई: केवल आधिकारिक स्रोतों से सत्यापित करें और OTP या बैंक विवरण साझा न करें।
""",
    "Telugu": """
1. స్కామ్ రకం: {category}

2. ఎందుకు అనుమానాస్పదం: ఈ సందేశంలో {flags} వంటి హెచ్చరిక సంకేతాలు ఉన్నాయి.

3. ప్రమాదం: వ్యక్తిగత సమాచారం లేదా డబ్బు నష్టం జరిగే అవకాశం ఉంది.

4. సూచించిన చర్య: అధికారిక వనరుల ద్వారా ధృవీకరించండి మరియు OTP లేదా బ్యాంక్ వివరాలు పంచుకోవద్దు.
"""
}


def _retrieve_knowledge(
    message
):
    try:
        chunks = search_chunks(
            message,
            top_k=1
        )
    except Exception:
        return ""

    knowledge = "\n\n".join(
        chunks[:1]
    )

    return knowledge[:800]


def _build_prompt(
    message,
    risk_level,
    flags,
    category,
    target_language,
    knowledge
):
    config = LANGUAGES[target_language]

    native = config["native"]
    labels = config["labels"]

    label_block = "\n".join(
        f"{i}. {label}: <one short sentence>"
        for i,
        label in enumerate(
            labels,
            start=1
        )
    )

    language_rule = (
        "- Write 100% in the native script of the language. "
        "Zero transliterated or English words.\n"
        if config["ranges"]
        else "- Write 100% in English.\n"
    )

    return f"""
You are ScamShield AI, a fraud-safety assistant helping Indian users.

Write the safety guidance for the user entirely in {native}.

SUSPICIOUS MESSAGE:
{message}

SCAM CATEGORY: {category}
RISK LEVEL: {risk_level}
DETECTED WARNING SIGNS: {", ".join(flags)}
REFERENCE KNOWLEDGE:
{knowledge if knowledge else "No additional reference available. Rely on general fraud-prevention knowledge."}

OUTPUT FORMAT - EXACTLY 4 numbered lines using these exact labels:
{label_block}

STRICT RULES:
- The 4 labels above must be reproduced exactly as written.
{language_rule}- Do not use the labels from any other language.
- Exactly 4 points. No introduction, no conclusion, no extra bullets.
- Max 15 words per point.
- Point 4 must contain a concrete, actionable instruction.
"""


def _script_ratio(
    text,
    ranges
):
    letters = [
        char for char in text
        if char.isalpha()
    ]

    if not letters:
        return 0.0

    matching = sum(
        1 for char in letters
        if any(
            low <= ord(char) <= high
            for low,
            high in ranges
        )
    )

    return matching / len(letters)


def _is_valid(
    text,
    target_language
):
    if not text or not text.strip():
        return False

    # All 4 numbered points must be present
    numbers = re.findall(
        r"(?m)^\s*([1-4])\s*[.)]",
        text
    )

    if sorted(set(numbers)) != [
        "1",
        "2",
        "3",
        "4"
    ]:
        return False

    # Every label must be reproduced
    for label in LANGUAGES[target_language]["labels"]:
        if label not in text:
            return False

    ranges = LANGUAGES[target_language]["ranges"]

    if ranges is None:
        return True

    # Reject answers that are mostly Latin script
    if _script_ratio(
        text,
        ranges
    ) < 0.6:
        return False

    # Reject answers that leak real English words.
    # Brand-like tokens (OTP, KYC, Aadhaar, UPI) are allowed.
    allowed = {
        "otp",
        "kyc",
        "upi",
        "aadhaar",
        "atm",
        "pin",
        "sms",
        "id"
    }

    english_words = re.findall(
        r"[A-Za-z]{2,}",
        text
    )

    leaked = [
        word for word in english_words
        if word.lower() not in allowed
    ]

    return len(leaked) <= 2


def generate_explanation(
    message,
    risk_level,
    flags,
    category,
    response_language
):
    target_language = response_language

    if target_language not in LANGUAGES:
        target_language = "English"

    if isinstance(flags, str):
        flags = [
            flags
        ]

    knowledge = _retrieve_knowledge(
        message
    )

    prompt = _build_prompt(
        message,
        risk_level,
        flags,
        category,
        target_language,
        knowledge
    )

    for model in MODEL_CHAIN:
        # Flash-lite rejects thinking_config, so start without it for those
        drop_thinking = model in LITE_MODELS

        for attempt in range(4):
            config_args = {
                "temperature": 0.3,
                "top_p": 0.9,
                "max_output_tokens": 1024,
                "response_mime_type": "text/plain"
            }

            # Disable thinking: thought tokens otherwise eat the output
            # budget and truncate Indic scripts mid-sentence
            if not drop_thinking:
                config_args["thinking_config"] = (
                    types.ThinkingConfig(
                        thinking_budget=0
                    )
                )

            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        **config_args
                    )
                )

                text = (response.text or "").strip()

                if _is_valid(
                    text,
                    target_language
                ):
                    return text

                finish = (
                    response.candidates[0].finish_reason
                    if response.candidates
                    else None
                )
                print(
                    f"Model {model} returned an invalid answer "
                    f"(finish_reason={finish}). Retrying."
                )

                # Language drift or truncation: retry with a firmer instruction
                if attempt == 0:
                    prompt += (
                        "\n\nIMPORTANT: Your previous answer was incomplete or "
                        "used the wrong language. Produce all 4 numbered points, "
                        f"each in its full {LANGUAGES[target_language]['native']} sentence, "
                        "using exactly the 4 labels given above."
                    )
                    continue

                break

            except errors.ClientError as error:
                code = getattr(
                    error,
                    "code",
                    None
                )

                print(
                    f"Model {model} attempt {attempt + 1} failed: {error}"
                )

                # 400: this model may reject one of our config fields.
                # Retry once without thinking_config before giving up.
                if code == 400:
                    if not drop_thinking and attempt == 0:
                        drop_thinking = True
                        print(
                            f"Model {model} rejected thinking_config. "
                            "Retrying without it."
                        )
                        continue

                    break

                # 404: this model will never work for this key
                if code == 404:
                    break

                # 429: quota gone for this model, try another
                if code == 429:
                    break

                time.sleep(
                    min(
                        2 ** attempt,
                        8
                    )
                )

            except Exception as error:
                print(
                    f"Model {model} attempt {attempt + 1} failed: {error}"
                )

                time.sleep(
                    min(
                        2 ** attempt,
                        8
                    )
                )

    print(
        "All Gemini models failed. Using offline fallback."
    )

    return FALLBACKS[target_language].format(
        category=category,
        flags=", ".join(flags)
    )
