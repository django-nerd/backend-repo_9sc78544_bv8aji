import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import Lesson, Standard, User, Subscription, Organization

app = FastAPI(title="LessonlyAI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateLessonRequest(BaseModel):
    title: str
    grade: str
    subject: str
    teks_codes: List[str] = []
    duration_minutes: int = 45
    accommodate_ell: bool = True
    accommodate_sped: bool = True


@app.get("/")
def read_root():
    return {"message": "LessonlyAI backend running"}


@app.get("/test")
def test_database():
    """Simple DB connectivity check"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, "name") else "Unknown"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️ Connected but error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:120]}"
    return response


@app.get("/api/teks", response_model=List[Standard])
def list_teks(subject: Optional[str] = None, grade: Optional[str] = None, q: Optional[str] = None):
    """Browse TEKS standards (seed a small sample if empty)."""
    existing = get_documents("standard", {}) if db else []
    if db and not existing:
        samples = [
            {
                "code": "ELA.3.6.B",
                "subject": "ELA",
                "grade": "3",
                "title": "Reading Comprehension",
                "description": "Use text evidence to support an inference in literary texts.",
            },
            {
                "code": "MATH.5.3.A",
                "subject": "Math",
                "grade": "5",
                "title": "Place Value",
                "description": "Represent decimals to the thousandths using concrete and pictorial models.",
            },
            {
                "code": "SCI.8.7.C",
                "subject": "Science",
                "grade": "8",
                "title": "Forces and Motion",
                "description": "Demonstrate and calculate how unbalanced forces change the speed or direction of an object's motion.",
            },
        ]
        for s in samples:
            create_document("standard", s)
        existing = get_documents("standard", {})

    def matches(s):
        ok = True
        if subject:
            ok = ok and s.get("subject") == subject
        if grade:
            ok = ok and s.get("grade") == grade
        if q:
            hay = f"{s.get('code','')} {s.get('title','')} {s.get('description','')}".lower()
            ok = ok and q.lower() in hay
        return ok

    filtered = [s for s in existing if matches(s)]
    # Cast to Standard-compatible dicts
    return [
        {
            "code": s.get("code"),
            "subject": s.get("subject"),
            "grade": s.get("grade"),
            "title": s.get("title"),
            "description": s.get("description"),
        }
        for s in filtered
    ]


@app.post("/api/generate", response_model=Lesson)
def generate_lesson(req: GenerateLessonRequest):
    """Mock AI generation for demo purposes. Replace with real LLM later."""
    # Guardrails / simple validation
    if not req.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")

    teks_str = ", ".join(req.teks_codes) if req.teks_codes else "Aligned to selected TEKS"

    objectives = (
        f"Students will be able to demonstrate mastery of {req.subject} concepts aligned to {teks_str} by the end of the lesson."
    )
    procedures = (
        "1) Do Now (5m)\n2) Mini-lesson with modeling (10m)\n3) Guided practice (15m)\n"
        "4) Independent practice with checks for understanding (10m)\n5) Exit ticket (5m)"
    )
    accom = []
    if req.accommodate_ell:
        accom.append("Provide sentence stems and visuals for key vocabulary.")
    if req.accommodate_sped:
        accom.append("Offer extended time and choice of response modality.")

    assessment = (
        "Formative checks during guided practice; exit ticket aligned to the objective with TEKS-coded rubric."
    )

    lesson = Lesson(
        title=req.title,
        grade=req.grade,
        subject=req.subject,  # type: ignore
        duration_minutes=req.duration_minutes,
        teks_codes=req.teks_codes,
        objectives=objectives,
        procedures=procedures,
        accommodations="\n".join(accom) if accom else None,
        assessment=assessment,
    )

    # Persist lesson for demo
    try:
        create_document("lesson", lesson.model_dump())
    except Exception:
        # DB optional in this environment
        pass

    return lesson


@app.get("/api/lessons", response_model=List[Lesson])
def list_lessons(grade: Optional[str] = None, subject: Optional[str] = None):
    items = []
    try:
        items = get_documents("lesson", {})
    except Exception:
        pass

    def matches(d):
        ok = True
        if grade:
            ok = ok and d.get("grade") == grade
        if subject:
            ok = ok and d.get("subject") == subject
        return ok

    filtered = [d for d in items if matches(d)]
    return [
        {
            "title": d.get("title"),
            "grade": d.get("grade"),
            "subject": d.get("subject"),
            "duration_minutes": d.get("duration_minutes", 45),
            "teks_codes": d.get("teks_codes", []),
            "objectives": d.get("objectives"),
            "procedures": d.get("procedures"),
            "accommodations": d.get("accommodations"),
            "assessment": d.get("assessment"),
            "author_id": d.get("author_id"),
        }
        for d in filtered
    ]


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
