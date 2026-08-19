# Perception Module Guide

File-by-file reference for the perception module. Owned by the perception engineer.

## File map

```
perception/
  config.py            thresholds, zone capacities, backend URLs
  zones.py              zone polygon definitions + point-in-zone check
  detector.py            YOLO wrapper (done, proven working)
  tracker.py              centroid tracker: assigns persistent IDs + dwell time
  rules.py                 crowd/baggage/intrusion/fire rule checks
  occupancy.py              live per-zone person counting + trend detection
  incident_sender.py         builds incident JSON, POSTs to backend
  main.py                     the loop tying everything together
  test_detector.py             proof-of-concept script (not part of the real pipeline)
```

## Data flow within the module

```
video frame
  -> detector.detect(frame)              -> raw detections (class, confidence, box)
  -> tracker.update(detections)          -> adds track_id, dwell_time_seconds
  -> occupancy_tracker.update(tracked)   -> per-zone counts, sent to backend periodically
  -> rules.check_*(tracked, zones)       -> incident dict, or None
  -> incident_sender.send_incident(...)  -> POST to backend if a rule fired
```

## `config.py`

Every tunable number lives here — thresholds, frame skip rate, zone capacities, backend
URL. Edit this file when live-tuning before a demo rather than touching rule logic.

## `zones.py`

Zones are polygons (lists of `(x, y)` pixel points) specific to one camera angle and
resolution. `point_in_zone(x, y, zone_name)` uses `cv2.pointPolygonTest` to check
membership.

**To define a zone for a new video:** take a screenshot of a representative frame, note
the pixel coordinates of the corners of the area you want, add them to `ZONES` in this
file. Redo this any time you switch camera source or resolution.

## `detector.py`

Wraps a pretrained YOLOv8 model (`yolov8n.pt`, the small/fast variant). Filters to
classes we care about: person, backpack, handbag, suitcase. Returns a clean list of
dicts, hiding the raw ultralytics API from the rest of the module.

## `tracker.py`

The hardest and most important file. Detection alone has no memory across frames — the
tracker assigns persistent `track_id`s by matching each frame's detections to the
previous frame's by nearest center-point distance, and accumulates `dwell_time_seconds`
for objects that haven't moved much. Without this, "has this bag been here 30 seconds"
is literally unanswerable.

## `rules.py`

Plain deterministic logic, one function per rule:
- `check_crowd` — person count per zone vs threshold
- `check_baggage` — bag dwell time vs threshold, with no person nearby
- `check_intrusion` — person center point inside a restricted zone polygon
- `check_fire` — placeholder wrapper for a fire/smoke classifier (stretch goal)

Each returns an incident dict or `None`. Kept in isolated functions because thresholds
get tuned constantly during testing.

## `occupancy.py`

Separate from incident rules — tracks live person count per zone every frame, computes
occupancy percentage against configured capacity, and detects a simple
increasing/stable/decreasing trend by comparing recent vs older frame windows. Sent to
the backend on a slower interval (`OCCUPANCY_SEND_INTERVAL`) than every frame, since it's
continuous state rather than a discrete alert.

## `incident_sender.py`

`build_incident(...)` fills the shared JSON schema agreed with the backend engineer.
`send_incident(...)` POSTs it with a short timeout and a try/except that never crashes
the main loop — a dropped incident is recoverable, a crashed perception loop mid-demo is
not.

## `main.py`

The actual loop: read frame → detect → track → update occupancy → run all rule checks →
send incident if any fired → repeat. Deliberately thin — if logic starts accumulating
here instead of in the modules above, it's leaked into the wrong file.

## Testing without real video

Before wiring everything into `main.py`, test `tracker.py` and `rules.py` in isolation
against hand-built fake detections — this proves your logic works before real footage
even exists, and lets you develop in parallel with your backend teammate.

## The one contract that matters

The JSON shape from `incident_sender.build_incident()` must exactly match `IncidentIn`
in the backend's `schemas.py`. Lock this down with your backend engineer before either
of you builds much further — see `docs/PROPERTIES_REFERENCE.md` for the full field
list.
