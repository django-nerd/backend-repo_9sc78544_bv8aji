"""
Database Schemas for LessonlyAI

Each Pydantic model represents a collection in MongoDB. The collection
name is the lowercase of the class name (e.g., Lesson -> "lesson").
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, EmailStr


class Organization(BaseModel):
    name: str = Field(..., description="School or district name")
    slug: str = Field(..., description="URL-friendly identifier")
    plan: Literal["free", "pro"] = Field("free", description="Billing plan")


class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Work email")
    role: Literal["teacher", "coordinator", "admin"] = Field("teacher")
    org_id: Optional[str] = Field(None, description="Reference to organization id")
    is_active: bool = Field(True)


class Subscription(BaseModel):
    user_id: str
    tier: Literal["free", "premium"] = Field("free")
    usage_ai_generations: int = 0
    limit_ai_generations: int = 10


class Standard(BaseModel):
    code: str = Field(..., description="TEKS identifier e.g., ELA.3.6.B")
    subject: Literal["ELA", "Math", "Science", "SocialStudies"]
    grade: str = Field(..., description="K, 1, 2, ... 12")
    title: str
    description: str


class Lesson(BaseModel):
    title: str
    grade: str
    subject: Literal["ELA", "Math", "Science", "SocialStudies"]
    duration_minutes: int = 45
    teks_codes: List[str] = Field(default_factory=list, description="Array of TEKS codes")
    objectives: Optional[str] = None
    procedures: Optional[str] = None
    accommodations: Optional[str] = None
    assessment: Optional[str] = None
    author_id: Optional[str] = None


# The Flames database viewer will automatically read these schemas
# from the /schema endpoint in main.py and use them for validation.
