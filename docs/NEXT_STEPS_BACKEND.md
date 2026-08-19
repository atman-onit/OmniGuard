# Next Steps for Backend Engineer

You now have the foundation layer (schemas.py, config.py, database.py, models.py). Here's what to build next in order.

---

## STEP 1: Create .env file (5 minutes)

Create `.env` file in project root:

```bash
# Database
DATABASE_URL=sqlite:///./incidents.db

# LLM / Agent
ANTHROPIC_API_KEY=sk-your-key-here
```

If you don't have an Anthropic API key yet:
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Create an API key
4. Paste it above

---

## STEP 2: Create main.py (FastAPI app) (30 minutes)

Location: `backend/main.py`

This is the entry point that ties everything together.

```python
"""
main.py
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db, close_db
from .routes import incidents, actions, zones
from .websocket import manager

# Create FastAPI app
app = FastAPI(
    title="Campus Safety Intelligence Platform",
    description="Real-time campus surveillance with AI incident detection",
    version="1.0.0"
)

# Add CORS middleware (allow dashboard to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(incidents.router)
app.include_router(actions.router)
app.include_router(zones.router)

# Startup/shutdown events
@app.on_event("startup")
async def startup():
    await init_db()
    print("✓ Application started")

@app.on_event("shutdown")
async def shutdown():
    await close_db()
    print("✓ Application stopped")

# Health check
@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**To run:**
```bash
cd backend
python3 main.py
# Or with uvicorn directly:
uvicorn main:app --reload --port 8000
```

The app will:
- ✅ Create tables on startup
- ✅ Expose /health endpoint
- ✅ Ready to receive POSTs from perception

---

## STEP 3: Create routes/incidents.py (1-2 hours)

Location: `backend/routes/incidents.py`

This is where the main incident ingestion endpoint lives.

```python
"""
routes/incidents.py
Endpoints for incident management.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from ..database import get_db
from ..schemas import IncidentIn, IncidentOut
from ..models import Incident
from ..websocket import manager

router = APIRouter(prefix="/incidents", tags=["incidents"])

@router.post("", response_model=IncidentOut)
async def receive_incident(
    incident: IncidentIn,
    db: Session = Depends(get_db)
):
    """
    Receive incident from perception module.
    
    1. Save to DB immediately (fail-safe)
    2. Broadcast to dashboard
    3. (Later: trigger agent for severity/correlation)
    """
    # Create database object
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
    
    # Save to database (fail-safe)
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    
    # Broadcast to dashboard
    await manager.broadcast({
        "type": "incident",
        "data": IncidentOut.from_orm(db_incident).model_dump()
    })
    
    return IncidentOut.from_orm(db_incident)

@router.get("", response_model=list[IncidentOut])
async def list_incidents(
    status: str = None,
    type_filter: str = None,
    zone: str = None,
    db: Session = Depends(get_db)
):
    """List all incidents with optional filters."""
    query = db.query(Incident).order_by(Incident.created_at.desc())
    
    if status:
        query = query.filter(Incident.status == status)
    if type_filter:
        query = query.filter(Incident.type == type_filter)
    if zone:
        query = query.filter(Incident.zone == zone)
    
    incidents = query.all()
    return [IncidentOut.from_orm(i) for i in incidents]

@router.get("/{incident_id}", response_model=IncidentOut)
async def get_incident(incident_id: str, db: Session = Depends(get_db)):
    """Get single incident by ID."""
    incident = db.query(Incident).filter(
        Incident.incident_id == incident_id
    ).first()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    return IncidentOut.from_orm(incident)
```

---

## STEP 4: Create routes/actions.py (1 hour)

Location: `backend/routes/actions.py`

Operator actions: acknowledge, override, mark false positive.

```python
"""
routes/actions.py
Endpoints for operator actions on incidents.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from ..database import get_db
from ..schemas import AckRequest, OverrideRequest, FalsePositiveRequest, IncidentOut
from ..models import Incident
from ..websocket import manager

router = APIRouter(prefix="/incidents", tags=["actions"])

@router.post("/{incident_id}/acknowledge")
async def acknowledge_incident(
    incident_id: str,
    request: AckRequest,
    db: Session = Depends(get_db)
):
    """Operator acknowledges an incident."""
    incident = db.query(Incident).filter(
        Incident.incident_id == incident_id
    ).first()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    incident.status = "acknowledged"
    incident.acknowledged_at = datetime.utcnow()
    incident.acknowledged_by = request.operator_name
    incident.updated_at = datetime.utcnow()
    
    db.commit()
    
    # Broadcast update
    await manager.broadcast({
        "type": "incident_updated",
        "data": IncidentOut.from_orm(incident).model_dump()
    })
    
    return {"status": "acknowledged", "incident_id": incident_id}

