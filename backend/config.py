#Tune these numbers when testing against real videos. --JUST AN EXAMPLE FOR NOW

# Detection thresholds
CROWD_THRESHOLD = 5  
BAGGAGE_DWELL_SECONDS = 120  
DETECTION_CONFIDENCE = 0.5  # YOLO confidence cutoff (0-1)
TRACKER_MAX_DISAPPEARED = 70
  # frames before forgetting a tracked object

# Processing
FRAME_SKIP = 3  # process every Nth frame (1=every frame, 3=every 3rd for speed)
OCCUPANCY_SEND_INTERVAL = 5  # send occupancy update to backend every N frames

# Backend connection
BACKEND_URL = "http://localhost:8000"
INCIDENT_ENDPOINT = f"{BACKEND_URL}/incidents"
OCCUPANCY_ENDPOINT = f"{BACKEND_URL}/zones/occupancy"

# Zone capacities (for occupancy tracking)
# Maps zone name to max safe occupancy
ZONE_CAPACITIES = {
    "Gate_3": 10,           # main gate
    "Gate_1": 12,           # side gate
    "Gate_2": 10,           # side gate
    "Canteen": 50,          # large open area
    "Restricted_Lab": 5,    # small lab, max 5 people
    "Auditorium": 100,      # big hall
}