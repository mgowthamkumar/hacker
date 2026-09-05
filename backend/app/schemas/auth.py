from typing import Optional, Any, Dict
from pydantic import BaseModel, EmailStr


class GoogleAuthRequest(BaseModel):
    credential: str
    deviceVerified: Optional[bool] = False


class VerifyOtpRequest(BaseModel):
    tempToken: str
    otp: str


class ResendOtpRequest(BaseModel):
    tempToken: str


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = ""


class ConfigureSmtpRequest(BaseModel):
    appPassword: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None


class ProfileUpdateRequest(BaseModel):
    fullName: Optional[str] = None
    mobileNumber: Optional[str] = None
    userType: Optional[str] = None
    dob: Optional[str] = None
    preferredDomain: Optional[str] = None
    experienceLevel: Optional[str] = None
    githubProfile: Optional[str] = None
    linkedinProfile: Optional[str] = None
    termsAgreement: Optional[str] = None
    picture: Optional[str] = None
