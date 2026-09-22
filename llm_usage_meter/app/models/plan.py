from sqlalchemy import Column, Integer, String
from core.database import Base

class Plan(Base):
    __tablename__ = 'plans'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    monthly_tokens = Column(Integer, nullable=False)
    api_calls = Column(Integer, nullable=False)
