from pydantic import BaseModel, Field
from typing import Optional

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    dob: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class ProfileCreate(BaseModel):
    name: str
    dob: str

class ProfileOut(BaseModel):
    profile_id: str
    name: str
    dob: Optional[str] = None

class PredictRequest(BaseModel):
    profile_id:     Optional[str] = None
    dob:            Optional[str] = None
    age:            Optional[float] = Field(None, ge=10, le=80, description="Age must be between 10 and 80")
    weight:         Optional[float] = Field(None, ge=30, le=200, description="Weight must be between 30 and 200 kg")
    height:         Optional[float] = Field(None, ge=100, le=220, description="Height must be between 100 and 220 cm")
    bmi:            Optional[float] = Field(None, ge=10, le=60, description="BMI must be between 10 and 60")
    pulse:          Optional[float] = Field(None, ge=40, le=200, description="Pulse rate")
    rr:             Optional[float] = Field(None, ge=8, le=40, description="Respiration rate")
    hb:             Optional[float] = Field(None, ge=5, le=20, description="Hemoglobin level")
    cycle_regular:  Optional[int]   = Field(1, ge=0, le=1)
    cycle_length:   Optional[float] = Field(28, ge=20, le=90)
    waist:          Optional[float] = Field(None, ge=18, le=60)
    hip:            Optional[float] = Field(None, ge=24, le=70)
    tsh:            Optional[float] = Field(None, ge=0, le=100)
    amh:            Optional[float] = Field(None, ge=0, le=50)
    prl:            Optional[float] = Field(None, ge=0, le=300)
    vitd:           Optional[float] = Field(None, ge=0, le=150)
    rbs:            Optional[float] = Field(None, ge=50, le=400)
    bp_systolic:    Optional[float] = Field(None, ge=70, le=200)
    bp_diastolic:   Optional[float] = Field(None, ge=40, le=130)
    weight_gain:    Optional[int]   = Field(0, ge=0, le=1)
    hair_growth:    Optional[int]   = Field(0, ge=0, le=1)
    skin_darkening: Optional[int]   = Field(0, ge=0, le=1)
    hair_loss:      Optional[int]   = Field(0, ge=0, le=1)
    pimples:        Optional[int]   = Field(0, ge=0, le=1)
    fast_food:      Optional[int]   = Field(0, ge=0, le=1)
    exercise:       Optional[int]   = Field(0, ge=0, le=1)
    fsh:            Optional[float] = Field(None, ge=0, le=50)
    lh:             Optional[float] = Field(None, ge=0, le=50)
    marriage_years: Optional[float] = Field(None, ge=0, le=40)
    save_record:    bool = True

class DiaryEntryRequest(BaseModel):
    profile_id:     Optional[str] = None
    date: str
    period_status: str
    flow_level: Optional[str] = None
    symptoms: Optional[list] = []
    mood: Optional[str] = None
    notes: Optional[str] = None

class LifestyleInputs(BaseModel):
    wake_up_time: str = Field(..., description="Time input")
    sleep_duration: str = Field(..., description="<5 hours, 5-6 hours, 6-7 hours, 7-8 hours, 8+ hours")
    activity_level: str = Field(..., description="Sedentary, Moderate, Active")
    stress_level: str = Field(..., description="Low, Medium, High")
    exercise_frequency: str = Field(..., description="None, 1-2 days, 3-5 days, Daily")
    food_preference: str = Field(..., description="Veg, Non-Veg, Vegan")
    water_intake: str = Field(..., description="Low, Medium, High")
    job_type: str = Field(..., description="Corporate / Desk Job, Active / Field Work, Sports Woman / Athlete, Student, Homemaker")

class AssessmentResult(BaseModel):
    risk_percentage: float
    risk_level: str
    features: dict
    record_id: Optional[str] = None

class PlanGenerateRequest(BaseModel):
    assessment_result: AssessmentResult
    lifestyle_inputs: LifestyleInputs

