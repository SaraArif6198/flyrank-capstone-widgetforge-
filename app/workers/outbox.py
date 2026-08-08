from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import OutboxEvent, Submission
from app.integrations.notifier import ConsoleNotifier, Notifier

MAX_ATTEMPTS = 3


def process_pending_events(db: Session, notifier: Notifier | None = None) -> int:
    notifier = notifier or ConsoleNotifier()
    now = datetime.now(timezone.utc)
    events = list(db.scalars(select(OutboxEvent).where(OutboxEvent.status == "pending", OutboxEvent.available_at <= now)))
    processed = 0
    for event in events:
        submission = db.get(Submission, event.submission_id)
        try:
            if submission is None:
                raise RuntimeError("Submission no longer exists")
            notifier.send_submission_accepted(submission, event.id)
            event.status = "sent"
            event.attempt_count += 1
            event.last_error = None
        except Exception:
            event.attempt_count += 1
            event.last_error = "Notification delivery failed"
            if event.attempt_count >= MAX_ATTEMPTS:
                event.status = "failed"
            else:
                event.available_at = now + timedelta(seconds=2 ** event.attempt_count)
        processed += 1
    db.commit()
    return processed
