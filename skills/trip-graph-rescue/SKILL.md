---
name: trip-graph-rescue
description: Analyze a synthetic multi-component travel disruption without executing refunds, rebooking, or customer outreach
---

# Trip Graph Rescue

## Use when

- A synthetic flight delay, supplier cancellation, weather event, or local issue may affect linked travel components
- An operator needs a deterministic incident brief before making a human-approved decision

## Safety boundary

- Accept only synthetic and de-identified JSON fixtures
- Calculate timing, dependency, buffer, and explicit policy constraints in code
- Never call airline, inventory, payment, refund, rebooking, or messaging APIs
- Mark missing policy as `counselor_confirmation_required`
- Mark safety, dispute, and local-issue events as `operations_lead_or_safety_approval_required`

## Run

```bash
python scripts/analyze_trip.py fixtures/paris_flight_delay.json
```

## Output

- Impacted graph nodes and calculation evidence
- Alternative candidates that satisfy explicit constraints
- Excluded candidates and the reason for exclusion
- Approval gates and a customer-message draft separated into facts, options, and follow-up
