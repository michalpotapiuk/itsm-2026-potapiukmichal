---
lab2_edge_cases:
  E1: {rule: R-08, count: 3}
  E2: {rule: R-06, count: 2}
  E3: {rule: R-09, count: 4}
  E4: {rule: R-10, count: 4}
  E5: {rule: R-12, count: 1}
  E6: {rule: R-13, count: 11}
---
<!-- ai-generated: 100% - drafted with ChatGPT from METRIC-SPEC.md and the counts reported by my running service -->

# Edge cases in the practice event log

## E1 - clock skew produces a negative lead time

- What the log contains: The log contains commits whose timestamps are later than the successful production deployment that delivered them.
- What a default definition would have done: A naive calculation could discard these observations or expose a negative lead time that has no useful operational meaning.
- Why the rule is defensible: Clamping the duration to zero keeps the observation while explicitly recording the clock-skew anomaly instead of silently hiding it.

## E2 - a revert of a revert

- What the log contains: The log contains revert commits, including a revert that points to another revert and therefore forms a transitive revert chain.
- What a default definition would have done: A simple implementation could treat every revert commit as a separate change and inflate the number of changes represented in the data.
- Why the rule is defensible: Resolving the chain back to the original change keeps change identity stable and avoids counting rollback mechanics as new product work.

## E3 - a hotfix that never touched main

- What the log contains: Some commits were deployed to production from branches other than main and still represent changes that reached users.
- What a default definition would have done: Filtering only commits whose branch equals main would incorrectly remove valid production changes from the metric calculation.
- Why the rule is defensible: Production delivery is determined by the deployment itself, so the branch name should not decide whether delivered work counts.

## E4 - a deployment with zero linked commits

- What the log contains: Several production deployments contain an empty commits array even though the deployments themselves are valid deployment events.
- What a default definition would have done: A naive implementation might discard these deployments entirely because there are no commits available for lead-time calculation.
- Why the rule is defensible: The deployment still occurred and therefore belongs in deployment frequency and deployment-based rates, even though it creates no lead-time pair.

## E5 - a deployment that failed and never recovered

- What the log contains: One failed production deployment has no usable recovery instant because no covering incident resolves it.
- What a default definition would have done: A naive implementation might invent a recovery at the end of the window or remove the failed deployment from failure statistics.
- Why the rule is defensible: Leaving the failure open avoids inventing recovery data while still preserving it in the change-fail-rate denominator.

## E6 - overlapping incidents

- What the log contains: Multiple incident intervals overlap in time, including incidents that may cover different failed deployments during the same period.
- What a default definition would have done: A simplistic calculation could merge overlapping incidents or sum their durations and distort recovery measurements.
- Why the rule is defensible: Recovery belongs to each failed deployment independently, so overlapping incidents should remain separate while their overlap is recorded as an anomaly.

## Gaming demonstration

The gaming demonstration will use a permitted transformation of the practice log to improve one reported metric while making delivery of the original work measurably worse. The final explanation will be completed together with `gaming.json` and `gaming/after.jsonl`.