@router.post("/{incident_id}/override")
async def override_severity(
    incident_id: str,
    request: OverrideRequest,
    db: Session = Depends(get_db)
):
    """Operator overrides agent's severity judgment."""
    incident = db.query(Incident).filter(
        Incident.incident_id == incident_id
    ).first()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    incident.severity = request.new_severity
    incident.reasoning_summary = f"Override: {request.reason}"
    incident.updated_at = datetime.utcnow()
    
    db.commit()
    
    # Broadcast update
    await manager.broadcast({
        "type": "incident_updated",
        "data": IncidentOut.from_orm(incident).model_dump()
    })
    
    return {"status": "overridden", "new_severity": request.new_severity}

@router.post("/{incident_id}/false_positive")
async def mark_false_positive(
    incident_id: str,
    request: FalsePositiveRequest,
    db: Session = Depends(get_db)
):
    """Operator marks incident as false positive."""
    incident = db.query(Incident).filter(
        Incident.incident_id == incident_id
    ).first()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    incident.status = "false_positive"
    incident.reasoning_summary = f"False positive: {request.reason}"
    incident.updated_at = datetime.utcnow()
    
    db.commit()
    
    # Broadcast update
    await manager.broadcast({
        "type": "incident_updated",
        "data": IncidentOut.from_orm(incident).model_dump()
    })
    
    return {"status": "marked_false_positive"}
```

---

## STEP 5: Create websocket.py (30 minutes)

Location: `backend/websocket.py`

Real-time push to all connected dashboard clients.

```python
"""
websocket.py
WebSocket connection management for broadcasting updates to dashboards.
"""
from fastapi import WebSocket
from typing import Set

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        print(f"✓ Client connected ({len(self.active_connections)} total)")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        print(f"✓ Client disconnected ({len(self.active_connections)} total)")
    
    async def broadcast(self, message: dict):
        """Send message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"✗ Failed to send to client: {e}")

manager = ConnectionManager()

# WebSocket route (goes in main.py or routes)
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back or process commands
    except Exception:
        manager.disconnect(websocket)
```

Add to main.py:
```python
from .websocket import websocket_endpoint

@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    await websocket_endpoint(websocket)
```

---

## STEP 6: Create routes/__init__.py (5 minutes)

Location: `backend/routes/__init__.py`

```python
"""
routes package
"""
from . import incidents, actions, zones

__all__ = ["incidents", "actions", "zones"]
```

---

## TESTING CHECKLIST

Once you've built the above, test:

```bash
# 1. Start backend
python3 backend/main.py
# Should see: ✓ Database tables created/verified, ✓ Application started

# 2. Check health
curl http://localhost:8000/health
# Should return: {"status":"ok"}

# 3. Check API docs
open http://localhost:8000/docs
# Interactive Swagger UI showing all endpoints

# 4. Send test incident (from perception module or manually)
curl -X POST http://localhost:8000/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "inc_test_001",
    "type": "overcrowding",
    "zone": "Gate_3",
    "timestamp": "2026-08-19T14:35:22Z",
    "count": 8
  }'
# Should return full incident with "status": "new"

# 5. List incidents
curl http://localhost:8000/incidents
# Should return array with your test incident

# 6. Acknowledge incident
curl -X POST http://localhost:8000/incidents/inc_test_001/acknowledge \
  -H "Content-Type: application/json" \
  -d '{"operator_name": "Security John"}'
# Should show status changed to "acknowledged"
```

---

## AFTER THIS: AGENT LAYER

Once the above works, you'll build:
- `agent/triage_agent.py` — LLM call with tool-use
- `agent/tools.py` — agent tool definitions
- `agent/fallback.py` — deterministic fallback
- Modify `routes/incidents.py` to call agent after saving

But the architecture is now in place for all of this.

---

## File Structure So Far

```
backend/
  __init__.py
  config.py          ✅ (you have this)
  database.py        ✅ (you have this)
  models.py          ✅ (you have this)
  schemas.py         ✅ (you have this)
  main.py            ← BUILD THIS NEXT
  websocket.py       ← THEN THIS
  routes/
    __init__.py      ← CREATE THIS
    incidents.py     ← AND THIS
    actions.py       ← AND THIS
    zones.py         ✅ (you have this)
  agent/
    (empty for now, build later)
```

---

## Summary: What To Do Next

1. **Create `.env`** with DATABASE_URL and ANTHROPIC_API_KEY
2. **Create `main.py`** — FastAPI app entry point
3. **Create `websocket.py`** — connection manager
4. **Create `routes/incidents.py`** — incident ingestion endpoint
5. **Create `routes/actions.py`** — operator action endpoints
6. **Create `routes/__init__.py`** — package init
7. **Test all endpoints** with curl or Postman
8. **Verify WebSocket** by connecting a client

Once this is done, the perception module can start sending incidents and the backend can receive, store, and broadcast them. The agent layer comes after.

**Time estimate:** 3-4 hours total for one person, or 1.5-2 hours if two people work on it in parallel (one on main.py + websocket.py, one on routes/incidents.py + routes/actions.py).
