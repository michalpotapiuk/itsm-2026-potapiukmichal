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

# ---------------------------------------------------------------------------
# Lab 2 - DORA metrics
# ---------------------------------------------------------------------------

from decimal import Decimal, ROUND_HALF_UP


def round_half_up(value: float) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def round_six(value: float) -> float:
    return float(
        Decimal(str(value)).quantize(
            Decimal("0.000001"),
            rounding=ROUND_HALF_UP,
        )
    )


def median(values: list[float]) -> int | None:
    if not values:
        return None

    ordered = sorted(values)
    count = len(ordered)
    middle = count // 2

    if count % 2 == 1:
        return round_half_up(ordered[middle])

    return round_half_up(
        (ordered[middle - 1] + ordered[middle]) / 2
    )


def parse_metric_timestamp(value: str) -> datetime:
    try:
        normalized = value

        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"

        parsed = datetime.fromisoformat(normalized)

        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError()

        return parsed.astimezone(timezone.utc)

    except Exception:
        raise ApiError(
            422,
            "validation",
            "invalid RFC3339 timestamp",
        )


def validate_and_deduplicate_events(
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    unique_events: list[dict[str, Any]] = []
    seen_event_ids: set[str] = set()

    for event in events:
        if not isinstance(event, dict):
            raise ApiError(422, "validation", "event must be an object")

        event_id = event.get("event_id")
        event_type = event.get("type")
        at = event.get("at")

        if (
            not isinstance(event_id, str)
            or not (1 <= len(event_id) <= 64)
            or event_type not in {"commit", "deployment", "incident"}
            or not isinstance(at, str)
        ):
            raise ApiError(422, "validation", "malformed event")

        # R-05: first event_id wins
        if event_id in seen_event_ids:
            continue

        seen_event_ids.add(event_id)

        event = dict(event)
        event["_at"] = parse_metric_timestamp(at)

        unique_events.append(event)

    commits_by_sha: dict[str, dict[str, Any]] = {}
    deployments_by_id: dict[str, dict[str, Any]] = {}
    incidents_by_id: dict[str, dict[str, dict[str, Any]]] = {}

    # first validation pass
    for event in unique_events:
        if event["type"] == "commit":
            sha = event.get("sha")
            branch = event.get("branch")
            change_id = event.get("change_id")
            reverts = event.get("reverts")

            if not isinstance(sha, str) or not isinstance(branch, str):
                raise ApiError(422, "validation", "malformed commit")

            if sha in commits_by_sha:
                raise ApiError(422, "validation", "duplicate commit sha")

            if reverts is None:
                if not isinstance(change_id, str):
                    raise ApiError(
                        422,
                        "validation",
                        "non-revert commit requires change_id",
                    )
            else:
                if not isinstance(reverts, str) or change_id is not None:
                    raise ApiError(
                        422,
                        "validation",
                        "revert commit must have null change_id",
                    )

            commits_by_sha[sha] = event

        elif event["type"] == "deployment":
            deployment_id = event.get("deployment_id")
            environment = event.get("environment")
            outcome = event.get("outcome")
            commits = event.get("commits")
            unplanned = event.get("unplanned")
            caused_by = event.get("caused_by")

            if (
                not isinstance(deployment_id, str)
                or not isinstance(environment, str)
                or outcome not in {"success", "failure"}
                or not isinstance(commits, list)
                or not isinstance(unplanned, bool)
                or (
                    caused_by is not None
                    and not isinstance(caused_by, str)
                )
            ):
                raise ApiError(422, "validation", "malformed deployment")

            deployments_by_id[deployment_id] = event

        elif event["type"] == "incident":
            incident_id = event.get("incident_id")
            phase = event.get("phase")
            deployments = event.get("deployments")

            if (
                not isinstance(incident_id, str)
                or phase not in {"opened", "resolved"}
                or not isinstance(deployments, list)
            ):
                raise ApiError(422, "validation", "malformed incident")

            incidents_by_id.setdefault(incident_id, {})

            if phase in incidents_by_id[incident_id]:
                raise ApiError(
                    422,
                    "validation",
                    "duplicate incident phase",
                )

            incidents_by_id[incident_id][phase] = event

    # cross-reference validation
    for event in unique_events:
        if event["type"] == "commit":
            reverts = event.get("reverts")

            if reverts is not None and reverts not in commits_by_sha:
                raise ApiError(
                    422,
                    "validation",
                    "reverts references unknown commit",
                )

        elif event["type"] == "deployment":
            for sha in event["commits"]:
                if sha not in commits_by_sha:
                    raise ApiError(
                        422,
                        "validation",
                        "deployment references unknown commit",
                    )

            caused_by = event.get("caused_by")
            if caused_by is not None and caused_by not in incidents_by_id:
                raise ApiError(
                    422,
                    "validation",
                    "caused_by references unknown incident",
                )

        elif event["type"] == "incident":
            for deployment_id in event["deployments"]:
                if deployment_id not in deployments_by_id:
                    raise ApiError(
                        422,
                        "validation",
                        "incident references unknown deployment",
                    )

    for incident_id, phases in incidents_by_id.items():
        if "resolved" in phases and "opened" not in phases:
            raise ApiError(
                422,
                "validation",
                "resolved incident has no opened event",
            )

    return unique_events


def resolve_change_id(
    sha: str,
    commits_by_sha: dict[str, dict[str, Any]],
    cache: dict[str, str],
) -> str:
    if sha in cache:
        return cache[sha]

    current = commits_by_sha[sha]
    seen: set[str] = set()

    while current.get("reverts") is not None:
        current_sha = current["sha"]

        if current_sha in seen:
            raise ApiError(
                422,
                "validation",
                "revert cycle detected",
            )

        seen.add(current_sha)

        target_sha = current["reverts"]

        if target_sha not in commits_by_sha:
            raise ApiError(
                422,
                "validation",
                "revert references unknown commit",
            )

        current = commits_by_sha[target_sha]

    change_id = current.get("change_id")

    if not isinstance(change_id, str):
        raise ApiError(
            422,
            "validation",
            "could not resolve change id",
        )

    cache[sha] = change_id
    return change_id


def compute_dora_metrics(
    window_from: datetime,
    window_to: datetime,
    events: list[dict[str, Any]],
    original_window_from: str,
    original_window_to: str,
) -> dict[str, Any]:
    commits = [e for e in events if e["type"] == "commit"]
    deployments = [e for e in events if e["type"] == "deployment"]
    incidents = [e for e in events if e["type"] == "incident"]

    commits_by_sha = {
        e["sha"]: e
        for e in commits
    }

    # R-01 + R-02
    production_deployments = [
        e
        for e in deployments
        if e["environment"] == "production"
        and window_from <= e["_at"] < window_to
    ]

    successful_deployments = [
        e
        for e in production_deployments
        if e["outcome"] == "success"
    ]

    failed_deployments = [
        e
        for e in production_deployments
        if e["outcome"] == "failure"
    ]

    # R-06 change identity
    change_cache: dict[str, str] = {}

    for sha in commits_by_sha:
        resolve_change_id(
            sha,
            commits_by_sha,
            change_cache,
        )

    all_change_ids = set(change_cache.values())

    # first commit instant per change - R-07
    change_first_commit_at: dict[str, datetime] = {}

    for sha, commit in commits_by_sha.items():
        change_id = change_cache[sha]
        commit_at = commit["_at"]

        previous = change_first_commit_at.get(change_id)

        if previous is None or commit_at < previous:
            change_first_commit_at[change_id] = commit_at

    # R-08 lead-time pairs
    first_success_deployment_for_sha: dict[str, dict[str, Any]] = {}

    for deployment in sorted(
        successful_deployments,
        key=lambda x: x["_at"],
    ):
        for sha in deployment["commits"]:
            if sha not in first_success_deployment_for_sha:
                first_success_deployment_for_sha[sha] = deployment

    lead_times: list[float] = []
    negative_lead_time_pairs = 0

    for sha, deployment in first_success_deployment_for_sha.items():
        commit = commits_by_sha[sha]

        duration = (
            deployment["_at"] - commit["_at"]
        ).total_seconds()

        if duration < 0:
            duration = 0
            negative_lead_time_pairs += 1

        lead_times.append(duration)

    # R-09
    carried_shas = {
        sha
        for deployment in production_deployments
        for sha in deployment["commits"]
    }

    commits_never_on_main = sum(
        1
        for sha in carried_shas
        if commits_by_sha[sha]["branch"] != "main"
    )

    # R-10
    deployments_without_commits = sum(
        1
        for deployment in production_deployments
        if len(deployment["commits"]) == 0
    )

    # R-11
    window_days = (
        window_to - window_from
    ).total_seconds() / 86400

    deployment_frequency_per_day = round_six(
        len(production_deployments) / window_days
    )

    # incident phase structure
    incident_phases: dict[str, dict[str, dict[str, Any]]] = {}

    for incident in incidents:
        incident_phases.setdefault(
            incident["incident_id"],
            {},
        )[incident["phase"]] = incident

    # R-12 failure recovery
    recovery_times: list[float] = []
    recovered_failures = 0
    open_failures = 0

    for deployment in failed_deployments:
        covering_candidates = []

        for incident_id, phases in incident_phases.items():
            opened = phases.get("opened")

            if (
                opened is not None
                and deployment["deployment_id"]
                in opened["deployments"]
            ):
                covering_candidates.append(
                    (
                        opened["_at"],
                        incident_id,
                        phases,
                    )
                )

        if not covering_candidates:
            open_failures += 1
            continue

        covering_candidates.sort(
            key=lambda item: (
                item[0],
                item[1],
            )
        )

        phases = covering_candidates[0][2]
        resolved = phases.get("resolved")

        if resolved is None:
            open_failures += 1
            continue

        duration = (
            resolved["_at"] - deployment["_at"]
        ).total_seconds()

        if duration < 0:
            duration = 0

        recovery_times.append(duration)
        recovered_failures += 1

    # R-13 overlapping incidents
    incident_intervals: list[tuple[datetime, datetime]] = []

    for phases in incident_phases.values():
        opened = phases.get("opened")

        if opened is None:
            continue

        resolved = phases.get("resolved")

        end = (
            resolved["_at"]
            if resolved is not None
            else window_to
        )

        incident_intervals.append(
            (
                opened["_at"],
                end,
            )
        )

    overlapping_incident_pairs = 0

    for i in range(len(incident_intervals)):
        for j in range(i + 1, len(incident_intervals)):
            a_start, a_end = incident_intervals[i]
            b_start, b_end = incident_intervals[j]

            if a_start < b_end and b_start < a_end:
                overlapping_incident_pairs += 1

    # R-14
    if production_deployments:
        change_fail_rate = round_six(
            len(failed_deployments)
            / len(production_deployments)
        )
    else:
        change_fail_rate = None

    # R-15
    rework_deployments = sum(
        1
        for deployment in production_deployments
        if deployment["unplanned"] is True
        and deployment["caused_by"] is not None
    )

    if production_deployments:
        deployment_rework_rate = round_six(
            rework_deployments
            / len(production_deployments)
        )
    else:
        deployment_rework_rate = None

    # R-16/R-17 ground truth
    first_success_deployment_for_change: dict[
        str,
        datetime,
    ] = {}

    for deployment in sorted(
        successful_deployments,
        key=lambda x: x["_at"],
    ):
        deployment_changes = {
            change_cache[sha]
            for sha in deployment["commits"]
        }

        for change_id in deployment_changes:
            if change_id not in first_success_deployment_for_change:
                first_success_deployment_for_change[
                    change_id
                ] = deployment["_at"]

    true_change_lead_times: list[float] = []

    for (
        change_id,
        deployment_at,
    ) in first_success_deployment_for_change.items():
        first_commit_at = change_first_commit_at[change_id]

        duration = (
            deployment_at - first_commit_at
        ).total_seconds()

        if duration < 0:
            duration = 0

        true_change_lead_times.append(duration)

    revert_chains_collapsed = sum(
        1
        for commit in commits
        if commit.get("reverts") is not None
    )

    return {
        "spec_version": "1.0.0",
        "window": {
            "from": original_window_from,
            "to": original_window_to,
        },
        "deployment_frequency_per_day":
            deployment_frequency_per_day,
        "change_lead_time_seconds_p50":
            median(lead_times),
        "failed_deployment_recovery_time_seconds_p50":
            median(recovery_times),
        "change_fail_rate":
            change_fail_rate,
        "deployment_rework_rate":
            deployment_rework_rate,
        "counts": {
            "deployments":
                len(production_deployments),
            "successful_deployments":
                len(successful_deployments),
            "failed_deployments":
                len(failed_deployments),
            "recovered_failures":
                recovered_failures,
            "open_failures":
                open_failures,
            "rework_deployments":
                rework_deployments,
            "lead_time_pairs":
                len(lead_times),
            "changes":
                len(all_change_ids),
        },
        "anomalies": {
            "negative_lead_time_pairs":
                negative_lead_time_pairs,
            "deployments_without_commits":
                deployments_without_commits,
            "commits_never_on_main":
                commits_never_on_main,
            "revert_chains_collapsed":
                revert_chains_collapsed,
            "overlapping_incident_pairs":
                overlapping_incident_pairs,
        },
        "ground_truth": {
            "changes_delivered":
                len(first_success_deployment_for_change),
            "true_change_lead_time_seconds_p50":
                median(true_change_lead_times),
        },
    }


@app.post("/dora/metrics")
async def dora_metrics(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise ApiError(
            422,
            "validation",
            "request body must be valid JSON",
        )

    if not isinstance(body, dict):
        raise ApiError(
            422,
            "validation",
            "request body must be an object",
        )

    window = body.get("window")
    events = body.get("events")

    if not isinstance(window, dict):
        raise ApiError(
            422,
            "validation",
            "window is required",
        )

    if not isinstance(events, list):
        raise ApiError(
            422,
            "validation",
            "events must be an array",
        )

    from_value = window.get("from")
    to_value = window.get("to")

    if (
        not isinstance(from_value, str)
        or not isinstance(to_value, str)
    ):
        raise ApiError(
            422,
            "validation",
            "window requires from and to",
        )

    window_from = parse_metric_timestamp(from_value)
    window_to = parse_metric_timestamp(to_value)

    if window_to <= window_from:
        raise ApiError(
            422,
            "validation",
            "window.to must be after window.from",
        )

    parsed_events = validate_and_deduplicate_events(events)

    return compute_dora_metrics(
        window_from,
        window_to,
        parsed_events,
        from_value,
        to_value,
    )


# ---------------------------------------------------------------------------
# Lab 2 - ticket event stream
# ---------------------------------------------------------------------------

@app.get("/dora/ticket-events")
def dora_ticket_events():
    tickets = load_all_tickets()
    events: list[dict[str, Any]] = []

    for ticket in tickets:
        phases = [
            (
                ticket.get("created_at"),
                "created",
                "new",
            ),
            (
                ticket.get("acknowledged_at"),
                "acknowledged",
                "acknowledged",
            ),
            (
                ticket.get("resolved_at"),
                "resolved",
                "resolved",
            ),
            (
                ticket.get("closed_at"),
                "closed",
                "closed",
            ),
        ]

        for at, phase, state in phases:
            if at is None:
                continue

            events.append(
                {
                    "ticket_id": ticket["id"],
                    "at": at,
                    "phase": phase,
                    "priority": ticket["priority"],
                    "state": state,
                }
            )

    events.sort(
        key=lambda item: (
            from_timestamp(item["at"]),
            item["ticket_id"],
        )
    )

    return events