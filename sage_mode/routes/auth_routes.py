from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sage_mode.database import get_db
from sage_mode.models.user_model import User
from sage_mode.services.user_service import UserService
from sage_mode.services.session_service import SessionService
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["auth"])
user_service = UserService()
session_service = SessionService()

class SignupRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    class Config:
        from_attributes = True

@router.post("/signup")
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == request.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    user = User(
        username=request.username,
        email=request.email,
        password_hash=user_service.hash_password(request.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse(id=user.id, username=user.username, email=user.email)

@router.post("/login")
def login(request: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()
    if not user or not user_service.verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    session_id = session_service.create_session(user.id)
    response.set_cookie("session_id", session_id, httponly=True)
    return {"session_id": session_id, "user_id": user.id}

@router.get("/me")
def get_current_user(request: Request, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401)
    user_id = session_service.get_session(session_id)
    if not user_id:
        raise HTTPException(status_code=401)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404)
    return UserResponse(id=user.id, username=user.username, email=user.email)

@router.post("/logout")
def logout(request: Request, response: Response):
    session_id = request.cookies.get("session_id")
    if session_id:
        session_service.delete_session(session_id)
    response.delete_cookie("session_id")
    return {"message": "Logged out"}
