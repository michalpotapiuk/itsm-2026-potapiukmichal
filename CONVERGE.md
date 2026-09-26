<!-- ai-generated: 100% - drafted with ChatGPT from the Lab 1 requirements, API contract and checker results -->

# svcdesk Convergence Report

## Validation scope

This report compares the implemented svcdesk service with the requirements,
API contract, documented decisions and automated checker results.

The implementation was validated against the following requirements:

R-02 - The service exposes GET /health and returns a successful health response.

R-04 - Ticket priority is calculated from the impact and urgency priority matrix.

R-05 - Priority is controlled by the service and a priority supplied by the client is ignored.

R-07 - Tickets follow the required lifecycle:
new -> acknowledged -> in_progress -> resolved -> closed.

R-08 - Invalid state transitions are rejected with HTTP 409.

R-12 - SLA acknowledgement and resolution targets are calculated according to ticket priority.

R-13 - Business-hour SLA calculations use Monday to Friday from 08:00 to 16:00 in Europe/Warsaw.

R-15 - The SLA endpoint reports priority, due times, breach state and paused state.

R-16 - SLA breach and pause behaviour is calculated according to the current ticket state and time.

R-21 - The service supports X-Test-Clock when SVCDESK_TEST_CLOCK is enabled.

R-22 - The service runs through Docker Compose as a service named svcdesk.

R-24 - The service starts and answers GET /health within the required startup window.

## C1 convergence

Decision C1 is wallclock.

P1 acknowledgement and resolution SLA targets use wall-clock time and continue
running outside normal business hours.

P2, P3 and P4 continue to use the business-hours clock.

The running implementation matches the C1 value declared in DECISIONS.md.

## C2 convergence

Decision C2 is immutable.

Resolved tickets may be reopened within the permitted seven-day window.

Closed tickets cannot be reopened. Further work on a closed issue requires a
new ticket referencing the previous ticket.

The running implementation matches the C2 value declared in DECISIONS.md.

## C3 convergence

Decision C3 is vip.

The normal impact and urgency matrix is evaluated first.

If a VIP ticket would receive priority P3 or P4, the implementation promotes
the ticket to P2. Existing P1 and P2 priorities are unchanged.

The running implementation matches the C3 value declared in DECISIONS.md.

## Docker validation

The Docker Compose configuration defines the required svcdesk service.

The service is built from the repository, listens on port 8080 and has
SVCDESK_TEST_CLOCK enabled.

A named Docker volume is used instead of a host-path bind mount.

Dependencies are installed during the image build so that the application does
not require network access at runtime.

## Checker evidence

The automated Lab 1 checker successfully validates the Core implementation.

The observed decisions are:

- C1 = wallclock
- C2 = immutable
- C3 = vip

These observed values match DECISIONS.md.

The official grader has also confirmed that the specification-first workflow
passes.

## Conclusion

The implemented svcdesk service, specification, API contract and documented
decisions converge on one consistent behaviour.

The implementation satisfies the selected requirements and there are no
remaining conflicts between C1, C2, C3 and the running service.