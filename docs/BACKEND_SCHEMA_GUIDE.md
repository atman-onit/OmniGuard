# Backend Schema & Database Guide

Three files work together to define and manage data in the backend:

## 1. `schemas.py` — The API Contract

**Purpose:** Pydantic models that define request/response shapes. These validate data coming in and going out.

**Key classes:**
- `IncidentIn` — what perception module POSTs (8 fields from CV)
- `AgentOutput` — what LLM agent produces (5 fields)
- `IncidentOut` — full incident returned to dashboard (all fields)
- `ZoneOccupancy` — occupancy update from perception
- `AckRequest`, `OverrideRequest`, `FalsePositiveRequest` — operator actions

**Why it matters:**
- Validates incoming data (if perception sends wrong shape, endpoint rejects it)
- Documents the API (shows dashboard developer what response looks like)
- Converts DB objects to JSON automatically (`from_attributes = True`)

**Example use in a route:**
```python
from schemas import IncidentIn, IncidentOut

@app.post("/incidents", response_model=IncidentOut)
async def receive_incident(incident: IncidentIn, db: Session = Depends(get_db)):
    # incident is validated against IncidentIn schema
    # response will be validated against IncidentOut schema
    ...
```

---

## 2. `models.py` — The Database Schema

**Purpose:** SQLAlchemy ORM models that define what tables exist and what columns they have.

**Key tables:**
- `Incident` — main incident table (20 columns)
- `ZoneStatus` — live zone occupancy (7 columns)

**Column types:**
- `String` — text (incident_id, zone, type)
- `Integer` — whole numbers (count, tracked_object_id, id)
- `Float` — decimals (confidence, occupancy_percentage)
- `DateTime` — timestamps (created_at, updated_at)
- `JSON` — lists/dicts (correlated_incident_ids)

**Why `nullable=True/False` matters:**
- `incident_id` → `nullable=False` (always required from perception)
- `severity` → `nullable=True` (added later by agent)
- `acknowledged_at` → `nullable=True` (added later by operator, may never happen)

**Example table structure:**
```
CREATE TABLE incidents (
    id INTEGER PRIMARY KEY,
    incident_id STRING UNIQUE NOT NULL,
    type STRING NOT NULL,
    zone STRING,
    timestamp STRING NOT NULL,
    tracked_object_id INTEGER,
    dwell_time_seconds FLOAT,
    detection_confidence FLOAT,
    count INTEGER,
    severity STRING,
    reasoning_summary STRING,
    correlated_incident_ids JSON,
    recommended_action STRING,
    notification_draft STRING,
    status STRING DEFAULT 'new',
    acknowledged_at DATETIME,
    acknowledged_by STRING,
    created_at DATETIME DEFAULT NOW(),
    updated_at DATETIME DEFAULT NOW()
)
```

---

## 3. `database.py` — Connection & Session Management

**Purpose:** Sets up database connection, creates tables, and provides session dependency for routes.

**Key functions:**
- `create_engine()` — connects to database (SQLite file or PostgreSQL)
- `SessionLocal()` — factory that creates new database sessions
- `create_all_tables()` — creates tables on startup
- `get_db()` — FastAPI dependency that provides a session to routes

**Why sessions matter:**
- Each route request gets its own database session
- Automatically closed after request completes
- Prevents connection leaks and ensures thread safety

**Example use in a route:**
```python
@app.get("/incidents")
async def list_incidents(db: Session = Depends(get_db)):
    # db is a live database session
    incidents = db.query(Incident).all()
    # session auto-closes after function returns
    return incidents
```

---

## How They Work Together

```
Perception Module sends POST /incidents
    ↓
    Pydantic validates against IncidentIn schema (schemas.py)
    ↓
    Route handler receives validated data
    ↓
    get_db() provides a Session (database.py)
    ↓
    Route creates Incident object using models.py
    ↓
    Session saves to database (INSERT)
    ↓
    ORM converts Incident model to IncidentOut schema (schemas.py)
    ↓
    IncidentOut returned as JSON to perception module
```

---

## Data Flow: Perception → Schema → Database → Dashboard

### Step 1: Perception sends this (IncidentIn shape)
```json
{
    "incident_id": "inc_a1b2c3d4",
    "type": "overcrowding",
    "zone": "Gate_3",
    "timestamp": "2026-08-19T14:35:22Z",
    "count": 8,
    "tracked_object_id": null,
    "dwell_time_seconds": null,
    "detection_confidence": null
}
```

### Step 2: Pydantic validates it matches IncidentIn
- Checks: incident_id is string ✓
- Checks: type is one of the allowed values ✓
- Checks: count is integer or None ✓
- If anything is wrong, return 422 validation error

