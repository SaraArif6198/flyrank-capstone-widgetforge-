from app.db.models import Submission


class Notifier:
    def send_submission_accepted(self, submission: Submission, event_id: str) -> None:
        raise NotImplementedError


class ConsoleNotifier(Notifier):
    def send_submission_accepted(self, submission: Submission, event_id: str) -> None:
        # No PII is logged; an event ID lets any future receiver deduplicate.
        print(f"notification event={event_id} submission={submission.id}")
