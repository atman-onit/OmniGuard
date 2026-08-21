import os
import json
import re
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from dotenv import load_dotenv
from anthropic import Anthropic

from schemas import IncidentIn, AgentOutput
from database import SessionLocal, Incident, ZoneOccupancyRecord

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("")
AGENT_MODEL = os.getenv("AGENT_MODEL", "claude-3-haiku-20240307")


client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

ZONE_STATIC_CONTEXT = {
    "Gate_3": {
        "description": "Busy pedestrian entrance gate." ,
        "risk_level":"high",
        "notes": "Unattended objects near gates should be treated as high risk " ,

    },
    "Gate_1":{
        "desciption": "Main entrance gate with moderate traffic.",
        "risk_level":"medium",
        "notes": "High foot traffic druring class change times.",

    },
    "Restricted_Lab":{
        "description": "Restricted access laboratory area.",
        "risk_level":"critical",
        "notes": "Only authorized personnel allowed. Any intrusion should be treated as critical.",
    },
    "Library": {
        "description": "study area with high occupancy.",
        "risk_level":"medium",
        "notes": "Overcrowding can occur during exam periods.",
    },
    "Cafeteria": {
        "description": "highly crowded area during lunch hours.",
        "risk_level":"medium",
        "notes": "Monitor for overcrowding during peak hours.",
    },
}

# agent tools

TOOLS = [
    {
        "name": "get_recent_incidents",
        "description": (
            "Get recent incidents in a zone."
            "Use this to correlate the current incident with nearby recent incidents."
        ),
        "input_schema": {
            "type": "object",
            "properties":{
                "zone":{
                    "type": "string",
                    "description": "Zone name , e.g. Gate_3",
                },
                "minutes": {
                    "type": "integer",
                    "description": "Maximum number of incidents to return",
                    "default":10,
                },
                "exclude_incident_id": {
                    "type": "string",
                    "description": "Exclude current incident id from results",
                },
            },
            "required":["zone"],
        },
    },
    {
        "name": "get_object_track_history",
        "description": (
            "Get recent incident involving the same tracked object ID. "
            "Useful for unattended baggage or intrusion events."
        ),
        "input_schema":{
            "type":"object",
            "properties":{
                "tracked_object_id": {
                    "type":"integer",
                    "description": "Tracked object ID from perception module",
                },
                "limit":{
                    "type": "integer",
                    "description":"Maximum number of events to return",
                    "default":20,
                },
            },
            "required":["tracked_object_id"],
        },
    },
    {
        "name": "get_zone_context",
        "description": (
            "Get static zone context, latest occupancy, and recent incidents for a zone"
        ),
        "input_schema: {"
        "type": "object",
        "properties": {
            "zone":{
                "type": "string",
                "description": "Zone name, e.g Gate_3",
            },

        },
        "required":["zone"],
    },
]


