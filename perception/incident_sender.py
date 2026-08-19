
#Builds a structured incident matching the schema the backend expects (IncidentIn),and sends it via HTTP POST. Never crashes the main perception loop on failure.

import uuid
from datetime import datetime
import requests
from config import INCIDENT_ENDPOINT


def build_incident(incident_type, zone=None, tracked_object_id=None,
                    dwell_time_seconds=None, count=None, detection_confidence=None):
    #Build a structured incident matching backend/schemas.py IncidentIn exactly.

    return {
        "incident_id": f"inc_{uuid.uuid4().hex[:8]}",
        "type": incident_type,
        "zone": zone,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "tracked_object_id": tracked_object_id,
        "dwell_time_seconds": dwell_time_seconds,
        "detection_confidence": detection_confidence,
        "count": count,
    }


def send_incident(incident, endpoint=INCIDENT_ENDPOINT):
    try:
        response = requests.post(endpoint, json=incident, timeout=2)
        if response.status_code == 200:
            print(f"Sent {incident['type']} incident: {incident['incident_id']}")
        else:
            print(f"Backend returned {response.status_code}: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send incident: {e}")