# ai-generated: 100% - generated with ChatGPT from the course API.md and REQUIREMENTS.md
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone, time
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt


# ---------------------------------------------------------------------------
# Configuration / Lab 1 decisions
# ---------------------------------------------------------------------------

C1 = "wallclock"
C2 = "immutable"
C3 = "vip"

WARSAW = ZoneInfo("Europe/Warsaw")

DATABASE_PATH = os.getenv("SVCDESK_DB", "/data/svcdesk.db")


# ---------------------------------------------------------------------------
# FastAPI
# ---------------------------------------------------------------------------

app = FastAPI(title="svcdesk")


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()

    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.get("loc", []) if part != "body")
        message = first.get("msg", "invalid request")

        if location:
            message = f"{location}: {message}"
    else:
        message = "invalid request"

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation",
                "message": message,
            }
        },
    )


# ---------------------------------------------------------------------------
# Test clock
# ---------------------------------------------------------------------------

def parse_rfc3339(value: str) -> datetime:
    try:
        normalized = value

        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"

        parsed = datetime.fromisoformat(normalized)

        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("timezone offset required")

        return parsed.astimezone(timezone.utc)

    except (ValueError, TypeError):
        raise ApiError(
            400,
            "invalid_clock",
            "X-Test-Clock must be a valid RFC 3339 timestamp with timezone offset",
        )


@app.middleware("http")
async def test_clock_middleware(request: Request, call_next):
    enabled = os.getenv("SVCDESK_TEST_CLOCK", "").lower() in {"1", "true"}

    if enabled:
        header = request.headers.get("X-Test-Clock")

        if header is not None:
            try:
                request.state.now = parse_rfc3339(header)
            except ApiError as exc:
                return JSONResponse(
                    status_code=exc.status_code,
                    content={
                        "error": {
                            "code": exc.code,
                            "message": exc.message,
                        }
                    },
                )
        else:
            request.state.now = datetime.now(timezone.utc)
    else:
        request.state.now = datetime.now(timezone.utc)

    return await call_next(request)


def request_now(request: Request) -> datetime:
    return request.state.now


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class ReporterCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = Field(min_length=1, max_length=100)
    email: str | None = None
    vip: StrictBool = False


class TicketCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)
    reporter: ReporterCreate

    impact: StrictInt = Field(ge=1, le=3)
    urgency: StrictInt = Field(ge=1, le=3)

    related_to: str | None = None


# ---------------------------------------------------------------------------
# SQLite persistence
# ---------------------------------------------------------------------------

def init_database() -> None:
    path = Path(DATABASE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            )
            """
        )
        connection.commit()


@app.on_event("startup")
def startup_event():
    init_database()


def save_ticket(ticket: dict[str, Any]) -> None:
    payload = json.dumps(ticket)

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT INTO tickets (id, payload)
            VALUES (?, ?)
            ON CONFLICT(id)
            DO UPDATE SET payload = excluded.payload
            """,
            (ticket["id"], payload),
        )
        connection.commit()


def load_ticket(ticket_id: str) -> dict[str, Any]:
    with sqlite3.connect(DATABASE_PATH) as connection:
        row = connection.execute(
            "SELECT payload FROM tickets WHERE id = ?",
            (ticket_id,),
        ).fetchone()

    if row is None:
        raise ApiError(
            404,
            "not_found",
            f"ticket {ticket_id} was not found",
        )

    return json.loads(row[0])


def load_all_tickets() -> list[dict[str, Any]]:
    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = connection.execute(
            "SELECT payload FROM tickets"
        ).fetchall()

    return [json.loads(row[0]) for row in rows]


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def to_utc_z(value: datetime) -> str:
    utc_value = value.astimezone(timezone.utc)

    return utc_value.strftime("%Y-%m-%dT%H:%M:%SZ")


def from_timestamp(value: str | None) -> datetime | None:
    if value is None:
        return None

    normalized = value

    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    return datetime.fromisoformat(normalized).astimezone(timezone.utc)


# ---------------------------------------------------------------------------
# Priority
# ---------------------------------------------------------------------------

PRIORITY_MATRIX = {
    (1, 1): "P1",
    (1, 2): "P2",
    (1, 3): "P3",
    (2, 1): "P2",
    (2, 2): "P3",
    (2, 3): "P4",
    (3, 1): "P3",
    (3, 2): "P4",
    (3, 3): "P4",
}


def calculate_priority(
    impact: int,
    urgency: int,
    vip: bool,
) -> str:
    priority = PRIORITY_MATRIX[(impact, urgency)]

    if C3 == "vip" and vip and priority in {"P3", "P4"}:
        priority = "P2"

    return priority


