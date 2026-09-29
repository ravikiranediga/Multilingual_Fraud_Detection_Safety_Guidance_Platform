from pydantic import BaseModel


class StatsResponse(BaseModel):

    total_analyses: int

    high_risk: int

    medium_risk: int

    low_risk: int

    top_category: str