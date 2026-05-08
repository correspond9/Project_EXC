# AML/CFT Programme — XChange Platform

**Document Version:** 1.0  
**Effective Date:** [Date upon VARA approval]  
**Document Owner:** Chief Compliance Officer  
**Approved by:** Board of Directors  
**Regulatory Framework:** VARA AML/CFT Guidelines, UAE Federal Decree-Law No. 20 of 2018 (AML), UAE Cabinet Resolution No. 10 of 2019, FATF Recommendations

---

## 1. Purpose & Scope

This document describes the Anti-Money Laundering and Counter-Financing of Terrorism (AML/CFT) programme of [Company Name] ("the Company"), operator of the XChange virtual asset trading platform. This programme applies to:
- All user-facing services (registration, KYC, trading, deposits, withdrawals)
- All staff and contractors with access to user data or financial flows
- All third-party providers involved in customer onboarding or fund processing

---

## 2. Governance & Accountability

### 2.1 MLRO (Money Laundering Reporting Officer)
The Company has appointed a designated MLRO who is responsible for:
- Oversight of day-to-day AML/CFT compliance
- Receiving internal SAR (Suspicious Activity Reports) from staff
- Filing STRs (Suspicious Transaction Reports) with the UAE Financial Intelligence Unit (FIU) via goAML
- Maintaining AML risk assessments and policy documentation
- Liaising with VARA on regulatory matters

### 2.2 Board Oversight
The Board of Directors approves this policy annually and receives quarterly AML compliance reports.

---

## 3. Risk Assessment

### 3.1 Business Risk Factors
| Risk Category | Assessment | Mitigation |
|---------------|-----------|------------|
| Customer risk (anonymous cash users) | LOW — KYC required before LIVE trading | Full KYC with document verification |
| Geographic risk (FATF high-risk jurisdictions) | MEDIUM | Country blocklist on registration |
| Product risk (futures/leveraged trading) | MEDIUM | Position limits, leverage caps |
| Channel risk (online-only) | MEDIUM | IP monitoring, device fingerprinting |
| Transaction risk (large withdrawals) | MEDIUM | Manual admin review of all withdrawals |

### 3.2 Customer Risk Classification
- **Low risk:** UAE residents with verified Emirates ID, salaried employees, small transaction volumes
- **Medium risk:** Non-UAE residents with valid passport, frequent trading
- **High risk:** PEPs, high-value transactions, unusual patterns — subject to Enhanced Due Diligence (EDD)

---

## 4. Customer Due Diligence (CDD)

### 4.1 Standard CDD (all users before LIVE trading)
1. Full legal name and date of birth
2. Nationality and country of residence
3. Government-issued photo ID (Passport or Emirates ID)
4. Proof of address (utility bill or bank statement — less than 3 months old)
5. Selfie / liveness check
6. AML screening against sanctions lists and adverse media

### 4.2 Enhanced Due Diligence (EDD) Triggers
- PEP (Politically Exposed Person) status
- Transaction volume above [configurable threshold]
- Country of residence on FATF grey/blacklist
- Adverse media hits during AML screening
- Unusual trading patterns flagged by the transaction monitoring system

### 4.3 Ongoing Monitoring
- All transactions are logged in the immutable `balance_ledger`
- Trading activity reviewed for patterns indicative of wash trading, layering, or structuring
- Annual refresh of KYC documents for active live-trading users

---

## 5. Suspicious Activity Monitoring & Reporting

### 5.1 Transaction Monitoring Rules
The following patterns trigger enhanced review:
- Multiple deposits just below AED 55,000 (structuring indicator)
- Rapid deposits followed by immediate full withdrawal with no trading
- Trading account used only for pass-through fund movement
- Transactions involving addresses on public blockchain sanction lists
- Unusually large single transactions (above configurable threshold)

### 5.2 SAR Workflow
1. Staff or automated system identifies suspicious activity
2. Internal SAR filed with MLRO via `POST /api/admin/compliance/sar/{user_id}`
3. MLRO reviews within 3 business days
4. If grounds for suspicion confirmed: STR filed with UAE FIU via goAML within 35 days
5. Account may be suspended pending MLRO review

### 5.3 Record Keeping
All SARs and STRs are retained for 5 years. STR filings are logged in `sar_flags` table.

---

## 6. Sanctions Screening

- All new users are screened against:
  - UN Security Council Consolidated List
  - OFAC SDN List
  - UAE Targeted Financial Sanctions List
  - EU Consolidated List
- Screening is conducted at onboarding and re-run on any adverse media hit or manual trigger
- Matches result in account freeze and MLRO notification
- Ongoing screening: batch re-screen of all users on list updates

---

## 7. Training & Awareness

- All staff with access to user data receive AML/CFT training on joining
- Annual refresher training required
- MLRO receives VARA-accredited AML/CFT training
- Training records retained for 5 years

---

## 8. Record Retention

| Record Type | Retention Period |
|-------------|-----------------|
| KYC documents and CDD records | 5 years after account closure |
| Transaction records | 5 years |
| Internal SARs | 5 years |
| goAML STR filings | 5 years |
| Training records | 5 years |

---

## 9. Policy Review

This policy is reviewed annually by the MLRO and approved by the Board. Material changes require VARA notification.

---

## 10. Regulatory Reporting

In addition to STRs, the Company provides:
- Annual AML/CFT programme report to VARA
- Transaction reports as required by VARA regulations
- Ad-hoc information requests responded to within regulatory deadlines

---

*This document is classified CONFIDENTIAL. Distribution is restricted to authorised staff, Board members, and VARA inspectors.*
