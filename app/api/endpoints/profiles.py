from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_user
from app.models.database import UserModel, ProfileModel
from app.models.schemas import ProfileCreate, ProfileOut
import uuid

router = APIRouter()

@router.get("/", response_model=list[ProfileOut], tags=["Profiles"])
def get_profiles(db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    profiles = db.query(ProfileModel).filter(ProfileModel.user_id == current_user.user_id).all()
    return profiles

@router.post("/", response_model=ProfileOut, tags=["Profiles"])
def create_profile(req: ProfileCreate, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    # Limit profiles per user? (Optional)
    count = db.query(ProfileModel).filter(ProfileModel.user_id == current_user.user_id).count()
    if count >= 5:
        raise HTTPException(status_code=400, detail="Maximum 5 profiles allowed per account.")

    profile = ProfileModel(
        profile_id=str(uuid.uuid4()),
        user_id=current_user.user_id,
        name=req.name,
        dob=req.dob
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

@router.delete("/{profile_id}", tags=["Profiles"])
def delete_profile(profile_id: str, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    profile = db.query(ProfileModel).filter(ProfileModel.profile_id == profile_id, ProfileModel.user_id == current_user.user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Don't allow deleting the last profile maybe?
    count = db.query(ProfileModel).filter(ProfileModel.user_id == current_user.user_id).count()
    if count <= 1:
         raise HTTPException(status_code=400, detail="Cannot delete the only profile in the account.")

    db.delete(profile)
    db.commit()
    return {"message": "Profile deleted"}
