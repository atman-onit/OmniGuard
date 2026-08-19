# Complete Properties Reference

## All properties in the incident system, organized by source and when they're set

---

## SOURCE 1: Perception Module sends these (IncidentIn)

| Property | Type | Required? | Set by | When | Example |
|---|---|---|---|---|---|
| `incident_id` | string | ✅ YES | Perception module | At detection | `"inc_a1b2c3d4"` |
| `type` | string | ✅ YES | Perception module | At detection | `"unattended_baggage"` |
| `zone` | string | ❌ optional | Perception module | At detection (if rule applies to zone) | `"Gate_3"` |
| `timestamp` | string (ISO 8601) | ✅ YES | Perception module | At detection | `"2026-08-19T14:32:10Z"` |
| `tracked_object_id` | integer | ❌ optional | Perception module | At detection (for baggage/intrusion) | `47` |
| `dwell_time_seconds` | float | ❌ optional | Perception module | At detection (for baggage rule) | `32.5` |
| `detection_confidence` | float (0-1) | ❌ optional | Perception module | At detection (YOLO confidence) | `0.89` |
| `count` | integer | ❌ optional | Perception module | At detection (for crowd rule) | `5` |

### Example IncidentIn payload:
```json
{
  "incident_id": "inc_a1b2c3d4",
  "type": "unattended_baggage",
  "zone": "Gate_3",
  "timestamp": "2026-08-19T14:32:10Z",
  "tracked_object_id": 47,
  "dwell_time_seconds": 32.5,
  "detection_confidence": 0.89
}
```

---

## SOURCE 2: Backend adds these on ingestion (auto-populated)

| Property | Type | Set by | When | Example |
|---|---|---|---|---|
| `id` | integer (DB primary key) | PostgreSQL/SQLite | On row insert | `1` |
| `created_at` | datetime | Backend (sqlalchemy default) | On row insert | `2026-08-19T14:32:10Z` |
| `updated_at` | datetime | Backend (sqlalchemy onupdate) | On row insert/update | `2026-08-19T14:32:10Z` |
| `status` | string | Backend (hardcoded default) | On row insert | `"new"` |

---

## SOURCE 3: Agent adds these after LLM analysis (AgentOutput)

| Property | Type | Required? | Set by | When | Example |
|---|---|---|---|---|---|
| `severity` | string | ✅ YES | LLM agent | After agent processes incident | `"high"` |
| `reasoning_summary` | string | ✅ YES | LLM agent | After agent processes incident | `"Bag stationary 32s, owner absent, rapid movement detected"` |
| `correlated_incident_ids` | list of strings | ❌ optional | LLM agent | After agent looks up related incidents | `["inc_a1b2c2d0"]` |
| `recommended_action` | string | ✅ YES | LLM agent | After agent processes incident | `"dispatch_security"` |
| `notification_draft` | string | ✅ YES | LLM agent | After agent processes incident | `"Unattended bag flagged at Gate 3 — possible abandonment"` |

### Example AgentOutput payload:
```json
{
  "severity": "high",
  "reasoning_summary": "Bag unattended at Gate 3 for 32s, owner seen moving rapidly away",
  "correlated_incident_ids": ["inc_a1b2c2d0"],
  "recommended_action": "dispatch_security",
  "notification_draft": "Unattended bag at Gate 3, bag ID #47 — security dispatch requested"
}
```

---

## SOURCE 4: Human operator updates these (AckRequest, OverrideRequest)

| Property | Type | When updated | Set by | Example |
|---|---|---|---|---|
| `status` | string | On operator action | Operator | Change from `"new"` → `"acknowledged"` |
| `acknowledged_at` | datetime | When operator clicks "ack" | Backend (endpoint handler) | `2026-08-19T14:35:22Z` |
| `acknowledged_by` | string | When operator clicks "ack" | Operator (from request) | `"Security Officer John"` |

### Example AckRequest payload:
```json
{
  "operator_name": "Security Officer John"
}
```

### Example OverrideRequest payload:
```json
{
  "new_severity": "critical",
  "reason": "Operator observed suspicious activity on secondary camera"
}
```

---

## COMPLETE INCIDENT RECORD (IncidentOut - what dashboard gets)

This is the full object combining all of the above:

```json
{
  "incident_id": "inc_a1b2c3d4",
  "type": "unattended_baggage",
  "zone": "Gate_3",
  "timestamp": "2026-08-19T14:32:10Z",
  "tracked_object_id": 47,
  "dwell_time_seconds": 32.5,
  "detection_confidence": 0.89,
  "count": null,
  
  "severity": "high",
  "reasoning_summary": "Bag unattended at Gate 3 for 32s, owner absent",
  "correlated_incident_ids": ["inc_a1b2c2d0"],
  "recommended_action": "dispatch_security",
  "notification_draft": "Unattended bag flagged at Gate 3",
  
  "status": "new",
  "acknowledged_at": null,
  "acknowledged_by": null,
  
  "created_at": "2026-08-19T14:32:10Z",
  "updated_at": "2026-08-19T14:32:10Z"
}
```

---

## PROPERTY VALUES BY INCIDENT TYPE

