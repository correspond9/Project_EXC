# KYC/AML Provider Evaluation - Sprint 13 Draft

**Date:** 08-May-2026  
**Status:** Draft for decision support (not final)

## 1. Objective

Evaluate candidate providers for KYC and AML integration in Phase 4:
- Sumsub
- Jumio
- Onfido

## 2. Evaluation Criteria

| Criterion | Weight | Notes |
|---|---:|---|
| API reliability and documentation quality | 20 | SDK quality, webhook reliability, API ergonomics |
| KYC coverage and verification strength | 20 | Document support, liveness, fraud signals |
| AML screening capability | 15 | Watchlist and sanction checks, ongoing monitoring |
| Turnaround time and user experience | 15 | User conversion and verification speed |
| Pricing and scalability | 15 | Cost per verification and volume scaling |
| Compliance reporting support | 10 | Exportability, audit traces, case management |
| Integration effort for current stack | 5 | FastAPI compatibility and implementation complexity |

## 3. Initial Comparative Notes

| Provider | Strengths | Risks / Unknowns |
|---|---|---|
| Sumsub | Strong all-in-one KYC + AML posture, mature docs | Commercial terms and UAE-specific support to confirm |
| Jumio | Established identity verification workflows | AML depth and integration fit need validation |
| Onfido | Strong identity UX and onboarding tooling | AML breadth may require additional tooling |

## 4. Shortlist Outcome (Current)

No final provider selected yet.

Current working direction:
- Keep Sumsub and Jumio as the primary shortlist for deep validation.
- Keep Onfido as backup option if pricing or jurisdiction constraints require it.

## 5. Decision Checklist (Before Selection)

- Confirm UAE and VARA alignment with legal counsel.
- Verify webhook event model maps cleanly to target KYC states.
- Verify AML screening data and match explanation quality.
- Confirm pricing under expected academy and growth volumes.
- Complete a technical proof-of-concept against user-service sandbox.

## 6. Next Action

Run a provider POC in Sprint 14 and finalize selection before production LIVE mode work.