---
lab3_slo:
  service: svcdesk
  route: /kb/search
  window: 30d
  slis:
    availability:
      objective: 0.99
      good: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search", http_response_status_code!~"5.."}[5m]))'
      valid: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search"}[5m]))'
      error_budget: {fraction: 0.01, minutes: 432}
    latency:
      objective: 0.95
      threshold_seconds: 0.15
      good: 'sum(rate(http_server_request_duration_seconds_bucket{job="svcdesk", http_route="/kb/search", le="0.15"}[5m]))'
      valid: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search"}[5m]))'
      error_budget: {fraction: 0.05, minutes: 2160}
  alerts:
    - {alert: KbSearchErrorsBurnFast, sli: availability, burn_rate: 14.4, long_window: 1h, short_window: 5m}
    - {alert: KbSearchErrorsBurnSlow, sli: availability, burn_rate: 6, long_window: 6h, short_window: 30m}
---
<!-- ai-generated: 80% - ChatGPT helped draft the SLO structure and PromQL; I chose the objectives and latency threshold from my measured service profile -->

# SLO for `GET /kb/search`

Copy this file to `slo.md` at your repository root and replace every `TODO` above; MONITORING-SPEC.md section 5
has the rules (M-13 to M-16) and a filled-in example with made-up numbers. What the checker does with the front
matter:

- `L3-CORE-4.01` and `4.02`: every field is there, and the error-budget arithmetic holds;
- `4.03`: `threshold_seconds` is one of the boundaries your service exposes;
- `4.04`: the checker's Prometheus runs each `good` and `valid` after its measurement, and each returns exactly one
  sample (aggregate with `sum`), `valid` above 0, good / valid between 0 and 1. Its scrape job is `svcdesk`; never
  select an `instance`; write `le` as Prometheus 3 stores it, which may differ from what your service exposes:
  `le="0.3"`, `le="1.0"` (MONITORING-SPEC.md section 5, "The `le` label is text");
- `4.05` and L3-CORE-5: every alert declared here exists in `prometheus/alerts.yml` under the same name, with the
  label `slo` equal to its `sli` here, and behaves as declared - the checker's probes use exactly the burn rate and
  the windows you write here.

Everything below the front matter is read by the lecturer, not checked. Defend your numbers in plain prose; do not
restate the rules. Delete these instructions when you write the file.

## Availability

The SLI in words, the objective, and the error budget as a fraction and in minutes. Why this objective: what do
`kb-index`'s own failures, which you cannot fix, do to it?

## Latency

The SLI in words, the threshold, the objective, and the error budget. Why this threshold, against the distribution
you measured (your p50, p99 and the slow mode), and why this objective?
(Lab 6, on 28 November, reads this file's window, objectives and threshold - at most 1 s - as a canary gate's
thresholds: an objective your own service does not meet will make that gate roll back an honest release.)

## Alerts

| alert | SLI | burn rate | long / short window | budget spent when it fires | severity: page or chat |
|---|---|---|---|---|---|
| TODO | TODO | TODO | TODO | TODO | TODO |
| TODO | TODO | TODO | TODO | TODO | TODO |

Which alert pages a person (P1) and which goes to chat (P2, P3), and why: what a page at that burn rate costs the
person woken, and what waiting until the morning would cost the users.

## Buckets

Your ladder, where the p99 you measured falls in it, how wide that bucket is relative to the p99, how wide a band
around it you resolved and why, and where you spent the rest of your (at most 30) boundaries.