### Type: `overcrowding`
```json
{
  "type": "overcrowding",
  "zone": "Gate_3",
  "count": 5,
  "tracked_object_id": null,
  "dwell_time_seconds": null
}
```

### Type: `unattended_baggage`
```json
{
  "type": "unattended_baggage",
  "zone": null,
  "tracked_object_id": 47,
  "dwell_time_seconds": 32.5,
  "detection_confidence": 0.89,
  "count": null
}
```

### Type: `intrusion`
```json
{
  "type": "intrusion",
  "zone": "Restricted_Lab",
  "tracked_object_id": 12,
  "detection_confidence": 0.92,
  "dwell_time_seconds": null,
  "count": null
}
```

### Type: `fire`
```json
{
  "type": "fire",
  "zone": "Building_A_Floor_2",
  "detection_confidence": 0.87,
  "tracked_object_id": null,
  "dwell_time_seconds": null,
  "count": null
}
```

---

## SEVERITY VALUES

| Severity | Typical incident type | Color on dashboard | Priority |
|---|---|---|---|
| `"critical"` | Fire, intrusion | Red | 🔴 Immediate dispatch |
| `"high"` | Unattended baggage, intrusion | Orange | 🟠 Urgent verification |
| `"medium"` | Overcrowding, sustained baggage | Yellow | 🟡 Monitor, may need action |
| `"low"` | Borderline crowd, new detection | Gray | ⚪ Log, low priority |

---

## STATUS VALUES (Incident lifecycle)

| Status | Meaning | Who sets it | When |
|---|---|---|---|
| `"new"` | Just arrived from perception, not yet reviewed | Backend (default) | On incident creation |
| `"acknowledged"` | Operator has reviewed and acknowledged | Operator | When operator clicks "acknowledge" |
| `"resolved"` | Operator resolved the incident (bag picked up, intruder left, etc) | Operator | When operator marks resolved |
| `"false_positive"` | Operator determined this was a detection error | Operator | When operator marks as false alarm |

---

## RECOMMENDED ACTION VALUES

| Action | Meaning | Who receives it |
|---|---|---|
| `"dispatch_security"` | Send security personnel to investigate | Control room operator |
| `"verify"` | Operator should visually verify before escalating | Control room operator |
| `"monitor"` | Keep watching, escalate if condition worsens | Control room operator |
| `"investigate"` | Could be something serious, look into it | Control room operator |
| `"none"` | No action recommended, just logged | Control room operator |

---

## FIELD USAGE BY MODULE

### Perception Module outputs:
- `incident_id`, `type`, `zone`, `timestamp`, `tracked_object_id`, `dwell_time_seconds`, `detection_confidence`, `count`

### Backend adds on ingestion:
- `id` (auto), `created_at` (auto), `updated_at` (auto), `status` (default "new")

### Agent adds after processing:
- `severity`, `reasoning_summary`, `correlated_incident_ids`, `recommended_action`, `notification_draft`

### Operator updates via dashboard:
- `status`, `acknowledged_at`, `acknowledged_by` (via POST requests)

### Dashboard displays:
- ALL of the above (full IncidentOut)

---

## DATABASE SCHEMA (SQLAlchemy)

```python
class Incident(Base):
    __tablename__ = "incidents"
    
    # PK
    id = Column(Integer, primary_key=True, index=True)
    
    # From perception
    incident_id = Column(String, unique=True, index=True, nullable=False)
    type = Column(String, index=True, nullable=False)
    zone = Column(String, index=True, nullable=True)
    timestamp = Column(String, nullable=False)
    tracked_object_id = Column(Integer, nullable=True, index=True)
    dwell_time_seconds = Column(Float, nullable=True)
    detection_confidence = Column(Float, nullable=True)
    count = Column(Integer, nullable=True)
    
    # From agent
    severity = Column(String, index=True, nullable=True)
    reasoning_summary = Column(String, nullable=True)
    correlated_incident_ids = Column(JSON, nullable=True)
    recommended_action = Column(String, nullable=True)
    notification_draft = Column(String, nullable=True)
    
    # Status
    status = Column(String, default="new", index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

---

## PYDANTIC MODELS (Request/Response contracts)

### IncidentIn (what perception sends)
- `incident_id`, `type`, `zone`, `timestamp`, `tracked_object_id`, `dwell_time_seconds`, `detection_confidence`, `count`

### AgentOutput (what agent produces)
- `severity`, `reasoning_summary`, `correlated_incident_ids`, `recommended_action`, `notification_draft`

### IncidentOut (what dashboard receives)
- All fields from IncidentIn + AgentOutput + `status`, `acknowledged_at`, `acknowledged_by`, `created_at`, `updated_at`

### AckRequest (operator acknowledges)
- `operator_name`

### OverrideRequest (operator changes severity)
- `new_severity`, `reason`

---

## SUMMARY: Property counts

- **Perception sends:** 8 properties
- **Backend auto-adds:** 4 properties
- **Agent adds:** 5 properties
- **Operator can update:** 3 properties
- **Total in DB row:** 20 properties
- **Total fields dashboard sees:** 20 properties
