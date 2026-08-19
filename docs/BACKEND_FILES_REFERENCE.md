# Backend Files Reference

Complete listing of the three core backend files that define data structure and database setup.

---

## File 1: `backend/schemas.py`

**Location:** `/home/claude/campus-safety/backend/schemas.py`

**Purpose:** Pydantic models for request/response validation and API documentation

**Main classes:**
- `IncidentIn` — what perception sends (8 fields)
- `IncidentOut` — what dashboard receives (19 fields)
- `AgentOutput` — LLM agent produces (5 fields)
- `ZoneOccupancy` — live zone status (6 fields)
- `AckRequest`, `OverrideRequest`, `FalsePositiveRequest` — operator actions

**Key responsibilities:**
- Validate incoming JSON from perception module
- Document API endpoints
- Convert database objects to JSON
- Enforce field constraints (e.g., occupancy_percentage must be 0-200)

---

## File 2: `backend/models.py`

**Location:** `/home/claude/campus-safety/backend/models.py`

**Purpose:** SQLAlchemy ORM models that define database tables

**Main classes:**
- `Incident` — stores detected incidents (20 columns)
- `ZoneStatus` — stores live occupancy per zone (7 columns)

**Incident columns:**
```
id, incident_id, type, zone, timestamp, 
tracked_object_id, dwell_time_seconds, detection_confidence, count,
severity, reasoning_summary, correlated_incident_ids, recommended_action, notification_draft,
status, acknowledged_at, acknowledged_by,
created_at, updated_at
```

**ZoneStatus columns:**
```
id, zone, current_count, capacity, occupancy_percentage, trend,
timestamp, updated_at
```

**Key responsibilities:**
- Define table structure
- Set up indexes for query performance
- Enforce relationships and constraints
- Auto-manage timestamps (created_at, updated_at)

---

## File 3: `backend/database.py`

**Location:** `/home/claude/campus-safety/backend/database.py`

**Purpose:** Database connection setup and session management

**Main functions:**
- `create_engine()` — creates DB connection (SQLite or PostgreSQL)
- `SessionLocal` — factory for creating sessions
- `create_all_tables()` — creates tables on startup
- `get_db()` — FastAPI dependency providing sessions to routes
- `init_db()` — startup hook to initialize database
- `close_db()` — shutdown hook to clean up connections

**Key responsibilities:**
- Manage database connection lifecycle
- Provide sessions to routes
- Create tables on application startup
- Handle different database backends (SQLite, PostgreSQL, etc)

---

## How They Connect

