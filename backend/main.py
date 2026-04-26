from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime
import os
from urllib.parse import urlparse

# ─── Database Configuration ───────────────────────────────

# For Cloud SQL: Set DATABASE_URL environment variable
# Format: postgresql://user:password@/dbname?unix_socket_dir=/cloudsql/PROJECT:REGION:INSTANCE
# For local PostgreSQL: postgresql://postgres:postgres@localhost:5432/names_db
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:030615@localhost:5432/mytable"
)

# Parse the database URL to extract components
parsed_url = urlparse(DATABASE_URL)
db_name = parsed_url.path.lstrip('/')
admin_database_url = f"{parsed_url.scheme}://{parsed_url.netloc}/postgres"

# Create database if it doesn't exist
try:
    admin_engine = create_engine(admin_database_url, echo=False, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        # Check if database exists
        result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
        if not result.fetchone():
            # Database doesn't exist, create it
            conn.execute(text(f"CREATE DATABASE {db_name}"))
            print(f"Created database: {db_name}")
except Exception as e:
    print(f"Warning: Could not check/create database: {e}")

# Now connect to the target database
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ─── SQLAlchemy Models ────────────────────────────────────

class Name(Base):
    __tablename__ = "names"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

# Create all tables on startup
Base.metadata.create_all(bind=engine)

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
    allow_origins=["*"],  # Change to specific domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    names = db.query(Name).order_by(Name.created_at.desc()).all()
    return names

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
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)