---
svcdesk_decisions:
  C1: wallclock
  C2: immutable
  C3: vip
---
<!-- ai-generated: 100% - drafted with ChatGPT based on the selected Lab 1 decisions and reviewed by the student -->

# Decisions

## C1 - SLA clock for P1

**Decision:** P1 acknowledgement and resolution targets use the wall-clock model, so their SLA timers continue running outside normal business hours.

**Rejected alternative:** The rejected alternative was the business-hours model, where P1 SLA timers would pause outside the defined service desk business hours.

**Reason:** P1 tickets represent the most critical incidents, therefore their acknowledgement and resolution targets should continue running regardless of evenings or weekends.

**Service owner:** The Service Desk product owner should approve this decision because this role is responsible for defining SLA expectations and handling critical incidents.

**Customer outcome:** Users reporting critical P1 incidents receive a continuous SLA commitment, ensuring that high-impact problems remain urgent regardless of when they occur.

## C2 - Closed tickets and reopening

**Decision:** Closed tickets are immutable and cannot be reopened. Further work on the same issue requires creating a new ticket referencing the previous ticket.

**Rejected alternative:** The rejected alternative was allowing closed tickets to be reopened within seven days and returned to the in-progress state.

**Reason:** Keeping closed tickets immutable provides a clear and reliable ticket history and ensures that closing a ticket represents a final lifecycle state.

**Service owner:** The Service Desk product owner should approve this decision because this role is responsible for ticket lifecycle rules, reporting and service desk governance.

**Customer outcome:** Customers receive a clear history of completed work, while recurring issues can still be tracked through new tickets linked to the original ticket.

## C3 - VIP reporters and the priority matrix

**Decision:** The normal priority matrix is applied first, but VIP tickets calculated as P3 or P4 are promoted to P2 while P1 and P2 remain unchanged.

**Rejected alternative:** The rejected alternative was using only the impact and urgency matrix, where the VIP flag would be stored but would not influence ticket priority.

**Reason:** Promoting lower-priority VIP tickets to P2 increases their visibility to the service desk without overriding genuinely critical P1 incidents.

**Service owner:** The Service Desk product owner should approve this decision because this role is responsible for prioritisation rules and operational response expectations.

**Customer outcome:** VIP reporters receive increased visibility for their lower-priority issues while the standard priority matrix continues to identify genuinely critical incidents.