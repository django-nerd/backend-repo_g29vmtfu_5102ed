import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
from database import create_document, get_documents, db

app = FastAPI(title="re:collect API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "re:collect backend is running"}

class WaitlistIn(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    linkedin: Optional[str] = None
    notes: Optional[str] = None

@app.post("/api/waitlist")
def join_waitlist(payload: WaitlistIn):
    if db is None:
        # Still allow demo without DB, but return 503
        raise HTTPException(status_code=503, detail="Database not available")
    try:
        # Check if already exists
        existing = get_documents("waitlist", {"email": payload.email}, limit=1)
        if existing:
            return {"status": "ok", "message": "You're already on the list."}
        _id = create_document("waitlist", payload.model_dump())
        return {"status": "ok", "id": _id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/waitlist")
def list_waitlist(limit: int = 50):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    docs = get_documents("waitlist", {}, limit=limit)
    # Convert ObjectId to string if present
    for d in docs:
        if "_id" in d:
            d["_id"] = str(d["_id"])
    return {"items": docs}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
