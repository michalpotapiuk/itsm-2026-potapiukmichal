---
lab4_comms:
  awareness: 2026-10-12T06:40:09Z
  detection: 2026-10-12T06:39:19Z
  classification: 2026-10-12T06:45:00Z
  nis2:
    early_warning_due: 2026-10-13T06:40:09Z
    notification_due: 2026-10-15T06:40:09Z
    notification_sent: 2026-10-12T09:00:00Z
    final_report_due: 2026-11-12T09:00:00Z
  ksc:
    early_warning_due: 2026-10-13T06:39:19Z
    notification_due: 2026-10-15T06:39:19Z
    notification_sent: 2026-10-12T09:00:00Z
    final_report_due: 2026-11-12T09:00:00Z
  dora:
    initial_due: 2026-10-12T10:45:00Z
    initial_sent: 2026-10-12T07:00:00Z
    intermediate_due: 2026-10-15T07:00:00Z
    intermediate_sent: 2026-10-12T09:00:00Z
    final_due: 2026-11-12T09:00:00Z
  log:
    - {at: 2026-10-12T06:40:09Z, to: incident commander, what: Confirm failed checkouts and acknowledge P1; start significance assessment}
    - {at: 2026-10-12T06:45:00Z, to: regulatory reporting owner, what: Classify assumed major ICT incident after initial recovery assessment}
    - {at: 2026-10-12T07:00:00Z, to: appropriate CSIRT or competent authority, what: Proposed NIS2 and KSC early warning with known impact and uncertainty}
    - {at: 2026-10-12T07:00:00Z, to: competent financial supervisor, what: Proposed DORA initial notification}
    - {at: 2026-10-12T09:00:00Z, to: appropriate CSIRT or competent authority, what: Proposed NIS2 and KSC incident notification}
    - {at: 2026-10-12T09:00:00Z, to: competent financial supervisor, what: Proposed DORA intermediate report following service recovery}
    - {at: 2026-11-12T09:00:00Z, to: reporting authorities, what: Proposed final reports with causes and corrective actions}
---
<!-- ai-generated: 100% - Codex calculated UTC deadlines using the lab specification and checked official legal sources. -->

# Simulated regulatory communications

## Scope and decision instants

This exercise assumes the shop falls within all three regimes and the incident is significant under NIS2/KSC and major under DORA, as the laboratory requests. Eight synthetic failed orders alone do not establish those legal classifications. Every communication here is a proposed simulation entry; no authority was contacted, and the recording provides no evidence that these reports were actually sent.

Detection is 2026-10-12T06:39:19Z, when ShopCheckoutErrors first fired. That is the reproducible KSC detection anchor used in this exercise. Awareness of significance is set to 06:40:09Z, when the on-call acknowledged the P1 and could connect the symptom to failed checkout service. This is a defended scenario choice, not an additional timestamp measured from regulatory records. It deliberately distinguishes a machine's detection from a responder's awareness by 50 seconds.

Major classification is assumed at 06:45:00Z, after the recorded alert recovery at 06:44:19Z, allowing an initial review of impact. Restoration does not erase an incident's classification or reporting clock. The classification decision itself is hypothetical and should be recorded explicitly in a real incident.

## Proposed communications and clocks

At 06:40:09Z the incident commander receives the P1 acknowledgement and known impact. At 06:45Z the reporting owner records the assumed major classification. At 07:00Z the CSIRT or competent authority would receive the NIS2/KSC early warning, and the financial supervisor would receive the DORA initial notification. No malicious origin or cross-border impact is asserted without evidence; those fields would be marked unknown pending investigation.

The 09:00Z NIS2/KSC notifications would provide the initial impact assessment and remaining uncertainty. Their final reports are due one calendar month after these notifications, on 12 November at 09:00Z. The DORA intermediate report is proposed for the same 09:00Z, following the initial notification and service recovery; it need not wait for its outer 72-hour deadline. The DORA final deadline is one calendar month after that intermediate report. These are deadline calculations, not a recommendation to wait until the deadline to report.

| Clock | Anchor | Early or initial deadline | Notification or intermediate deadline | Final deadline |
|---|---|---|---|---|
| NIS2 | Awareness 12 Oct 06:40:09Z | 13 Oct 06:40:09Z | 15 Oct 06:40:09Z | 12 Nov 09:00:00Z |
| KSC | Detection 12 Oct 06:39:19Z | 13 Oct 06:39:19Z | 15 Oct 06:39:19Z | 12 Nov 09:00:00Z |
| DORA | Classification 12 Oct 06:45:00Z | 12 Oct 10:45:00Z | 15 Oct 07:00:00Z | 12 Nov 09:00:00Z |

For DORA, classification is within 24 hours of awareness. The initial deadline is the earlier of classification plus four hours (12 Oct 10:45Z) and awareness plus 24 hours (13 Oct 06:40:09Z). Thus the four-hour limit binds. The intermediate outer deadline runs from the proposed 07:00Z initial submission, rather than from detection or classification. All month arithmetic follows the laboratory's UTC-calendar rule; weekend relief is ignored as instructed. This recording predates the Warsaw daylight-saving change, but UTC avoids a local-clock ambiguity in any attempt.

## Sources

The laboratory arithmetic follows INCIDENT-SPEC.md section 4.7. Official sources checked on 24 October 2026 are [NIS2, Article 23](https://eur-lex.europa.eu/eli/dir/2022/2555/oj), [the Polish KSC amendment, Dz. U. 2026 poz. 252](https://eli.gov.pl/eli/DU/2026/252/ogl), and [Delegated Regulation (EU) 2025/301, Article 5](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32025R0301). NIS2 anchors warning/notification to awareness; the lab applies KSC's detection wording. DORA distinguishes classification, awareness and submission anchors. Actual jurisdiction, recipients and significance criteria would need the entity's compliance assessment; they are assumptions of this simulation.
