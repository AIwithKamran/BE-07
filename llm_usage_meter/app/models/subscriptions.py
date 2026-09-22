from sqlalchemy import Column, Integer, DateTime, String, ForeignKey
from core.database import Base

class Subscriptions(Base):
    __tablename__ = "Subscriptions"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    plan_id = Column(Integer, ForeignKey("plans.id"))
    status= Column(String)
    created_at = Column(DateTime)