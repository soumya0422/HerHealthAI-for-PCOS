import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_user
from app.models.database import UserModel, HealthRecord, ProgressRecord
from app.models.schemas import PredictRequest
from app.ml.inference import ml_predict
from app.ml.recommendation_engine import get_rule_based_recommendations
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()

from app.models.schemas import PlanGenerateRequest
from pydantic import BaseModel

@router.post('/plan/generate', tags=['Recommendations'])
@limiter.limit("100/minute")
def plan_generate(request: Request, req: PlanGenerateRequest, db: Session = Depends(get_db)):
    """
    Step 2: Generate personalized Diet, Exercise, Lifestyle, and Sleep plans based on the assessment result and new lifestyle inputs.
    """
    try:
        user_input = req.assessment_result.features
        risk_pct = req.assessment_result.risk_percentage
        risk_level = req.assessment_result.risk_level
        lifestyle_inputs = req.lifestyle_inputs.model_dump()

        # Generate full rule-based recommendations with Tier 3 logic
        recs = get_rule_based_recommendations(user_input, risk_pct, risk_level, lifestyle_inputs)

        # If a record ID is provided, try to save the updated recommendations
        if req.assessment_result.record_id:
            record = db.query(HealthRecord).filter(HealthRecord.record_id == req.assessment_result.record_id).first()
            if record:
                record.recommendations = json.dumps(recs)
                record.lifestyle_features = json.dumps(lifestyle_inputs)
                db.commit()

        return recs
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/history', tags=['Progress'])
def history(profile_id: str = None, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    query = db.query(HealthRecord).filter(HealthRecord.user_id == current_user.user_id)
    if profile_id:
        query = query.filter(HealthRecord.profile_id == profile_id)
    
    records = query.order_by(HealthRecord.prediction_date.desc()).limit(20).all()
    return {
        'records': [
            {
                'record_id': r.record_id,
                'risk_score': r.risk_score,
                'risk_level': r.risk_level,
                'prediction_date': r.prediction_date.isoformat(),
                'input_features': json.loads(r.input_features),
            } for r in records
        ],
        'total': len(records)
    }

@router.get('/progress', tags=['Progress'])
def progress(profile_id: str = None, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    query = db.query(HealthRecord).filter(HealthRecord.user_id == current_user.user_id)
    if profile_id:
        query = query.filter(HealthRecord.profile_id == profile_id)
    
    records = query.order_by(HealthRecord.prediction_date.asc()).all()

    if not records:
        return {'has_data': False, 'message': 'No predictions yet.'}

    scores = [{'date': r.prediction_date.isoformat()[:10], 'score': r.risk_score, 'level': r.risk_level} for r in records]
    latest  = records[-1]
    first   = records[0]
    improvement = round(first.risk_score - latest.risk_score, 2)
    pct_change  = round((improvement / first.risk_score) * 100, 2) if first.risk_score > 0 else 0

    prog_query = db.query(ProgressRecord).filter(ProgressRecord.user_id == current_user.user_id)
    if profile_id:
        prog_query = prog_query.filter(ProgressRecord.profile_id == profile_id)
        
    progress_recs = prog_query.order_by(ProgressRecord.recorded_at.desc()).limit(10).all()

    return {
        'has_data': True,
        'total_assessments': len(records),
        'first_score': first.risk_score,
        'latest_score': latest.risk_score,
        'improvement': improvement,
        'improvement_percentage': pct_change,
        'trend': 'improving' if improvement > 0 else ('worsening' if improvement < 0 else 'stable'),
        'scores_over_time': scores,
        'recent_progress': [
            {
                'previous': p.previous_score,
                'current': p.current_score,
                'change': round(p.previous_score - p.current_score, 2),
                'date': p.recorded_at.isoformat()[:10]
            } for p in progress_recs
        ]
    }
