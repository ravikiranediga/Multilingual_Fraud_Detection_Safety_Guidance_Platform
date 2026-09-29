from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime

from datetime import datetime

from backend.database.db import Base


class ScamAnalysis(Base):

    __tablename__ = "scam_analysis"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    message = Column(String)

    category = Column(String)

    risk_score = Column(Integer)

    risk_level = Column(String)

    language = Column(String)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )