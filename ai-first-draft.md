---
lab3_first_draft:
  source: ai
  tool: "ChatGPT GPT-5.6 Sol, 10 October 2026"
  ladder: [0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.35, 0.5, 0.75, 1.0, 1.5, 2.0]
  verdict: refuted
  evidence: {p99_seconds: 0.146, bucket: [0.1, 0.15], relative_width: 0.342}
lab3_flawed_ladder:
  verdict: refuted
  evidence: {p99_seconds: 0.146, bucket: [0.04, 0.5], relative_width: 3.151}
---
<!-- ai-generated: 80% - ChatGPT provided the first draft and helped calculate the verdict arithmetic; I validated it using my own load measurement -->

# The assistant's first draft, and two verdicts

Copy this file to `ai-first-draft.md` at your repository root. The rules are M-25 to M-27 in MONITORING-SPEC.md
(section 9, with a filled-in example for the practice profile); the checks are `L3-CORE-3.07` to `3.09`.

1. **Before you measure or design anything**, ask an assistant for histogram bucket boundaries and an alert rule
   for `GET /kb/search`. Paste your prompt under `## Prompt` and its whole answer under `## Answer`, verbatim. If
   the answer itself contains lines that begin with `## `, put `> ` in front of every line of it: the checker
   reads a section up to the next line that begins with `## `, and each section needs at least 40 characters.
2. Copy its ladder into `ladder`, in seconds, exactly as it gave it.
3. Measure with `./itsmlab.sh load 3` (Windows: `.\itsmlab.ps1 load 3`) and write the p99 it prints as
   `p99_seconds`, in seconds, in both `evidence` blocks. It must be within 30 % of the checker's own q.
4. For each ladder, `bucket` is `[lo, hi]` of the bucket that holds that p99 (lo is 0 below the first boundary; hi
   is `"+Inf"` above the last), and `relative_width` is (hi - lo) / p99_seconds, to three decimals.
5. `verdict`: `confirmed` when hi is finite and hi - lo is at most 0.20 x p99, else `refuted`. The checker applies
   the same rule at its own q; both verdicts score the same, and only a verdict its measurement contradicts fails.

No AI at all: set `source: instructor`, delete `tool`, copy the fourteen boundaries of `buckets-flawed.example.yml`
into `ladder`, and delete `## Prompt` and `## Answer`. Delete these instructions when you write the file.

## Prompt

I am instrumenting GET /kb/search in a small HTTP service with a Prometheus histogram.

Before I have measured the service, propose:
1. A reasonable set of histogram bucket boundaries in seconds for HTTP latency.
2. A Prometheus alert rule for an SLO burn-rate alert for this route.

The bucket ladder should be suitable for a service that is usually fast but may have a slower tail.

## Answer

For an HTTP endpoint that is usually fast but may have a slower tail, I would start with the following histogram bucket boundaries in seconds:

[0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.35, 0.5, 0.75, 1.0, 1.5, 2.0]

This ladder spends more resolution below 250 ms, where interactive request latency is likely to matter most, while still retaining several buckets for slower responses and timeouts.

For alerting, I would use a multi-window burn-rate alert rather than alerting directly on raw error percentage. For example, assuming a 99% availability SLO, define the error ratio for GET /kb/search as the rate of non-successful requests divided by the rate of all valid requests.

A fast burn alert could require both a one-hour and a five-minute error ratio to exceed 14.4 times the allowed error budget:

(1 - success_ratio_1h) > 14.4 * (1 - 0.99)
and
(1 - success_ratio_5m) > 14.4 * (1 - 0.99)

This alert should page because a sustained burn at that rate would consume the error budget quickly.

A slower alert could use a lower burn rate over longer windows and notify a chat channel instead of paging. The exact SLO objective, route filters, latency threshold and windows should be chosen after measuring the real service.

## Verdict on the draft ladder

The measured p99 was 0.146 s. In the assistant's original ladder this value falls in the bucket (0.10, 0.15]. The bucket width is 0.05 s, so its relative width is 0.05 / 0.146 = 0.342, or 34.2%.

Because 34.2% is greater than the maximum allowed width of 20% of the measured p99, the assistant's original ladder does not resolve my p99 and is therefore refuted.

Within this bucket, histogram_quantile could estimate the p99 anywhere between 0.10 s and 0.15 s depending on the observations inside the bucket. That interval is too wide for the required resolution around the measured tail latency.

## The draft alert rule

The assistant proposed a multiwindow burn-rate approach with a fast alert using a 14.4 burn rate over both a one-hour and a five-minute window. I kept the general idea of combining a long and a short window, because this avoids paging on a brief isolated spike while still detecting a sustained fast burn.

The final alert thresholds and SLO objective will be based on the SLO defined in slo.md rather than copying the draft values blindly.

## Verdict on the instructor's flawed ladder

The measured p99 was 0.146 s. In the instructor's flawed ladder this value falls in the bucket (0.04, 0.50]. The bucket width is 0.46 s, so its relative width is 0.46 / 0.146 = 3.151, or 315.1%.

This is far above the allowed 20% width, so the flawed ladder is refuted. The ladder spends too little resolution around the observed slow mode of my service. For this p99, histogram_quantile could return a value anywhere inside a very wide interval from 0.04 s to 0.50 s, which would make the reported tail latency operationally imprecise.
