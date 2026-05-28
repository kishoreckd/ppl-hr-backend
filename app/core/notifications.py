from sqlalchemy.orm import Session

from app.models.hr import NotificationEvent, NotificationStatusEnum


def queue_notification(
    db: Session,
    event_key: str,
    module: str,
    actor_id: int | None = None,
    recipient_id: int | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    payload: dict | None = None,
) -> NotificationEvent:
    event = NotificationEvent(
        event_key=event_key,
        module=module,
        actor_id=actor_id,
        recipient_id=recipient_id,
        entity_type=entity_type,
        entity_id=entity_id,
        payload=payload or {},
        status=NotificationStatusEnum.QUEUED,
    )
    db.add(event)
    db.flush()
    return event
