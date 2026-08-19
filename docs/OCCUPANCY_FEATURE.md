# Zone Occupancy Tracking Feature

## Overview

Added live occupancy tracking to the campus safety system. The perception module now tracks person count per zone in real-time and sends occupancy updates to the backend regularly. The dashboard receives these updates via WebSocket and shows live occupancy gauges for each zone.

## New files added

### Backend
- `backend/routes/zones.py` — endpoints for occupancy data
- `backend/config.py` — zone capacities and settings
- Updated `backend/schemas.py` — `ZoneOccupancy` and `ZoneOccupancyOut` models
- Updated `backend/models.py` — `ZoneStatus` ORM table

### Perception
- `perception/config.py` — perception settings including zone capacities
- `perception/occupancy.py` — `OccupancyTracker` class and occupancy sender
- Updated `perception/main.py` — integrated occupancy tracking into main loop

## How it works

### Perception side

1. **Every frame:** Count persons in each zone by checking if their center point falls within the zone polygon
2. **Calculate occupancy:** `occupancy_percentage = current_count / capacity * 100`
3. **Detect trend:** Compare recent 5 frames vs older 5 frames (increasing/stable/decreasing)
4. **Send updates:** Every N frames (configurable), POST occupancy data to `/zones/occupancy` endpoint

```python
# Example occupancy update
{
  "zone": "Gate_3",
  "current_count": 8,
  "capacity": 10,
  "occupancy_percentage": 80.0,
  "trend": "stable",
  "timestamp": "2026-08-19T14:35:22Z"
}
```

### Backend side

1. **Receive:** `POST /zones/occupancy` endpoint ingests occupancy updates
2. **Store:** Saves/updates the `ZoneStatus` table (one row per zone)
3. **Broadcast:** Pushes occupancy update to all connected dashboard clients via WebSocket
4. **Query:** Dashboard can also poll `GET /zones/occupancy` to get all zones or `/zones/occupancy/{zone_name}` for a specific zone

### Dashboard side

1. **Connect:** Opens WebSocket to `/ws`
2. **Receive:** Listens for messages with `"type": "zone_occupancy"`
3. **Display:** Renders occupancy gauges per zone showing:
   - Current count / capacity
   - Percentage bar (0-100%, red if overcrowded >100%)
   - Trend indicator (up/down/stable arrow)

## Zone capacities

Configured in `config.py` (both backend and perception):

```python
ZONE_CAPACITIES = {
    "Gate_3": 10,           # main gate - safe limit 10
    "Gate_1": 12,
    "Gate_2": 10,
    "Canteen": 50,          # large area - safe limit 50
    "Restricted_Lab": 5,    # small lab - safe limit 5
    "Auditorium": 100,
}
```

These values are used to:
- Calculate occupancy percentage
- Alert if occupancy >= 90% of capacity (warning threshold)
- Alert if occupancy > 110% of capacity (critical - overcrowded)

## API Endpoints

### POST /zones/occupancy
Perception module sends occupancy updates here regularly.
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

### GET /zones/occupancy
Get current occupancy for all zones.
```json
{
  "zones": [
    {
      "zone": "Gate_3",
      "current_count": 8,
      "capacity": 10,
      "occupancy_percentage": 80.0,
      "trend": "stable",
      "timestamp": "2026-08-19T14:35:22Z"
    }
  ]
}
```

### GET /zones/occupancy/{zone_name}
Get occupancy for a specific zone.
```json
{
  "zone": "Gate_3",
  "current_count": 8,
  "capacity": 10,
  "occupancy_percentage": 80.0,
  "trend": "stable",
  "timestamp": "2026-08-19T14:35:22Z",
  "updated_at": "2026-08-19T14:35:22Z"
}
```

## WebSocket messages

Dashboard receives occupancy updates via WebSocket:
```json
{
  "type": "zone_occupancy",
  "data": {
    "zone": "Gate_3",
    "current_count": 8,
    "capacity": 10,
    "occupancy_percentage": 80.0,
    "trend": "stable",
    "timestamp": "2026-08-19T14:35:22Z"
  }
}
```

## Configuration

### Perception module (`perception/config.py`)
- `OCCUPANCY_SEND_INTERVAL` — send occupancy update every N frames (default: 5)
- `ZONE_CAPACITIES` — dict of zone name → capacity

### Backend module (`backend/config.py`)
- `ZONE_CAPACITIES` — same dict, for reference/validation
- `CROWD_ALERT_THRESHOLD` — alert if occupancy >= 90% of capacity
- `CROWD_CRITICAL_THRESHOLD` — critical alert if occupancy > 110% of capacity

## Database

New table: `zone_status`
```sql
CREATE TABLE zone_status (
  id INTEGER PRIMARY KEY,
  zone STRING UNIQUE NOT NULL,
  current_count INTEGER NOT NULL,
  capacity INTEGER NOT NULL,
  occupancy_percentage FLOAT NOT NULL,
  trend STRING,
  timestamp DATETIME NOT NULL,
  updated_at DATETIME NOT NULL
)
```

## Differences from incidents

- **Incidents:** Event-based, discrete alerts ("something bad happened")
- **Occupancy:** State-based, continuous updates ("here's what's happening now")

Incidents and occupancy are separate data streams:
- Incidents go to `/incidents` endpoint and populate the alert list
- Occupancy goes to `/zones/occupancy` endpoint and populates the occupancy gauges
- Both broadcast to dashboard via the same WebSocket connection but with different message types

## Trend detection algorithm

Compares occupancy over two time windows:
- Recent: average of last 5 frames
- Older: average of frames 5-10 frames ago
- If `recent > older + 0.5` → "increasing"
- If `recent < older - 0.5` → "decreasing"
- Otherwise → "stable"

The threshold of 0.5 people can be tuned in `occupancy.py` if needed.

## Future enhancements

- Store occupancy history and show charts of occupancy over time
- Predict when a zone will exceed capacity based on trend
- Set different capacity thresholds per time-of-day (e.g. higher during peak hours)
- Send proactive "capacity approaching" alerts at 80%, 90%, 100%
- Integrate with event scheduling to set expected capacity based on scheduled events
