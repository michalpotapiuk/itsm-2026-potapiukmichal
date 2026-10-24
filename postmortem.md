---
lab4_postmortem:
  ticket: "50ceffde-fa49-40b3-b4ca-957734d74bf7"
  detecting_alert: ShopCheckoutErrors
  onset: 2026-10-12T06:36:23Z
  detection: 2026-10-12T06:39:19Z
  acknowledgement: 2026-10-12T06:40:09Z
  recovery: 2026-10-12T06:44:19Z
  mttd_seconds: 176
  mtta_seconds: 50
  mttr_seconds: 476
  identified_flags: [paymentFailure, loadGeneratorFloodHomepage]
---
<!-- ai-generated: 100% - Codex investigated the assigned recording, evaluated PromQL and drafted this retrospective for student review. -->

# Postmortem: failed checkouts during a homepage traffic surge

## Date

The recorded incident occurred on 12 October 2026, from 06:36:23Z to 06:44:19Z by the laboratory's detecting-alert definition. This retrospective was prepared on 24 October 2026. All times below are UTC.

## Authors

Prepared for Michał Potapiuk, the student reviewing the on-call simulation, with Codex assistance disclosed above. The original response and acknowledgement were performed by the lecturer's recorded on-call; this analysis did not operate that live system.

## Status

Retrospective analysis complete; proposed corrective actions remain open and require assignment in the team's real tracker. The recording's ticket remains acknowledged, with no resolved_at value. Alert recovery is evidenced, but ticket closure is not.

## Summary

Payment failures propagated into checkout while frontend request volume increased sharply. The detecting alert fired 176 seconds after onset, the ticket was acknowledged 50 seconds later, and the alert's first firing run ended 476 seconds after onset. The metrics support paymentFailure and loadGeneratorFloodHomepage from the published fault pool; the resource-class fault remains unidentified.

## Impact

At 06:42:00Z, 31.19% of checkout SERVER spans were errors over the preceding five minutes, with an error rate of 0.0321134/s. Query Q1 below divides checkout error spans by all checkout server spans. This measures failed service calls, not unique customers or payment losses; the recording contains synthetic traffic and no revenue measure.

By 06:44:19Z the checkout SERVER error counter held 8, from no baseline error series and its first emitted counter value of zero. Q2 reads this cumulative counter without counting duplicate CLIENT spans. Q3 estimates 8.153 errors in the 476-second alert-defined incident interval, and Q4 estimates 53.486 total checkout server calls in that interval. Fractional counts are Prometheus increase() extrapolations over minute-spaced telemetry, not fractional requests. The observed counter total of eight is the safer statement of recorded failures.

Frontend SERVER volume rose from 3.80833/s at 06:31:23Z to 63.40833/s at 06:42:00Z, about 16.65 times baseline (Q5). Checkout p99 stayed near 49.6 ms (Q6); high homepage traffic did not establish a sustained checkout latency incident. The 476 seconds describe the alert run's recovery boundary, not proof that every user-facing request had failed for the entire interval.

## Root Causes

The strongest explanation for the errors is paymentFailure. Internal payment charge errors, payment SERVER errors, checkout's payment CLIENT errors and checkout SERVER errors each measured 0.0321134/s at 06:42:00Z. That agreement fits failures propagating across the payment dependency; it does not independently prove a source-code defect, the configured percentage, or exact call ordering.

The second identification is loadGeneratorFloodHomepage: frontend SERVER volume rose about 16.65-fold, while checkout volume increased only from 0.09167/s to 0.10295/s. This distribution fits homepage flooding rather than a uniform rise in order demand. The published pool predicts roughly fifteenfold frontend traffic for that flag.

The injector seeds three classes. Neither emailMemoryLeak nor recommendationCacheFailure is sufficiently established by the observations retained here. Email container memory was 60,928,000 bytes at baseline and 61,190,144 at 06:42; recommendation memory decreased between those instants. Uptime advanced without an intervening reset visible at those endpoints. These measurements do not exclude short excursions or prove the absence of the sealed resource flag. Only the two supported flags are declared above.

The system weakness is that a failing payment dependency directly fails checkout, while independent browsing load can grow substantially without a release guard tied to customer symptoms. The flags are the simulation's fault mechanism; additional traces or source inspection would be needed to attribute a production defect.

## Trigger

