# svcdesk - Service Desk API Specification

## Purpose

The svcdesk service provides a REST API for managing service desk tickets.
The service must provide predictable ticket creation, priority calculation,
status transitions and SLA handling.

## Health

The service shall expose a health endpoint.

GET /health shall return HTTP 200 when the service is running and ready
to accept requests.

## Tickets

The service shall allow clients to create and manage service desk tickets.
Each ticket shall have a unique identifier and contain the information
required to determine its priority, current state and SLA.

Invalid input shall be rejected with an appropriate HTTP error response.

## Priority

Ticket priority shall be determined according to the service desk priority
matrix. The calculation shall be deterministic for the same ticket data.

The service shall also support tickets reported by VIP users according to
the selected VIP priority rules.

## Ticket state

Tickets shall follow a defined state machine. Only valid state transitions
shall be accepted.

The service shall support closing tickets and shall implement a defined
policy for reopening previously closed tickets.

Invalid state transitions shall be rejected.

## SLA

The service shall calculate SLA timing according to ticket priority.

The SLA implementation shall support the required SLA clock behaviour,
including pausing the clock when applicable and detecting an SLA breach.

The service shall support the test clock provided by the laboratory
environment so that SLA behaviour can be tested deterministically.

## Conflicting requirements

The specification contains conflicting requirements concerning:

- C1: SLA clock behaviour for P1 tickets.
- C2: closed tickets and reopening.
- C3: VIP reporters and the priority matrix.

For each conflict, one admissible behaviour shall be selected.
The selected behaviour and its justification shall be documented in
DECISIONS.md and must match the behaviour implemented by the service.

## Runtime

The service shall run using Docker Compose and expose the svcdesk service
on the port required by the course environment.

The application shall provide all dependencies inside the built container
and shall not require network access at runtime.