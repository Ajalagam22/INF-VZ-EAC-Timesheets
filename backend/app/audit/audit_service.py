from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.activity_record import AuditEvent


class AuditService:
    def record_event(
        self,
        db: Session,
        *,
        run_id: str,
        event_type: str,
        payload: Dict[str, Any],
        record_uid: Optional[str] = None
    ) -> AuditEvent:
        event = AuditEvent(
            run_id=run_id,
            record_uid=record_uid,
            event_type=event_type,
            payload_json=payload
        )
        db.add(event)
        return event

    def timeline(self, db: Session, record_uid: str) -> List[Dict[str, Any]]:
        rows = (
            db.query(AuditEvent)
            .filter(AuditEvent.record_uid == record_uid)
            .order_by(AuditEvent.created_at.asc())
            .all()
        )
        return [
            {
                "id": row.id,
                "run_id": row.run_id,
                "record_uid": row.record_uid,
                "event_type": row.event_type,
                "payload": row.payload_json,
                "created_at": row.created_at.isoformat() if row.created_at else None
            }
            for row in rows
        ]
