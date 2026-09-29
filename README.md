# 🛡️ ScamShield AI

**Multilingual Fraud Detection & Safety Guidance Platform**

ScamShield AI analyses suspicious messages and screenshots, scores their risk, and returns
safety guidance in **English, Hindi, and Telugu**. It is built for users who read the
warning but do not necessarily understand it in English.

A message that says *"Your Aadhaar will be blocked today, call 9876543210 and give OTP"*
is obvious in English. In Telugu, without this tool, it is not. The safety guidance is
returned in the reader's own language and script.

---

## Table of Contents

- [Why This Exists](#why-this-exists)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [How Detection Works](#how-detection-works)
- [How Multilingual Output Works](#how-multilingual-output-works)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Running the Project](#running-the-project)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Limitations](#limitations)
- [Future Work](#future-work)
- [License](#license)

---

## Why This Exists

Fraud messages in India overwhelmingly target non-English speakers. The threat itself
is language-independent: urgency, an OTP request, an impersonated government or bank,
a phone number to call. But the *defence* is often published only in English.

The consequence is that a warning message is forwarded to a family member, and the
family member cannot verify it. This project closes that gap: the same detection logic,
but the safety guidance comes back in the reader's own language.

---

## Architecture

```
                    ┌──────────────────────────┐
                    │   Streamlit Frontend     │
                    │      (port 8501)         │
                    └────────────┬─────────────┘
                                 │  HTTP / JSON
                                 ▼
                    ┌──────────────────────────┐
                    │    FastAPI Backend       │
                    │      (port 8000)         │
                    └────────────┬─────────────┘
                                 │
     ┌───────────────┬───────────┼───────────┬────────────────┐
     ▼               ▼           ▼           ▼                ▼
┌──────────┐  ┌───────────┐ ┌────────┐ ┌──────────┐  ┌──────────────┐
│  Scam    │  │    RAG    │ │ Gemini │ │   OCR    │  │  LangDetect  │
│ Analyzer │  │  (FAISS)  │ │ Service│ │ EasyOCR  │  │  (langdetect)│
│keywords  │  │ all-Mini  │ │multi-  │ │  en, hi  │  │              │
│+ scoring │  │ LM-L6-v2  │ │ model  │ │          │  │              │
└──────────┘  └───────────┘ └────────┘ └──────────┘  └──────────────┘
     │               │            │          │              │
     └───────────────┴────────────┴──────────┴──────────────┘
                                 │
                          ┌──────┴───────┐
                          │  SQLite DB   │
                          │ (SQLAlchemy) │
                          └──────────────┘
```

**Request flow for `/analyze-text`:**

1. `analyze_message()` scores the message against keyword rules → risk score, level, category, flags
2. `detect_language()` identifies the *input* language via `langdetect`
3. `get_safety_advice()` returns category-specific safety advice
4. The result is persisted to SQLite
5. `generate_explanation()` retrieves one knowledge chunk from FAISS, then calls Gemini with a
   language-specific prompt and returns the 4-point explanation in the requested language
6. FastAPI assembles and returns the combined payload

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit 1.62 |
| Backend API | FastAPI 0.141 + Uvicorn |
| LLM | Google Gemini (`google-genai`) |
| Embeddings | `sentence-transformers` → `all-MiniLM-L6-v2` (384-dim) |
| Vector search | FAISS (`IndexFlatL2`) |
| Chunking | `langchain-text-splitters` → `RecursiveCharacterTextSplitter` |
| OCR | EasyOCR (English + Hindi) |
| Language ID | `langdetect` |
| Database | SQLite via SQLAlchemy 2.0 |
| Validation | Pydantic 2.13 |

---

## How Detection Works

`backend/services/scam_analyzer.py` runs a transparent keyword rule engine. It is
deliberately explainable — every risk point can be traced to a specific matched keyword.

| Signal | Score | Category set |
|---|---|---|
| Banking keyword | +20 | Banking Scam |
| OTP request | +40 | OTP Scam |
| UPI / wallet keyword | +25 | UPI Scam |
| Courier / parcel keyword | +25 | Courier Scam |
| Job offer keyword | +25 | Job Scam |
| Government keyword | +25 | Government Scam |
| Urgency language | +10 | — |
| Suspicious TLD (`.xyz`, `.top`, `.click`) | +30 | — |

Risk bands: **High** ≥ 70 · **Medium** ≥ 40 · **Low** < 40

Keyword lists include English, Hindi (Devanagari), and Telugu script terms, so detection
works regardless of the input language.

---

## How Multilingual Output Works

`backend/services/gemini_service.py`. This is the part of the system that required the most
care, and it is worth documenting because three separate problems had to be solved.

**1. Language-specific prompts.** The prompt contains only the *selected* language's four
labels, never all three at once. Listing every language in one prompt causes the model to
frequently copy the English labels regardless of the instruction.

**2. Thinking disabled.** Gemini reasoning models spend `thinking` tokens before the answer.
With a small output budget this consumed the budget first and truncated Telugu and Hindi
mid-sentence — responses cut off after point 2 of 4. Setting `thinking_budget=0` fixed it.
Flash-lite models reject `thinking_config` outright with a `400`, so those models build
their config without it.

**3. Output validation.** Every response is verified before it reaches the user:

- all four numbered points present
- all four language-specific labels present
- script-ratio check — at least 60% of letters must be Telugu (`U+0C00–0C7F`) or
  Devanagari (`U+0900–0C097F`) codepoints
- leaked-English check — no more than 2 unapproved Latin words, with a brand-term
  allowlist (`OTP`, `KYC`, `UPI`, `Aadhaar`, `ATM`, `PIN`, `SMS`, `ID`)

A response that fails validation is retried with a corrective prompt rather than shown to
the user.

**4. Model failover.** A chain of models is tried in order until one succeeds:

```
gemini-3.5-flash → gemini-3-flash-preview → gemini-2.5-flash
  → gemini-3.5-flash-lite → gemini-3.1-flash-lite → gemini-flash-lite-latest
```

Error handling is differentiated rather than uniform: `429` and `404` skip to the next
model, `503` backs off and retries the *same* model, and `400` retries once without
`thinking_config`. If every model fails, a localized offline template is returned so the
user always receives guidance in their language.

Set the preferred model with `GEMINI_MODEL` in `.env` — it is prepended to the chain.

---

## Project Structure

```
.
├── backend/
│   ├── main.py                     # FastAPI app, all endpoints
│   ├── database/
│   │   ├── db.py                   # Engine, session factory
│   │   └── models.py               # ScamAnalysis table
│   ├── schemas/
│   │   ├── request.py              # AnalyzeRequest
│   │   ├── response.py             # AnalyzeResponse
│   │   └── stats_response.py
│   └── services/
│       ├── scam_analyzer.py        # Keyword risk engine
│       ├── gemini_service.py       # Multilingual explanation + failover
│       ├── faiss_service.py        # Vector index load/search
│       ├── embedding_service.py    # all-MiniLM-L6-v2 embeddings
│       ├── chunking_service.py     # Recursive text splitter
│       ├── language_service.py     # langdetect wrapper
│       ├── ocr_service.py          # EasyOCR extraction
│       ├── safety_advice.py        # Category advice lookup
│       ├── similarity_service.py
│       └── rag_service.py
├── frontend/
│   └── app.py                      # Streamlit UI (4 tabs)
├── scripts/
│   └── build_vector_db.py          # Rebuild the FAISS index
├── data/
│   ├── scam_knowledge/             # 6 knowledge documents
│   └── vector_store/               # Generated: index + chunks
├── tests/
├── docs/screenshots/
├── requirements.txt
└── .env                            # Local only — never commit
```

---

## Installation

**Prerequisites:** Python 3.11

```bash
git clone <your-repo-url>
cd Multilingual_Fraud_Detection_Safety_Guidance_Platform

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
```

Create `.env` in the project root:

```bash
GEMINI_API_KEY=your-key-here
```

Get a key at [Google AI Studio](https://aistudio.google.com/apikey).

**Build the vector index** (required once, otherwise RAG retrieval returns nothing):

```bash
python scripts/build_vector_db.py
```

> `data/vector_store/` is excluded by `.gitignore` because it is a generated binary
> artifact. Run this script after cloning. If you prefer to ship a prebuilt index,
> remove that line from `.gitignore`.

---

## Running the Project

Two processes are required. Open two terminals.

**Terminal 1 — backend:**

```bash
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 — frontend:**

```bash
streamlit run frontend/app.py
```

Open <http://localhost:8501>.

| Tab | Function |
|---|---|
| Analyze Text | Paste a message, choose response language, get risk analysis + multilingual explanation |
| Analyze Image | Upload a scam screenshot, extract text via OCR, analyse it in the chosen language |
| History | View all past analyses from SQLite |
| Analytics | Aggregated metrics, category distribution, risk distribution |

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Service banner |
| `GET` | `/health` | Liveness check |
| `POST` | `/analyze-text` | Analyse a text message |
| `POST` | `/analyze-image` | Analyse an uploaded image |
| `GET` | `/history` | All stored analyses |
| `GET` | `/analytics` | Aggregate statistics |

**`POST /analyze-text`**

```json
{
  "message": "Your Aadhaar will be blocked today. Call 9876543210 and give OTP.",
  "response_language": "Telugu"
}
```

`response_language` is one of `English`, `Hindi`, `Telugu`. Defaults to `English`.

Response:

```json
{
  "risk_score": 65,
  "risk_level": "Medium",
  "category": "Government Scam",
  "flags": ["OTP Request", "Government Related"],
  "language": "en",
  "advice": "Never share OTPs with anyone...",
  "explanation": "1. స్కామ్ రకం: ..."
}
```

**`POST /analyze-image`**

Multipart form with a `file` field, plus an optional query parameter:

```
POST /analyze-image?response_language=Hindi
```

Returns `{ "extracted_text": "...", "analysis": { ... } }`.

---

## Configuration

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `GEMINI_API_KEY` | Yes | — | Google Gemini API key |
| `GEMINI_MODEL` | No | `gemini-3.5-flash` | Preferred model, prepended to the failover chain |

---

## Troubleshooting

**All output suddenly looks generic or repetitive.**

You have hit the API quota. The app silently falls back to its built-in templates, which
are correct in each language but not message-specific. The tell-tale sign is the literal
string `Government Scam` appearing inside the Telugu explanation. Free-tier limits are
20 requests/day *per model*; across the six models in the chain that is roughly 120
requests/day. Limits reset daily. Enable billing to remove them.

**Explanation is cut off after point 2.**

A model is running with thinking enabled. Confirm the running code includes
`thinking_budget=0` in `backend/services/gemini_service.py`.

**`400 INVALID_ARGUMENT` in the terminal.**

A flash-lite model received `thinking_config`, which it rejects. Lite models are listed
in `LITE_MODELS` and must build their config without that field.

**`404` on `gemini-2.5-pro`.**

That model is no longer available to new API keys; Google returns a redirect notice to
`gemini-3.1-pro-preview`. Remove it from the chain.

**Streamlit page loads but every button errors.**

The backend is not running on port 8000. Both processes are required.

**`IndexError` in `faiss_service.py` on first run.**

The vector index has not been built. Run `python scripts/build_vector_db.py`.

---

## Limitations

Stated plainly, because they are real:

- **Keyword detection is shallow.** It matches on substrings, so it can be evaded and can
  produce false positives. It is not a classifier and should not be presented as one.
  False negatives on novel scam phrasing are expected.
- **OCR handles English and Hindi only.** EasyOCR is configured for `['en', 'hi']`, so
  Telugu text in a screenshot will not be extracted. Telugu *output* is unaffected.
- **Risk scoring is additive and unweighted.** A message matching both OTP and government
  keywords is not scored more dangerously than one matching only OTP, unless a further
  signal fires.
- **`ScamAnalysis.message` is a `String` column with no length limit.** SQLite permits
  this, but a different database would require a `Text` column.
- **No authentication.** Every endpoint is open. Do not deploy publicly without adding
  access control, or you risk both abuse and unbounded API cost.
- **No prompt-injection defence.** A scam message containing instruction-like text is
  passed into the Gemini prompt. The output is constrained to a fixed four-line format and
  is not executed anywhere, which limits impact, but the message content is not
  neutralised before prompting.
- **SQLite is synchronous and global.** Fine for a single-user demo; not concurrent-safe
  for production traffic.

---

## Future Work

- Telugu OCR support
- Replace the keyword engine with a trained classifier, keeping the rule engine as an
  interpretable baseline
- Expand the knowledge base beyond six documents
- Per-user history and rate limiting
- WhatsApp and SMS ingestion
- Add a real automated test suite (`pytest` is not currently installed)

---

## License

Released under the MIT License.

---

## Acknowledgements

- Google Gemini API for multilingual generation
- `sentence-transformers` and the `all-MiniLM-L6-v2` model
- FAISS for vector similarity search
- EasyOCR for screenshot text extraction