The injector's recorded onset was 06:36:23Z after a healthy baseline. Its armed run introduced the combined fault. The onset is recomputed from the snapshot by the course checker; neither alert expressions nor ledger predictions use injector series to detect or explain customer symptoms.

## Resolution

The recorded operator recovered the simulation, and ShopCheckoutErrors stopped firing at 06:44:19Z. The recording documentation describes rollback of the incident flags, but the snapshot and ticket do not provide a timestamped operator command history. No per-flag rollback order or timestamp is claimed here.

For a recurrence, the proposed response is to disable the payment fault first to restore order processing, stop homepage flooding to reduce unnecessary demand, then inspect the remaining resource fault and verify all symptoms and error counters. This is a proposed runbook, not a claim that those actions were performed in that order. Wait for the detecting alert to resolve and check service telemetry before resolving the incident ticket.

## Detection

The recording's ShopCheckoutErrors fired at 06:39:19Z. The measured delay was 176 seconds from fault onset; ticket acknowledgement at 06:40:09Z gives MTTA 50 seconds. The page reached the pager, as verified against its notification counter by the checker. Without symptom alerting, a customer or synthetic order check would need to report failed checkouts.

The committed rules are our replacement policy, not the rules that generated the recording: a P1 for checkout errors above 5% and a P1 for p99 above 2000 ms, both with five-minute windows and a one-minute pending period. SERVER filtering avoids baseline load-generator client failures. A one-minute keep_firing_for limits brief gaps but also delays the measured alert recovery; those policy choices would change clocks in a new run. P2 elevated errors go to chat and are inhibited by P1 only for the same nonempty service label.

## Action Items

| Action Item | Type | Owner | Bug |
|---|---|---|---|
| Add a payment-failure rollback runbook with an order-success check before ticket resolution. | mitigate | Michał Potapiuk, operations owner | ITSM-401 |
| Gate payment flag changes on checkout SERVER error rate with automatic rollback on sustained regression. | prevent | Michał Potapiuk, service owner | ITSM-402 |
| Require investigators to echo the UTC incident window and reject tool times outside it. | process | Michał Potapiuk, AI workflow owner | ITSM-403 |
| Add homepage traffic and email/recommendation memory panels to the incident evidence checklist. | process | Michał Potapiuk, monitoring owner | ITSM-404 |

These are proposed follow-up identifiers, not claims that external tracker issues already exist. Each action has a concrete verification: successful synthetic checkout, a rollback exercise, an out-of-window query rejection, or resource and traffic evidence in the next drill.

## Lessons Learned

The useful unit of investigation is a claim paired with a query, a timestamp and a baseline result. Repeated claims about one component are not coverage of three independent fault classes.

### What went well

The recording preserves both ticket acknowledgement and its telemetry, so response timing is independently checkable. Payment internal, server and checkout client errors agree. A fixed snapshot makes both investigators' claims reproducible.

### What went wrong

The recorded model switched from 2026-10-12 to 2024-04-14 in steps 5–7, interpreting empty vectors outside the recording as potentially absent errors. It then repeated the payment diagnosis without investigating traffic or resources. Its checkout span abbreviation also differs from the actual label; copying that selector literally would test nothing.

### Where we got lucky

Earlier range-query results still showed payment errors, letting the model recover part of the diagnosis despite its date error. The traffic surge did not produce sustained checkout latency in the measured window. Neither fact guarantees resilience under higher load or a longer incident.

## Timeline

This is a retrospective reconstruction. Ledger evaluations dated 24 October are attached to the recording instants they test; they were not actions available to the lecturer during the original response.

