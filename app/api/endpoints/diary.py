import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_user
from app.models.database import UserModel, MenstrualRecord
from app.models.schemas import DiaryEntryRequest
from app.ml.inference import get_cycle_diary_insights

router = APIRouter()

@router.post('/entry', tags=['Diary'])
def log_diary_entry(req: DiaryEntryRequest, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    try:
        user_input = req.model_dump()
        
        # Pull history for Gemini context (max 30 days)
        history = (db.query(MenstrualRecord)
                   .filter(MenstrualRecord.user_id == current_user.user_id)
                   .order_by(MenstrualRecord.log_date.desc())
                   .limit(30)
                   .all())
                   
        hist_dicts = [{
            "date": h.log_date,
            "period_status": h.period_status,
            "flow_level": h.flow_level,
            "symptoms": json.loads(h.symptoms) if h.symptoms else [],
            "mood": h.mood
        } for h in history]

        # Generate Insights
        insights = get_cycle_diary_insights(hist_dicts, user_input)

        existing = db.query(MenstrualRecord).filter(
            MenstrualRecord.user_id == current_user.user_id,
            MenstrualRecord.log_date == req.date
        ).first()

        if existing:
            existing.period_status = req.period_status
            existing.flow_level = req.flow_level
            existing.symptoms = json.dumps(req.symptoms) if req.symptoms else None
            existing.mood = req.mood
            existing.notes = req.notes
        else:
            record = MenstrualRecord(
                user_id=current_user.user_id,
                log_date=req.date,
                period_status=req.period_status,
                flow_level=req.flow_level,
                symptoms=json.dumps(req.symptoms) if req.symptoms else None,
                mood=req.mood,
                notes=req.notes
            )
            db.add(record)
            
        db.commit()
        return insights

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/history', tags=['Diary'])
def get_diary_history(db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    records = (db.query(MenstrualRecord)
               .filter(MenstrualRecord.user_id == current_user.user_id)
               .order_by(MenstrualRecord.log_date.desc())
               .limit(100)
               .all())
    
    return {
        'records': [
            {
                'id': r.entry_id,
                'date': r.log_date,
                'period_status': r.period_status,
                'flow_level': r.flow_level,
                'symptoms': json.loads(r.symptoms) if r.symptoms else [],
                'mood': r.mood,
                'notes': r.notes
            } for r in records
        ],
        'total': len(records)
    }
