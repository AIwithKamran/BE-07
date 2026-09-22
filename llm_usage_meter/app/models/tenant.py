from sqlalchemy import Column, Integer, DateTime, String, func
from core.database import Base

class Tenant(Base):
    __tablename__  = 'tenants'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    