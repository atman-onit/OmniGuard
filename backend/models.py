from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Integer, Float, DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Incident(Base):
    __tablename__ = "incidents"

    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    type: Mapped[str] = mapped_column(String)  
    zone: Mapped[str] = mapped_column(String, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    tracked_object_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    dwell_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    person_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    detection_confidence: Mapped[float] = mapped_column(Float)

    
    severity: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    reasoning_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    correlated_incident_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    notification_draft: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    
    status: Mapped[str] = mapped_column(String, default="new")  
    snapshot_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
