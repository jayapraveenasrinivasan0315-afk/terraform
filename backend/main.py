from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime
import os
from urllib.parse import quote_plus

# ─── Database Configuration ───────────────────────────────

# Cloud Run injects secrets from Secret Manager as env vars (mapped in Cloud Run console)
# Secret Manager names: dev-db-url, dev-db-password
# These are mounted as Cloud Run environment variables with the same names

_raw_password = os.environ.get("dev-db-password", "")
_encoded_password = quote_plus(_raw_password) if _raw_password else ""

# Try to get full URL from Secret Manager first, fall back to constructing it
DATABASE_URL = os.environ.get(
    "dev-db-url",
    f"postgresql+psycopg2://myapp_user:{_encoded_password}@10.198.0.3:5432/myapp" if _encoded_password else None
)

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set. Check Secret Manager: 'dev-db-url' must be mounted as env var.")

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,       # checks connection health before use
    pool_recycle=3600,        # recycle connections every 1 hour
    connect_args={
        "connect_timeout": 10  # fail fast if DB unreachable
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ─── SQLAlchemy Models ────────────────────────────────────

class Name(Base):
    __tablename__ = "names"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

# ─── Pydantic Models ──────────────────────────────────────

class NameIn(BaseModel):
    name: str

class NameOut(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True

# ─── FastAPI App ──────────────────────────────────────────

app = FastAPI(title="Names API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    """Create database tables on app startup"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/verified")
    except Exception as e:
        print(f"⚠️  Warning: Could not create tables: {e}")
        # Don't crash — tables might already exist

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ─── Routes ───────────────────────────────────────────────

@app.post("/api/names", response_model=NameOut)
def create_name(name_in: NameIn, db: Session = Depends(get_db)):
    """Save a new name to database"""
    db_name = Name(name=name_in.name)
    db.add(db_name)
    db.commit()
    db.refresh(db_name)
    return db_name

@app.get("/api/names", response_model=list[NameOut])
def list_names(db: Session = Depends(get_db)):
    """Get all names, ordered by most recent first"""
    return db.query(Name).order_by(Name.created_at.desc()).all()

@app.get("/api/names/{name_id}", response_model=NameOut)
def get_name(name_id: int, db: Session = Depends(get_db)):
    """Get a single name by ID"""
    name = db.query(Name).filter(Name.id == name_id).first()
    if not name:
        raise HTTPException(status_code=404, detail="Name not found")
    return name

@app.delete("/api/names/{name_id}")
def delete_name(name_id: int, db: Session = Depends(get_db)):
    """Delete a name by ID"""
    name = db.query(Name).filter(Name.id == name_id).first()
    if not name:
        raise HTTPException(status_code=404, detail="Name not found")
    db.delete(name)
    db.commit()
    return {"message": "Name deleted"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "ok", "database": "unreachable", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)