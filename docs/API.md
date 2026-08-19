# API Reference

Base URL (local demo): `http://localhost:8000`

## Incidents

### `POST /incidents`
Perception module sends detected incidents here.

**Request body** (`IncidentIn`):
```json
{
  "incident_id": "inc_a1b2c3d4",
  "type": "unattended_baggage",
  "zone": "Gate_3",
  "timestamp": "2026-08-19T14:32:10Z",
  "tracked_object_id": 47,
  "dwell_time_seconds": 32.5,
  "detection_confidence": 0.89,
  "count": null
}
```

**Response** (`IncidentOut`): the saved incident, initially with `severity: null` until
the agent processes it (broadcast separately over WebSocket once ready).

### `GET /incidents`
List incidents for the dashboard. Optional query params: `status`, `type_filter`, `zone`.

### `GET /incidents/{incident_id}`
Get a single incident by ID, including agent reasoning and status.

## Operator actions

### `POST /incidents/{incident_id}/acknowledge`
```json
{ "operator_name": "Security Officer John" }
```

### `POST /incidents/{incident_id}/override`
```json
{ "new_severity": "critical", "reason": "Operator observed suspicious activity" }
```

### `POST /incidents/{incident_id}/false_positive`
```json
{ "reason": "Bag belongs to nearby vendor, confirmed on camera" }
```

## Zone occupancy

### `POST /zones/occupancy`
Perception module sends this regularly (every N frames), not just on alerts.
```json
{
  "zone": "Gate_3",
  "current_count": 8,
  "capacity": 10,
  "occupancy_percentage": 80.0,
  "trend": "stable",
  "timestamp": "2026-08-19T14:35:22Z"
}
```

### `GET /zones/occupancy`
All zones' current occupancy.

### `GET /zones/occupancy/{zone_name}`
Single zone's current occupancy.

## WebSocket

### `WS /ws`
Dashboard connects here and receives push messages. No client messages expected.

**Message types:**

```json
{ "type": "incident", "data": { ...IncidentOut, "severity": null } }
```
Sent immediately when an incident is saved, before the agent has processed it.

```json
{ "type": "incident_enriched", "data": { ...IncidentOut, "severity": "high", ... } }
```
Sent once the agent finishes analysis.

```json
{ "type": "incident_updated", "data": { ...IncidentOut } }
```
Sent when an operator acknowledges, overrides, or marks false positive.

```json
{ "type": "zone_occupancy", "data": { "zone": "Gate_3", "current_count": 8, ... } }
```
Sent on every occupancy update from perception.

## Health check

### `GET /health`
```json
{ "status": "ok" }
```

## Interactive docs

FastAPI auto-generates a Swagger UI at `http://localhost:8000/docs` once the backend is
running — useful for testing endpoints without curl.
