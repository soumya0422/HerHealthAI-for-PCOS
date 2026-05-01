import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Text
from sqlalchemy.orm import DeclarativeBase
from app.db.session import engine

class Base(DeclarativeBase):
    pass

class UserModel(Base):
    __tablename__ = 'users'
    user_id    = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name       = Column(String, nullable=False)
    email      = Column(String, unique=True, index=True, nullable=False)
    password   = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ProfileModel(Base):
    __tablename__ = 'profiles'
    profile_id  = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id     = Column(String, index=True, nullable=False)
    name        = Column(String, nullable=False)
    dob         = Column(String, nullable=True) # YYYY-MM-DD
    created_at  = Column(DateTime, default=datetime.utcnow)

class HealthRecord(Base):
    __tablename__ = 'health_records'
    record_id       = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id      = Column(String, index=True, nullable=False)
    user_id         = Column(String, index=True, nullable=False)
    input_features  = Column(Text, nullable=False)
    risk_score      = Column(Float, nullable=False)
    risk_level      = Column(String, nullable=False)
    recommendations = Column(Text, nullable=True)
    lifestyle_features = Column(Text, nullable=True)
    prediction_date = Column(DateTime, default=datetime.utcnow, index=True)

class ProgressRecord(Base):
    __tablename__ = 'progress_tracking'
    progress_id         = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id          = Column(String, index=True, nullable=False)
    user_id             = Column(String, index=True, nullable=False)
    previous_score      = Column(Float, nullable=False)
    current_score       = Column(Float, nullable=False)
    improvement_pct     = Column(Float, nullable=False)
    recorded_at         = Column(DateTime, default=datetime.utcnow)

class MenstrualRecord(Base):
    __tablename__ = 'menstrual_records'
    entry_id        = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id      = Column(String, index=True, nullable=False)
    user_id         = Column(String, index=True, nullable=False)
    log_date        = Column(String, nullable=False) # Storing YYYY-MM-DD
    period_status   = Column(String, nullable=False)
    flow_level      = Column(String, nullable=True)
    symptoms        = Column(Text, nullable=True) # JSON list of symptoms
    mood            = Column(String, nullable=True)
    notes           = Column(Text, nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)
