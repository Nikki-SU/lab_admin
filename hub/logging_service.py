from sqlalchemy.orm import Session
from datetime import datetime
from .models import Log, LogAction
from .utils import generate_uuid, format_log_timestamp


def log_action(
    db: Session,
    operator: str,
    location: str,
    action: LogAction,
    detail: str,
    timestamp: datetime = None
):
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    log_entry = Log(
        id=generate_uuid(),
        timestamp=timestamp,
        operator=operator,
        location=location,
        action=action,
        detail=detail
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry
