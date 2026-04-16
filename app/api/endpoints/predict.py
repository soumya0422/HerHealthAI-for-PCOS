import json
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_user
from app.models.database import UserModel, HealthRecord, ProgressRecord
from app.models.schemas import PredictRequest
from app.ml.inference import ml_predict
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()

@router.post('/predict', tags=['Predictions'])
@limiter.limit("100/minute")
def predict(request: Request, req: PredictRequest):
    try:
        user_input = req.model_dump()
        result = ml_predict(user_input)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/predict/full', tags=['Predictions'])
@limiter.limit("100/minute")
def predict_full(request: Request, req: PredictRequest, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    try:
        user_input = req.model_dump()
        result = ml_predict(user_input)

        if req.save_record:
            from app.ml.inference import get_gemini_recommendations
            recs = get_gemini_recommendations(user_input, result['risk_percentage'], result['risk_level'])
            result['recommendations'] = recs

            record = HealthRecord(
                user_id=current_user.user_id,
                input_features=json.dumps(user_input),
                risk_score=result['risk_percentage'],
                risk_level=result['risk_level'],
                recommendations=json.dumps(recs)
            )
            db.add(record)

            prev_record = (db.query(HealthRecord)
                           .filter(HealthRecord.user_id == current_user.user_id)
                           .order_by(HealthRecord.prediction_date.desc())
                           .first())

            if prev_record:
                pct_change = round(((prev_record.risk_score - record.risk_score) / max(prev_record.risk_score, 1)) * 100, 2)
                progress = ProgressRecord(
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
        raise HTTPException(status_code=500, detail=str(e))
