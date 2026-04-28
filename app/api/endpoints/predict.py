import json
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
import uuid
from continuous_learning.data_collector import log_prediction, log_feedback
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_user
from app.models.database import UserModel, ProfileModel, HealthRecord, ProgressRecord
from app.models.schemas import PredictRequest
from app.ml.inference import ml_predict
from app.core.utils import calculate_age
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()

@router.post('/predict', tags=['Predictions'])
@limiter.limit("100/minute")
def predict(request: Request, req: PredictRequest, background_tasks: BackgroundTasks):
    try:
        user_input = req.model_dump()
        if req.dob:
            user_input['age'] = calculate_age(req.dob)
        result = ml_predict(user_input)
        
        # Continuous Learning Logging
        req_id = str(uuid.uuid4())
        prob = result.get('risk_percentage', 0) / 100.0
        background_tasks.add_task(log_prediction, req_id, user_input, prob, result.get('risk_level', 'Low'))
        result['request_id'] = req_id
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/predict/full', tags=['Predictions'])
@limiter.limit("100/minute")
def predict_full(request: Request, req: PredictRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    try:
        user_input = req.model_dump()
        
        # Get active profile
        profile = None
        if req.profile_id:
            profile = db.query(ProfileModel).filter(
                ProfileModel.profile_id == req.profile_id, 
                ProfileModel.user_id == current_user.user_id
            ).first()
        
        if not profile:
            # Pick the first profile as default if none specified
            profile = db.query(ProfileModel).filter(ProfileModel.user_id == current_user.user_id).first()
        
        if not profile:
            raise HTTPException(status_code=404, detail="No profile found for this user.")

        # Identity-aware validation: Compare DOB
        if req.dob and profile.dob and req.dob != profile.dob:
             return JSONResponse(
                 status_code=409,
                 content={
                     "detail": "Identity mismatch",
                     "message": "It looks like you're entering details for a different user.",
                     "code": "IDENTITY_MISMATCH"
                 }
             )

        # Calculate age for the ML model
        if req.dob:
            user_input['age'] = calculate_age(req.dob)
        elif profile.dob:
            user_input['age'] = calculate_age(profile.dob)

        result = ml_predict(user_input)
        
        # Continuous Learning Logging
        req_id = str(uuid.uuid4())
        prob = result.get('risk_percentage', 0) / 100.0
        background_tasks.add_task(log_prediction, req_id, user_input, prob, result.get('risk_level', 'Low'))
        result['request_id'] = req_id

        if req.save_record:
            from app.ml.inference import get_gemini_recommendations
            recs = get_gemini_recommendations(user_input, result['risk_percentage'], result['risk_level'])
            result['recommendations'] = recs

            record = HealthRecord(
                profile_id=profile.profile_id,
                user_id=current_user.user_id,
                input_features=json.dumps(user_input),
                risk_score=result['risk_percentage'],
                risk_level=result['risk_level'],
                recommendations=json.dumps(recs)
            )
            db.add(record)

            prev_record = (db.query(HealthRecord)
                           .filter(HealthRecord.profile_id == profile.profile_id)
                           .order_by(HealthRecord.prediction_date.desc())
                           .first())

            if prev_record:
                pct_change = round(((prev_record.risk_score - record.risk_score) / max(prev_record.risk_score, 1)) * 100, 2)
                progress = ProgressRecord(
                    profile_id=profile.profile_id,
                    user_id=current_user.user_id,
                    previous_score=prev_record.risk_score,
                    current_score=record.risk_score,
                    improvement_pct=pct_change
                )
                db.add(progress)

            db.commit()

            if prev_record:
                result['previous_score'] = prev_record.risk_score

        return result
    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))

from pydantic import BaseModel
class FeedbackRequest(BaseModel):
    request_id: str
    diagnosis: str

@router.post('/feedback', tags=['Predictions'])
def api_feedback(req: FeedbackRequest):
    """Stores verified clinical outcome for a past prediction to trigger continuous learning."""
    success = log_feedback(req.request_id, req.diagnosis)
    if success:
        return {"status": "success", "message": "Feedback recorded."}
    return {"status": "error", "message": "Request ID not found or error occurred."}