# ---------------------------------------------------------------------------
# SLA
# ---------------------------------------------------------------------------

ACK_TARGETS = {
    "P1": timedelta(minutes=15),
    "P2": timedelta(hours=1),
    "P3": timedelta(hours=4),
    "P4": timedelta(hours=8),
}

RESOLVE_TARGETS = {
    "P1": timedelta(hours=4),
    "P2": timedelta(hours=8),
    "P3": timedelta(hours=24),
    "P4": timedelta(hours=72),
}


def uses_business_clock(priority: str) -> bool:
    if priority == "P1":
        return C1 == "business"

    return True


def is_business_time(value: datetime) -> bool:
    local = value.astimezone(WARSAW)

    if local.weekday() >= 5:
        return False

    current_time = local.time().replace(tzinfo=None)

    return time(8, 0) <= current_time < time(16, 0)


def next_business_opening(value: datetime) -> datetime:
    local = value.astimezone(WARSAW)

    while True:
        if local.weekday() >= 5:
            next_day = local.date() + timedelta(days=1)
            local = datetime.combine(
                next_day,
                time(8, 0),
                tzinfo=WARSAW,
            )
            continue

        current_time = local.time().replace(tzinfo=None)

        if current_time < time(8, 0):
            return datetime.combine(
                local.date(),
                time(8, 0),
                tzinfo=WARSAW,
            )

        if current_time >= time(16, 0):
            next_day = local.date() + timedelta(days=1)
            local = datetime.combine(
                next_day,
                time(8, 0),
                tzinfo=WARSAW,
            )
            continue

        return local


def add_business_time(
    created_at: datetime,
    target: timedelta,
) -> datetime:
    cursor = next_business_opening(created_at)

    remaining = target.total_seconds()

    while remaining > 0:
        local_cursor = cursor.astimezone(WARSAW)

        closing = datetime.combine(
            local_cursor.date(),
            time(16, 0),
            tzinfo=WARSAW,
        )

        available = (closing - local_cursor).total_seconds()

        if remaining <= available:
            result = local_cursor + timedelta(seconds=remaining)
            return result.astimezone(timezone.utc)

        remaining -= available

        next_day = local_cursor.date() + timedelta(days=1)

        cursor = datetime.combine(
            next_day,
            time(8, 0),
            tzinfo=WARSAW,
        )

        cursor = next_business_opening(cursor)

    return cursor.astimezone(timezone.utc)


def calculate_due(
    created_at: datetime,
    target: timedelta,
    business_clock: bool,
) -> datetime:
    if business_clock:
        return add_business_time(created_at, target)

    return created_at + target


def create_sla(
    priority: str,
    created_at: datetime,
) -> dict[str, str]:
    business_clock = uses_business_clock(priority)

    ack_due = calculate_due(
        created_at,
        ACK_TARGETS[priority],
        business_clock,
    )

    resolve_due = calculate_due(
        created_at,
        RESOLVE_TARGETS[priority],
        business_clock,
    )

    return {
        "ack_due_at": to_utc_z(ack_due),
        "resolve_due_at": to_utc_z(resolve_due),
    }


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "svcdesk",
    }


# ---------------------------------------------------------------------------
# Create ticket
# ---------------------------------------------------------------------------

@app.post("/tickets", status_code=201)
def create_ticket(
    body: TicketCreate,
    request: Request,
):
    now = request_now(request)

    priority = calculate_priority(
        body.impact,
        body.urgency,
        body.reporter.vip,
    )

    ticket_id = str(uuid.uuid4())

    ticket = {
        "id": ticket_id,
        "title": body.title,
        "description": body.description,
        "reporter": {
            "name": body.reporter.name,
            "email": body.reporter.email,
            "vip": body.reporter.vip,
        },
        "impact": body.impact,
        "urgency": body.urgency,
        "priority": priority,
        "state": "new",
        "created_at": to_utc_z(now),
        "acknowledged_at": None,
        "resolved_at": None,
        "closed_at": None,
        "related_to": body.related_to,
        "sla": create_sla(priority, now),
    }

    save_ticket(ticket)

    return ticket


# ---------------------------------------------------------------------------
# Read tickets
# ---------------------------------------------------------------------------

@app.get("/tickets")
def list_tickets(
    state: str | None = None,
    priority: str | None = None,
):
    tickets = load_all_tickets()

    if state is not None:
        tickets = [
            ticket
            for ticket in tickets
            if ticket["state"] == state
        ]

    if priority is not None:
        tickets = [
            ticket
            for ticket in tickets
            if ticket["priority"] == priority
        ]

    return tickets


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    return load_ticket(ticket_id)


