---
actual_minutes: 80
---

<!-- ai-generated: 100% - drafted with ChatGPT from the recorded prediction and completed Lab 2 implementation -->

# METR n=1 replication

The predicted implementation time for the Lab 2 DORA metrics feature was 45 minutes.

The actual implementation time was approximately 80 minutes. The work included implementing the `POST /dora/metrics` endpoint, applying the published metric rules and six edge cases, adding `GET /dora/ticket-events`, preparing `metrics.json`, completing `EDGE-CASES.md`, and building the gaming demonstration.

The main source of additional effort was not the basic endpoint itself, but matching the detailed behaviour required by `METRIC-SPEC.md`. The revert-chain handling, failed deployment recovery logic, overlapping incidents, and gaming constraints required extra validation against the checker.

The ratio of actual time to predicted time is:

`actual/predicted = 80/45 = 1.78`

The implementation therefore took 1.78 times the predicted duration.

This result shows that the original estimate underestimated the effort required to translate the detailed metric rules into a fully conforming implementation. The straightforward API work was relatively quick, while the edge cases and required supporting artifacts accounted for most of the additional time.