| UTC, 2026-10-12 | Evidence or event |
|---|---|
| 06:31:23 | Baseline control, exactly onset minus five minutes: no payment charge or checkout SERVER error vector; frontend SERVER rate 3.80833/s. |
| 06:35:23 | Last quiet minute before onset, covered by the checker's ten-minute healthy baseline gate. |
| 06:36:23 | Fault onset, recomputed from the single armed run. |
| 06:39:19 | ShopCheckoutErrors begins firing: MTTD 176 s. |
| 06:39:44 | Recorded operator creates P1 ticket 50ceffde-fa49-40b3-b4ca-957734d74bf7. |
| 06:40:09 | Recorded acknowledgement: MTTA 50 s. |
| 06:42:00 | Retrospective H1/H2: `sum(rate(traces_span_metrics_calls_total{service_name="payment",span_kind="SPAN_KIND_INTERNAL",span_name="charge",status_code="STATUS_CODE_ERROR"}[5m])) > 0.01` returns 0.0321134/s; no result on baseline. Supports paymentFailure. |
| 06:42:00 | Retrospective H3/H4: payment charge and checkout payment CLIENT/SERVER error comparisons in ai-rca-eval.json each return true; H4 is partial because its span label was abbreviated. Supports propagation, without proving temporal causation. |
| 06:42:00 | Retrospective S2: `sum(rate(traces_span_metrics_calls_total{service_name="frontend",span_kind="SPAN_KIND_SERVER"}[5m])) > 30` returns 63.40833/s; baseline comparison is empty. Supports homepage flooding. S1/S3 reproduce payment and checkout failures with their full ledger queries. |
| 06:44:19 | Detecting alert's first firing run ends: MTTR 476 s. This is the checker-defined recovery, not a ticket closure timestamp. |

## Supporting information

The incident artifacts are incident/tsdb-snapshot.tar.gz and incident/ticket.json, copied byte-for-byte from the login-assigned lab4-rec-4. The source Qwen transcript is ai-rca/transcript.md, its scored claims are ai-rca-eval.json, and the second investigation and comparison are under ai-rca/second/ and ai-rca/COMPARISON.md. ai-rca/evidence.json retains actual HTTP query results at the baseline, incident and recovery instants. Serve a freshly extracted snapshot and use explicit evaluation times to reproduce them.

`./itsmlab.sh incident 4` returned run c1daa7d0f4acf990, onset 06:36:23Z, detection 06:39:19Z, acknowledgement 06:40:09Z and recovery 06:44:19Z. MTTD=176, MTTA=50, MTTR=476 seconds. These are single-incident differences, not population means, and recovery depends on the alert expression, evaluation interval and pending/hold policy. ai-rca/alert-replay.json records a counterfactual expression replay: all three new expressions were false across the ten-minute baseline; the checkout error expression first matched on the 10-second query grid at 06:38:13Z, before its one-minute pending period. This is not the firing history of these new rules, which did not run in the recording.

Queries Q1–Q6 (evaluate at 2026-10-12T06:42:00Z unless otherwise stated):

```promql
# Q1: checkout error fraction
sum(rate(traces_span_metrics_calls_total{service_name="checkout",span_kind="SPAN_KIND_SERVER",status_code="STATUS_CODE_ERROR"}[5m])) / sum(rate(traces_span_metrics_calls_total{service_name="checkout",span_kind="SPAN_KIND_SERVER"}[5m]))
# Q2: cumulative recorded errors, at recovery
sum(traces_span_metrics_calls_total{service_name="checkout",span_kind="SPAN_KIND_SERVER",status_code="STATUS_CODE_ERROR"})
# Q3: extrapolated error count, at recovery
sum(increase(traces_span_metrics_calls_total{service_name="checkout",span_kind="SPAN_KIND_SERVER",status_code="STATUS_CODE_ERROR"}[476s]))
# Q4: extrapolated total calls, at recovery
sum(increase(traces_span_metrics_calls_total{service_name="checkout",span_kind="SPAN_KIND_SERVER"}[476s]))
# Q5: frontend volume, also evaluate at 06:31:23Z
sum(rate(traces_span_metrics_calls_total{service_name="frontend",span_kind="SPAN_KIND_SERVER"}[5m]))
# Q6: checkout p99 in milliseconds
histogram_quantile(0.99,sum by(le)(rate(traces_span_metrics_duration_milliseconds_bucket{service_name="checkout",span_kind="SPAN_KIND_SERVER"}[5m])))
```

## Problem record

Incident record: 50ceffde-fa49-40b3-b4ca-957734d74bf7; recorded P1 response with alert recovery evidenced and ticket closure unrecorded.
Root cause: Payment charge failures propagate to checkout while homepage traffic is independently amplified; the third resource fault remains unconfirmed.
Known error: The published paymentFailure and loadGeneratorFloodHomepage controls reproduce the two observed symptom classes; no source-code defect or exact variants have been proven.
Workaround: Roll back the implicated payment and load flags, investigate the resource class separately, and confirm successful orders and alert resolution before closing the incident.
