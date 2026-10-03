from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os

from backend.schemas.request import AnalyzeRequest
from backend.schemas.response import AnalyzeResponse

from backend.services.scam_analyzer import analyze_message
#from backend.services.ocr_service import extract_text_from_image
from backend.services.language_service import detect_language
from backend.services.safety_advice import get_safety_advice
from backend.services.gemini_service import generate_explanation
from backend.services.faiss_service import load_index

from backend.database.db import engine
from backend.database.db import SessionLocal
from backend.database.db import Base

from backend.database.models import ScamAnalysis


app = FastAPI()

# The Streamlit frontend is hosted separately (Streamlit Community Cloud),
# so the browser calls this API cross-origin. CORS is required.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "*"
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

Base.metadata.create_all(
    bind=engine
)

@app.on_event("startup")
def startup_event():

    load_index()

@app.get("/")
def home():
    return {
        "message": "ScamShield AI Backend Running"
    }


@app.get("/health")
def health():
    return {
        "status": "running"
    }

@app.get("/analytics")
def analytics():

    db = SessionLocal()

    records = db.query(
        ScamAnalysis
    ).all()

    total = len(records)

    high = len(
        [r for r in records
         if r.risk_level == "High"]
    )

    medium = len(
        [r for r in records
         if r.risk_level == "Medium"]
    )

    low = len(
        [r for r in records
         if r.risk_level == "Low"]
    )

    category_count = {}

    for r in records:

        category_count[r.category] = (
            category_count.get(
                r.category,
                0
            ) + 1
        )

    top_category = "None"

    if category_count:

        top_category = max(
            category_count,
            key=category_count.get
        )

    db.close()

    return {
        "total_analyses": total,
        "high_risk": high,
        "medium_risk": medium,
        "low_risk": low,
        "top_category": top_category
    }
@app.get("/history")
def get_history():

    db = SessionLocal()

    records = db.query(
        ScamAnalysis
    ).all()

    data = []

    for record in records:

        data.append({
            "id": record.id,
            "message": record.message,
            "category": record.category,
            "risk_score": record.risk_score,
            "risk_level": record.risk_level,
            "language": record.language
        })

    db.close()

    return data

@app.post(
    "/analyze-text",
    response_model=AnalyzeResponse
)
def analyze_text(data: AnalyzeRequest):

    # Analyze scam message
    result = analyze_message(
        data.message
    )

    # Detect language
    language = detect_language(
        data.message
    )

    # Get safety advice
    advice = get_safety_advice(
        result["category"]
    )

    # Save to database
    db = SessionLocal()

    analysis = ScamAnalysis(
        message=data.message,
        category=result["category"],
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        language=language
    )

    db.add(analysis)
    db.commit()
    db.close()

    # Debug
    print(
        "Selected Language:",
        data.response_language
    )

    # Gemini explanation
    explanation = generate_explanation(
        data.message,
        result["risk_level"],
        result["flags"],
        result["category"],
        data.response_language
    )

    # Add extra fields
    result["language"] = language
    result["advice"] = advice
    result["explanation"] = explanation

    return result


'''@app.post(
    "/analyze-image"
)
async def analyze_image(
    file: UploadFile = File(...),
    response_language: str = "English"
):

    # Create uploads folder
    os.makedirs(
        "uploads",
        exist_ok=True
    )

    # Save image
    file_path = os.path.join(
        "uploads",
        file.filename
    )

    with open(
        file_path,
        "wb"
    ) as buffer:

        buffer.write(
            await file.read()
        )

    # OCR
    extracted_text = extract_text_from_image(
        file_path
    )

    # Scam analysis
    result = analyze_message(
        extracted_text
    )

    # Language detection
    language = detect_language(
        extracted_text
    )

    # Safety advice
    advice = get_safety_advice(
        result["category"]
    )

    # Gemini + RAG explanation
    explanation = generate_explanation(
        extracted_text,
        result["risk_level"],
        result["flags"],
        result["category"],
        response_language
    )

    # Add fields
    result["language"] = language
    result["advice"] = advice
    result["explanation"] = explanation

    return {
        "extracted_text": extracted_text,
        "analysis": result
    }'''