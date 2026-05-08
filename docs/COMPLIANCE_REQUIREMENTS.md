# XChange Platform - Compliance Requirements (Sprint 13 Draft)

**Version:** 0.2  
**Date:** 08-May-2026  
**Status:** Draft (internal, pending legal validation)

## 1. Purpose

This document defines the compliance baseline needed to move XChange from simulation-only operation to live trading readiness in Phase 4.

This is a technical and operational draft. It must be reviewed and approved by UAE legal counsel before any production live trading.

## 2. Regulatory Scope (Working Assumptions)

- Jurisdiction: United Arab Emirates (UAE)
- Regulator: VARA (Virtual Assets Regulatory Authority)
- Operating model: Centralized exchange/broker front-end with external liquidity routing
- Live-trading gate: No account may enter LIVE mode unless KYC status is APPROVED

## 3. Mandatory Control Areas

### 3.1 Identity and KYC Controls
- Verified identity documents required before LIVE mode activation.
- Liveness check required for identity verification flow.
- KYC decision states must be auditable: PENDING, SUBMITTED, APPROVED, REJECTED.
- Manual admin review queue required for exceptions or failed automated checks.

### 3.2 AML Controls
- Screening required at two points:
  - Initial user registration (basic watchlist screening)
  - KYC approval stage (enhanced screening)
- Any positive or uncertain match must create a review case and block LIVE activation.
- AML decisions must be logged with reason codes and reviewer identity.

### 3.3 Auditability and Data Integrity
- All compliance-relevant events must be immutable and timestamped.
- Required event classes:
  - KYC submission
  - KYC decision updates
  - AML screening results
  - LIVE mode activation/deactivation
  - Admin override actions
- Audit records must include actor, action, entity, timestamp, and metadata.

### 3.4 Access Control
- Compliance endpoints require JWT authentication.
- KYC review/approval actions are admin-only.
- Least-privilege access model for compliance data.
- SUPER_USER account visibility is restricted to SUPER_ADMIN for discovery and profile access.
- Partner access to referred-user trade history is discretionary and must be explicitly granted by SUPER_ADMIN.

### 3.5 Security Baseline Before Live Trading
- TLS termination enabled in production.
- Restricted CORS allowlist for production domains.
- Brute-force controls for login endpoints.
- Structured security event logging enabled.
- Dependency vulnerability scans integrated into release process.

## 4. Compliance Data Schema (Phase 4 Baseline)

## 4.1 Required New Data Objects
- kyc_documents
  - user_id, document_type, file_reference, verification_status, created_at, reviewed_at
- aml_checks
  - user_id, provider_name, result, risk_score, matched_entities, checked_at
- compliance_cases
  - user_id, case_type, status, assigned_admin_id, notes, created_at, resolved_at

## 4.2 Existing Objects Used for Compliance
- users.kyc_status
- audit_logs
- admin action history

## 4.3 Retention (Draft Policy)
- KYC and AML evidence: retain for minimum 5 years after account closure.
- Audit logs for security/compliance actions: retain for minimum 5 years.
- Final retention period must be confirmed by legal counsel.

## 5. VARA Reporting Output (Draft)

## 5.1 Transaction Report Exports
- Monthly export scope:
  - Deposits
  - Withdrawals
  - Executed trades
  - Fees
- Output format:
  - CSV for operational use
  - JSON schema export option for future regulator API integration

## 5.2 SAR-Style Internal Workflow (Pre-Regulatory Submission)
- Manual flagging flow for suspicious activity events.
- Case status workflow:
  - OPEN -> UNDER_REVIEW -> ESCALATED -> CLOSED
- Evidence bundle: user profile, KYC record, transaction timeline, reviewer notes.

## 6. Sprint 13 Implementation Outputs

- Added this document: docs/COMPLIANCE_REQUIREMENTS.md
- Added provider evaluation draft: docs/KYC_AML_PROVIDER_EVALUATION.md
- Added KYC flow design draft: docs/KYC_FLOW_DESIGN.md
- Added user-service KYC submission scaffold and DB migration (technical kickoff for Sprint 14)
- Added RBAC expansion for PARTNER, POWER_USER, and SUPER_USER roles with visibility and permission controls.

## 7. Open Items Requiring Legal Input

- Confirm required license type and exact obligations.
- Confirm mandatory retention windows and deletion constraints.
- Confirm report fields and submission cadence expected by regulator.
- Confirm suspicious activity reporting threshold and process.

## 8. Go/No-Go Rule

LIVE mode must remain disabled globally until:
- Legal review is complete.
- KYC/AML provider is selected and integrated.
- Compliance logging and reporting controls are verified in staging.