### Step 3: Route handler creates database object
```python
db_incident = Incident(
    incident_id="inc_a1b2c3d4",
    type="overcrowding",
    zone="Gate_3",
    timestamp="2026-08-19T14:35:22Z",
    count=8,
    tracked_object_id=None,
    dwell_time_seconds=None,
    detection_confidence=None,
    status="new",  # auto-set
    created_at=datetime.utcnow(),  # auto-set
    updated_at=datetime.utcnow()   # auto-set
)
db.add(db_incident)
db.commit()
```

### Step 4: Row is inserted into database
```sql
INSERT INTO incidents (
    incident_id, type, zone, timestamp, count, 
    tracked_object_id, dwell_time_seconds, detection_confidence,
    status, created_at, updated_at
) VALUES (
    'inc_a1b2c3d4', 'overcrowding', 'Gate_3', '2026-08-19T14:35:22Z', 8,
    NULL, NULL, NULL,
    'new', '2026-08-19T14:35:22.123Z', '2026-08-19T14:35:22.123Z'
)
```

### Step 5: ORM converts Incident object to IncidentOut schema
```python
# SQLAlchemy ORM model (models.py)
incident = db.query(Incident).filter(
    Incident.incident_id == "inc_a1b2c3d4"
).first()

# Pydantic schema converts it (schemas.py)
incident_out = IncidentOut.from_orm(incident)
# Returns:
{
    "incident_id": "inc_a1b2c3d4",
    "type": "overcrowding",
    "zone": "Gate_3",
    "timestamp": "2026-08-19T14:35:22Z",
    "count": 8,
    "tracked_object_id": null,
    "dwell_time_seconds": null,
    "detection_confidence": null,
    "severity": null,
    "reasoning_summary": null,
    "correlated_incident_ids": [],
    "recommended_action": null,
    "notification_draft": null,
    "status": "new",
    "acknowledged_at": null,
    "acknowledged_by": null,
    "created_at": "2026-08-19T14:35:22.123Z",
    "updated_at": "2026-08-19T14:35:22.123Z"
}
```

### Step 6: JSON returned to perception (or broadcast to dashboard)
```json
[
    {
        "incident_id": "inc_a1b2c3d4",
        "type": "overcrowding",
        ...
    }
]
```

---

## Database Configuration

Set `DATABASE_URL` in `.env`:

```bash
# SQLite (default, good for demo)
DATABASE_URL=sqlite:///./incidents.db

# PostgreSQL (production)
DATABASE_URL=postgresql://user:password@localhost:5432/campus_safety
```

The `database.py` file automatically handles connection details:
```python
if DATABASE_URL.startswith("sqlite"):
    # SQLite specific options
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # PostgreSQL
    engine = create_engine(DATABASE_URL)
```

---

## Key Field Attributes

### From Perception (immutable after creation)
```python
incident_id: str       # Unique ID, never changes
type: str              # Type of incident, never changes
zone: Optional[str]    # Where it happened, never changes
timestamp: str         # When detected, never changes
```

### Backend Auto-fills (on creation)
```python
id: int                           # DB primary key
created_at: datetime              # When saved
updated_at: datetime              # When last modified
status: str = "new"               # Starts as "new"
```

### Agent fills (after processing)
```python
severity: Optional[str] = None    # Assigned by LLM
reasoning_summary: Optional[str]  # Why severity assigned
correlated_incident_ids: JSON     # Linked incidents
recommended_action: Optional[str] # What to do
notification_draft: Optional[str] # Alert message
```

### Human fills (on operator action)
```python
acknowledged_at: Optional[datetime] = None    # When acked
acknowledged_by: Optional[str] = None         # Who acked
status: str                                   # Changed to "acknowledged"
updated_at: datetime                          # Updated timestamp
```

---

## Indexes for Query Performance

These fields are indexed (`index=True` in models.py) for fast queries:
- `incident_id` — find specific incident
- `type` — filter by incident type
- `zone` — filter by zone
- `status` — find all "new" alerts
- `severity` — sort by severity
- `created_at` — chronological queries
- `tracked_object_id` — find incidents about an object

---

## On Startup

The FastAPI app calls `init_db()`:
```python
from database import init_db

@app.on_event("startup")
async def startup():
    await init_db()  # Creates tables if they don't exist
```

This ensures tables exist before any requests arrive.

---

## Summary

| File | Purpose | Key Classes |
|---|---|---|
| `schemas.py` | API validation | IncidentIn, IncidentOut, AgentOutput, ZoneOccupancy |
| `models.py` | Database structure | Incident, ZoneStatus |
| `database.py` | Connection mgmt | create_all_tables(), get_db(), SessionLocal |

All three must work together:
- Schema validates data shape
- Models define database structure
- Database manages connections and sessions
