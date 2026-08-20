#Reads video → detects → tracks → runs rules → sends incidents

import cv2
import numpy as np
from datetime import datetime

from detector import Detector
from tracker import CentroidTracker
from rules import check_crowd, check_baggage, check_intrusion, check_fire
from incident_sender import build_incident, send_incident
from occupancy import OccupancyTracker, send_occupancy_update

from config import (
    CROWD_THRESHOLD, BAGGAGE_DWELL_SECONDS, DETECTION_CONFIDENCE,
    FRAME_SKIP, OCCUPANCY_SEND_INTERVAL, ZONE_CAPACITIES
)
from zones import ZONES


def run(video_path=0): #change path for video
    # Run on webcam: run(0)
    # Run on video file: run("path/to/video.mp4")

    detector = Detector(confidence=DETECTION_CONFIDENCE)
    tracker = CentroidTracker()
    occupancy_tracker = OccupancyTracker(zone_capacities=ZONE_CAPACITIES)
    
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    occupancy_send_counter = 0
    
    print("=" * 60)
    print("PERCEPTION MODULE STARTED")
    print("=" * 60)
    print(f"Video source: {video_path}")
    print(f"Crowd threshold: {CROWD_THRESHOLD} people")
    print(f"Baggage dwell time: {BAGGAGE_DWELL_SECONDS}s")
    print(f"Occupancy send interval: every {OCCUPANCY_SEND_INTERVAL} frames")
    print(f"Zone capacities: {ZONE_CAPACITIES}")
    print("=" * 60)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("\n[!] End of video or error reading frame")
            break
        
        frame_count += 1
        occupancy_send_counter += 1
        
        # Frame skipping for speed
        if frame_count % FRAME_SKIP != 0:
            continue

        frame = cv2.resize(frame, (640, 480))
        raw_detections = detector.detect(frame) #detect
        tracked_objects = tracker.update(raw_detections) #track
        occupancies = occupancy_tracker.update(tracked_objects)
        
        # Send occupancy updates at regular intervals (not every frame)
        if occupancy_send_counter >= OCCUPANCY_SEND_INTERVAL:
            for zone_name, occupancy_data in occupancies.items():
                send_occupancy_update(occupancy_data)
            occupancy_send_counter = 0
        
        # ========== INCIDENT RULES STEP ==========
        incident = None
        
        # Try crowd check first
        crowd_incident = check_crowd(tracked_objects, ZONES, CROWD_THRESHOLD)
        if crowd_incident:
            incident = build_incident(**crowd_incident)
        
        # Try baggage check
        if not incident:
            baggage_incident = check_baggage(tracked_objects, BAGGAGE_DWELL_SECONDS)
            if baggage_incident:
                incident = build_incident(**baggage_incident)
        
        # Try intrusion check
        if not incident:
            intrusion_incident = check_intrusion(tracked_objects, ZONES)
            if intrusion_incident:
                incident = build_incident(**intrusion_incident)
        
        # Try fire check
        if not incident:
            fire_incident = check_fire(0.0)  # placeholder, no actual fire model yet
            if fire_incident:
                incident = build_incident(**fire_incident)
        
        # ========== SEND INCIDENT (if any) ==========
        if incident:
            send_incident(incident)
        
        # ========== PERIODIC LOGGING ==========
        if frame_count % (FRAME_SKIP * 30) == 0:
            print(f"[Frame {frame_count:5d}] Tracked: {len(tracked_objects)} objects | " +
                  f"Occupancy: {dict(occupancy_tracker.current_counts)}")
    
    cap.release()
    print("\n[!] Perception loop stopped")


if __name__ == "__main__":
    run(0)
