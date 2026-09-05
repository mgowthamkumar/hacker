import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.auth.session import get_current_user
from backend.app.schemas.auth import ProfileUpdateRequest

router = APIRouter(tags=["Profile"])


@router.get("/api/profile")
def get_profile(user: User = Depends(get_current_user)):
    user_dict = user.to_dict()
    return {
        "user": user_dict,
        "profile": user_dict.get("profile", {})
    }


@router.put("/api/profile")
def update_profile(req: ProfileUpdateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = {}
    if user.profile_data:
        try:
            profile = json.loads(user.profile_data)
        except Exception:
            profile = {}

    update_dict = req.model_dump(exclude_unset=True)
    profile.update(update_dict)

    if req.fullName:
        user.name = req.fullName
    if req.picture:
        user.picture = req.picture

    user.profile_data = json.dumps(profile)
    db.commit()

    return {
        "success": True,
        "message": "Profile updated successfully.",
        "profile": profile,
        "user": user.to_dict()
    }
