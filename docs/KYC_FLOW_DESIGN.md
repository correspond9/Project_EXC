# KYC Flow Design (Phase 4)

**Version:** 0.2  
**Date:** 08-May-2026  
**Status:** Approved for implementation planning

## 1. Goal

Define a KYC flow that blocks LIVE trading activation until identity and AML checks are complete and auditable.

## 2. State Machine

User-level KYC states:
- PENDING: No documents submitted yet.
- SUBMITTED: Documents received and awaiting verification.
- APPROVED: Verification completed successfully.
- REJECTED: Verification failed or denied.

Allowed transitions:
- PENDING -> SUBMITTED
- SUBMITTED -> APPROVED
- SUBMITTED -> REJECTED
- REJECTED -> SUBMITTED (resubmission)

## 3. End-to-End Flow

1. User submits KYC package
- Required: identity document(s) and selfie/liveness capture reference.
- API: POST /api/kyc/submit
- System updates user.kyc_status to SUBMITTED.
- Audit log event: KYC_SUBMITTED.

2. Provider verification stage
- Service sends submission to selected KYC provider.
- Provider returns webhook updates for checks and final decision.

3. AML screening stage
- Triggered when KYC result is positive or near-final.
- If AML passes: continue to approval.
- If AML flags match: open compliance case and hold approval.

4. Admin review and decision
- Admin queue shows pending and flagged cases.
- Admin can approve/reject with reason.
- Audit log event: KYC_APPROVED or KYC_REJECTED.

5. LIVE mode gating
- trading_mode can switch to LIVE only when KYC_APPROVED is present.
- For POWER_USER and SUPER_USER, the same KYC_APPROVED gate applies before LIVE activation.

## 4. Error and Retry Handling

- Partial document upload: reject submission with validation error.
- Provider timeout: retain SUBMITTED state and retry asynchronously.
- Webhook replay: enforce idempotency by provider event id.
- Manual override: admin action required and fully audited.

## 5. Data and Audit Requirements

Minimum data to persist:
- submission timestamp
- document type metadata
- provider reference id
- decision status and reason
- reviewer identity for manual decisions

Audit events required:
- KYC_SUBMITTED
- KYC_PROVIDER_UPDATED
- AML_CHECK_COMPLETED
- KYC_APPROVED
- KYC_REJECTED
- LIVE_MODE_ACTIVATED

## 6. API Surface for Sprint 14

- POST /api/kyc/submit
- GET /api/kyc/status
- GET /api/admin/kyc/queue
- POST /api/admin/kyc/{user_id}/approve
- POST /api/admin/kyc/{user_id}/reject
- POST /api/kyc/webhook/provider

## 7. Security Constraints

- KYC endpoints require JWT.
- Admin review endpoints require ADMIN or SUPER_ADMIN.
- Store only references to binary files in app DB; binary storage lives in object storage.
- All compliance logs are immutable and timestamped.
- SUPER_USER profiles remain non-discoverable to non-SUPER_ADMIN operators in admin surfaces.
