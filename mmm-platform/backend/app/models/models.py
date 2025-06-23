from sqlalchemy import Column, Integer, String, Date, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class DailyMarketingData(Base):
    __tablename__ = "daily_marketing_data"
    
    date = Column(Date, primary_key=True)
    channel = Column(String(50), primary_key=True)
    spend = Column(Numeric(10, 2))
    impressions = Column(Integer)
    clicks = Column(Integer)
    conversions = Column(Integer)
    revenue = Column(Numeric(10, 2))
    new_customers = Column(Integer)
    returning_customers = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel = Column(String(50))
    campaign_name = Column(String(200))
    start_date = Column(Date)
    end_date = Column(Date)
    budget = Column(Numeric(10, 2))
    campaign_type = Column(String(50))  # 'awareness', 'conversion', 'retention'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ExternalFactor(Base):
    __tablename__ = "external_factors"
    
    date = Column(Date, primary_key=True)
    is_holiday = Column(Boolean, default=False)
    holiday_name = Column(String(100))
    competitor_activity = Column(String(200))
    seasonality_index = Column(Numeric(3, 2), default=1.0)  # 1.0 = normal, 1.5 = high season
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AttributionResult(Base):
    __tablename__ = "attribution_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date)
    channel = Column(String(50))
    model_type = Column(String(50))  # 'linear', 'time_decay', 'u_shaped', 'data_driven'
    attributed_conversions = Column(Numeric(10, 2))
    attributed_revenue = Column(Numeric(10, 2))
    created_at = Column(DateTime, default=datetime.utcnow)