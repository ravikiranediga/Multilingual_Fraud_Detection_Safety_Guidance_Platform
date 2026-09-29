from pydantic import BaseModel
from typing import List


class AnalyzeResponse(BaseModel):
    risk_score: int
    risk_level: str
    category: str
    flags: List[str]
    language: str
    advice: str
    explanation: str