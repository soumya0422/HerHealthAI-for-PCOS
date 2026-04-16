from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.schemas import RegisterRequest, LoginRequest
from app.models.database import UserModel
from app.core.security import hash_password, verify_password, create_token, get_current_user
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post('/register', tags=['Auth'])
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(UserModel).filter(UserModel.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail='Email already registered')
    user = UserModel(
        user_id=str(uuid.uuid4()),
        name=req.name,
        email=req.email.lower().strip(),
        password=hash_password(req.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token(user.user_id, user.email)
    logger.info(f"New user registered: {user.email}")
    return {'token': token, 'user': {'id': user.user_id, 'name': user.name, 'email': user.email}}

@router.post('/login', tags=['Auth'])
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == req.email.lower().strip()).first()
    if not user or not verify_password(req.password, user.password):
        raise HTTPException(status_code=401, detail='Invalid email or password')
    token = create_token(user.user_id, user.email)
    logger.info(f"User logged in: {user.email}")
    return {'token': token, 'user': {'id': user.user_id, 'name': user.name, 'email': user.email}}

@router.get('/me', tags=['Auth'])
def me(current_user: UserModel = Depends(get_current_user)):
    return {'id': current_user.user_id, 'name': current_user.name, 'email': current_user.email}
