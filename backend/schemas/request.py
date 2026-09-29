from pydantic import BaseModel

class AnalyzeRequest(BaseModel):
    message: str
    response_language: str