"""
Celery Worker — XChange Platform
=================================
Background task queue broker via Redis.

Planned tasks (to be implemented per sprint):
  - send_email_notification     : Send email on order fill, margin call, etc.
  - reconcile_portfolio         : Nightly P&L snapshot for all users
  - generate_statement          : Monthly account statement PDF
  - purge_expired_sessions      : Remove expired JWT refresh tokens
  - update_funding_rates        : Sync Futures funding rates from Binance
"""

import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = Celery(
    "xchange_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)


# ---------------------------------------------------------------------------
# Placeholder tasks — to be fully implemented in subsequent sprints
# ---------------------------------------------------------------------------

@app.task(name="tasks.send_email_notification")
def send_email_notification(user_id: str, subject: str, body: str) -> dict:
    """Placeholder: send email via notification-service (Sprint 3)."""
    return {"queued": True, "user_id": user_id}


@app.task(name="tasks.reconcile_portfolio")
def reconcile_portfolio(user_id: str) -> dict:
    """Placeholder: recalculate P&L snapshot (Sprint 5)."""
    return {"queued": True, "user_id": user_id}


@app.task(name="tasks.generate_statement")
def generate_statement(user_id: str, period: str) -> dict:
    """Placeholder: generate monthly statement PDF (Sprint 8)."""
    return {"queued": True, "user_id": user_id, "period": period}