```
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Route                              │
│                                                             │
│  @app.post("/incidents")                                   │
│  async def receive_incident(                               │
│      incident: IncidentIn,          ← schemas.py validates │
│      db: Session = Depends(get_db)  ← database.py provides │
│  ):                                                         │
│      db_incident = Incident(        ← models.py defines   │
│          incident_id=incident.incident_id,                │
│          type=incident.type,                              │
│          ...                                               │
│      )                                                     │
│      db.add(db_incident)                                  │
│      db.commit()                                          │
│                                                           │
│      return IncidentOut.from_orm(    ← schemas.py converts│
│          db_incident                                     │
│      )                                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Complete File Listing

### `backend/schemas.py`

```python
"""
schemas.py - Pydantic models for API validation and documentation
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# INCIDENT SCHEMAS

class IncidentIn(BaseModel):
    """Input from perception module - what we receive via POST"""
    incident_id: str
    type: str  # 'overcrowding' | 'unattended_baggage' | 'intrusion' | 'fire'
    zone: Optional[str] = None
    timestamp: str  # ISO 8601
    tracked_object_id: Optional[int] = None
    dwell_time_seconds: Optional[float] = None
    detection_confidence: Optional[float] = None
    count: Optional[int] = None


class AgentOutput(BaseModel):
    """Output from LLM agent - what we add to incident"""
    severity: str  # 'critical' | 'high' | 'medium' | 'low'
    reasoning_summary: str
    correlated_incident_ids: List[str] = []
    recommended_action: str
    notification_draft: str


class IncidentOut(BaseModel):
    """Full incident returned to dashboard - combines all layers"""
    # From perception
    incident_id: str
    type: str
    zone: Optional[str]
    timestamp: str
    tracked_object_id: Optional[int]
    dwell_time_seconds: Optional[float]
    detection_confidence: Optional[float]
    count: Optional[int]
    
    # From agent
    severity: Optional[str] = None
    reasoning_summary: Optional[str] = None
    correlated_incident_ids: List[str] = []
    recommended_action: Optional[str] = None
    notification_draft: Optional[str] = None
    
    # Status
    status: str = "new"  # 'new' | 'acknowledged' | 'resolved' | 'false_positive'
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# OPERATOR ACTION SCHEMAS

class AckRequest(BaseModel):
    operator_name: str


class OverrideRequest(BaseModel):
    new_severity: str  # 'critical' | 'high' | 'medium' | 'low'
    reason: str


# ZONE OCCUPANCY SCHEMAS

class ZoneOccupancy(BaseModel):
    """Live occupancy from perception module"""
    zone: str
    current_count: int
    capacity: int
    occupancy_percentage: float  # 0-200
    timestamp: str  # ISO 8601
    trend: Optional[str] = None  # 'increasing' | 'stable' | 'decreasing'


class ZoneOccupancyOut(BaseModel):
    """Occupancy response from database"""
    zone: str
    current_count: int
    capacity: int
    occupancy_percentage: float
    timestamp: str
    trend: Optional[str] = None
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

---

### `backend/models.py`

```python
"""
models.py - SQLAlchemy ORM models (database schema)
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Incident(Base):
    """Main incident table - stores all detected incidents"""
    __tablename__ = "incidents"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # From perception (immutable)
    incident_id = Column(String, unique=True, index=True, nullable=False)
    type = Column(String, index=True, nullable=False)
    zone = Column(String, index=True, nullable=True)
    timestamp = Column(String, nullable=False)
    tracked_object_id = Column(Integer, nullable=True, index=True)
    dwell_time_seconds = Column(Float, nullable=True)
    detection_confidence = Column(Float, nullable=True)
    count = Column(Integer, nullable=True)
    
    # From agent (added later)
    severity = Column(String, index=True, nullable=True)
    reasoning_summary = Column(String, nullable=True)
    correlated_incident_ids = Column(JSON, nullable=True)
    recommended_action = Column(String, nullable=True)
    notification_draft = Column(String, nullable=True)
    
    # Status (updated by operators)
    status = Column(String, default="new", index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Incident {self.incident_id} {self.type} {self.severity}>"


class ZoneStatus(Base):
    """Live occupancy per zone"""
    __tablename__ = "zone_status"
    
    id = Column(Integer, primary_key=True, index=True)
    
    zone = Column(String, index=True, nullable=False, unique=True)
    current_count = Column(Integer, nullable=False)
    capacity = Column(Integer, nullable=False)
    occupancy_percentage = Column(Float, nullable=False)
    trend = Column(String, nullable=True)
    
    timestamp = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ZoneStatus {self.zone}: {self.current_count}/{self.capacity}>"
```

---

### `backend/database.py`

```python
"""
database.py - Database connection and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models import Base
from .config import DATABASE_URL


# Create engine
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    poolclass = StaticPool
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        poolclass=poolclass,
        echo=False
    )
else:
    engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def create_all_tables():
    """Create all tables on startup"""
    Base.metadata.create_all(bind=engine)
    print(f"✓ Database tables created")


def get_db() -> Session:
    """FastAPI dependency providing database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """Called on app startup"""
    create_all_tables()


async def close_db():
    """Called on app shutdown"""
    engine.dispose()
    print("✓ Database connection closed")
```

---

## Usage in Routes

### Receiving an incident from perception:
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .database import get_db
from .schemas import IncidentIn, IncidentOut
from .models import Incident

router = APIRouter()

@router.post("/incidents", response_model=IncidentOut)
async def receive_incident(
    incident: IncidentIn,  # Pydantic validates
    db: Session = Depends(get_db)  # Database session
):
    # Create ORM model from validated Pydantic model
    db_incident = Incident(
        incident_id=incident.incident_id,
        type=incident.type,
        zone=incident.zone,
        timestamp=incident.timestamp,
        tracked_object_id=incident.tracked_object_id,
        dwell_time_seconds=incident.dwell_time_seconds,
        detection_confidence=incident.detection_confidence,
        count=incident.count,
        status="new"
    )
    
    # Save to database
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    
    # Convert back to Pydantic for response
    return IncidentOut.from_orm(db_incident)
```

### Querying incidents:
```python
@router.get("/incidents")
async def list_incidents(db: Session = Depends(get_db)):
    incidents = db.query(Incident).order_by(
        Incident.created_at.desc()
    ).all()
    return [IncidentOut.from_orm(i) for i in incidents]
```

---

## Environment Setup

Create a `.env` file:
```bash
DATABASE_URL=sqlite:///./incidents.db
ANTHROPIC_API_KEY=sk-...
```

Or for PostgreSQL:
```bash
DATABASE_URL=postgresql://user:password@localhost/campus_safety
```

---

## Summary

These three files form the complete data layer:

| File | Type | Validates | Stores |
|---|---|---|---|
| `schemas.py` | Pydantic | API inputs/outputs | — |
| `models.py` | SQLAlchemy | — | Database structure |
| `database.py` | Connection | — | Sessions, initialization |

Use them in your routes like:
```python
def route_handler(incident: IncidentIn, db: Session = Depends(get_db)):
    db_obj = Model(...) # from models.py
    db.add(db_obj)
    return SchemaOut.from_orm(db_obj) # from schemas.py
```