# ---------------------------------------------------------------------------
# Ticket transitions
# ---------------------------------------------------------------------------

@app.post("/tickets/{ticket_id}/ack")
def acknowledge_ticket(
    ticket_id: str,
    request: Request,
):
    ticket = load_ticket(ticket_id)

    if ticket["state"] != "new":
        raise ApiError(
            409,
            "invalid_transition",
            "only a new ticket can be acknowledged",
        )

    ticket["state"] = "acknowledged"
    ticket["acknowledged_at"] = to_utc_z(request_now(request))

    save_ticket(ticket)

    return ticket


@app.post("/tickets/{ticket_id}/start")
def start_ticket(
    ticket_id: str,
    request: Request,
):
    ticket = load_ticket(ticket_id)

    if ticket["state"] != "acknowledged":
        raise ApiError(
            409,
            "invalid_transition",
            "only an acknowledged ticket can be started",
        )

    ticket["state"] = "in_progress"

    save_ticket(ticket)

    return ticket


@app.post("/tickets/{ticket_id}/resolve")
def resolve_ticket(
    ticket_id: str,
    request: Request,
):
    ticket = load_ticket(ticket_id)

    if ticket["state"] != "in_progress":
        raise ApiError(
            409,
            "invalid_transition",
            "only an in-progress ticket can be resolved",
        )

    ticket["state"] = "resolved"
    ticket["resolved_at"] = to_utc_z(request_now(request))

    save_ticket(ticket)

    return ticket


@app.post("/tickets/{ticket_id}/close")
def close_ticket(
    ticket_id: str,
    request: Request,
):
    ticket = load_ticket(ticket_id)

    if ticket["state"] != "resolved":
        raise ApiError(
            409,
            "invalid_transition",
            "only a resolved ticket can be closed",
        )

    ticket["state"] = "closed"
    ticket["closed_at"] = to_utc_z(request_now(request))

    save_ticket(ticket)

    return ticket


@app.post("/tickets/{ticket_id}/reopen")
def reopen_ticket(
    ticket_id: str,
    request: Request,
):
    ticket = load_ticket(ticket_id)

    now = request_now(request)

    if ticket["state"] == "resolved":
        event_time = from_timestamp(ticket["resolved_at"])

        if event_time is None:
            raise ApiError(
                409,
                "invalid_transition",
                "ticket has no resolution timestamp",
            )

        if now > event_time + timedelta(days=7):
            raise ApiError(
                409,
                "reopen_window_expired",
                "the seven-day reopen window has expired",
            )

    elif ticket["state"] == "closed":
        if C2 == "immutable":
            raise ApiError(
                409,
                "ticket_closed",
                "closed tickets are immutable",
            )

        event_time = from_timestamp(ticket["closed_at"])

        if event_time is None:
            raise ApiError(
                409,
                "invalid_transition",
                "ticket has no closure timestamp",
            )

        if now > event_time + timedelta(days=7):
            raise ApiError(
                409,
                "reopen_window_expired",
                "the seven-day reopen window has expired",
            )

    else:
        raise ApiError(
            409,
            "invalid_transition",
            "only resolved tickets can be reopened",
        )

    ticket["state"] = "in_progress"
    ticket["resolved_at"] = None
    ticket["closed_at"] = None

    save_ticket(ticket)

    return ticket


# ---------------------------------------------------------------------------
# SLA status
# ---------------------------------------------------------------------------

@app.get("/tickets/{ticket_id}/sla")
def get_ticket_sla(
    ticket_id: str,
    request: Request,
):
    ticket = load_ticket(ticket_id)

    now = request_now(request)

    ack_due = from_timestamp(ticket["sla"]["ack_due_at"])
    resolve_due = from_timestamp(ticket["sla"]["resolve_due_at"])

    acknowledged_at = from_timestamp(ticket["acknowledged_at"])
    resolved_at = from_timestamp(ticket["resolved_at"])

    if acknowledged_at is None:
        ack_breached = now > ack_due
    else:
        ack_breached = acknowledged_at > ack_due

    if resolved_at is None:
        resolve_breached = now > resolve_due
    else:
        resolve_breached = resolved_at > resolve_due

    business_clock = uses_business_clock(ticket["priority"])

    paused = (
        ticket["state"] not in {"resolved", "closed"}
        and business_clock
        and not is_business_time(now)
    )

    return {
        "priority": ticket["priority"],
        "ack_due_at": ticket["sla"]["ack_due_at"],
        "resolve_due_at": ticket["sla"]["resolve_due_at"],
        "ack_breached": ack_breached,
        "resolve_breached": resolve_breached,
        "paused": paused,
    }