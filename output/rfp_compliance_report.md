# Technical RFP Compliance Report — RFP-AERO-2026-042

**RFP Title:** Next-Generation Wing & Hydraulic Subassembly Procurement / Approvisionnement sous-ensembles voilure et hydraulique  
**Generated (UTC):** 2026-11-25T03:27:35Z  
**Source Files:** supplier_catalog_dirty.csv, supplier_spec_sheet_dirty.pdf, rfp_requirements_sample.md

---

## 1. Executive KPI Summary

| Metric | Value |
| :--- | ---: |
| Total Raw Records Ingested | 56 |
| CSV Records Ingested | 50 |
| PDF Records Ingested | 6 |
| Valid Components (`VALID`) | 41 |
| Valid with Warnings (`VALID_WITH_WARNINGS`) | 2 |
| Quarantined Components (`QUARANTINED`) | 13 |
| Total Validation Anomalies Detected | 16 |
| Total RFP Requirements Evaluated | 10 |
| Compliant Requirements (`COMPLIANT`) | 7 |
| Partial Compliance (`PARTIAL_COMPLIANCE`) | 2 |
| Non-Compliant (`NON_COMPLIANT`) | 1 |
| Overall Compliance Rate | 70.0% |
| Pipeline Execution Time | 0.022 s |

---

## 2. Master Compliance Matrix

| REQ-ID | Title | Category | Status | Recommended P/N | Supplier | Score | Unit Price | Lead Time |
| :--- | :--- | :--- | :--- | :--- | :--- | ---: | ---: | ---: |
| REQ-001 | Primary Wing-Spar Titanium Hex Bolts | FASTENER | **COMPLIANT** | TI64-BOLT-M8 | AeroFix Precision SA | 100.0% | $18.40 | 14 d |
| REQ-002 | Vanne de régulation hydraulique haute pression | VALVE | **COMPLIANT** | VLV-REL-5000 | Valcor Flight Systems | 100.0% | $760.00 | 21 d |
| REQ-003 | High-Strength Nickel Superalloy Turbine Bar Stock | ALLOY | **COMPLIANT** | INC718-BAR-25 | Aubert & Duval Alloys | 100.0% | $420.00 | 21 d |
| REQ-004 | Joint torique fluorosilicone pour circuit carburant | SEAL | **COMPLIANT** | SEAL-FVMQ-028 | Joints Aéronautiques SA | 100.0% | $14.50 | 10 d |
| REQ-005 | Titanium Hydraulic Bulkhead Fitting | FITTING | **COMPLIANT** | FIT-TI-012 | Raccords Aviation Nice | 100.0% | $132.00 | 18 d |
| REQ-006 | Capteur de pression différentielle avionique | SENSOR | **COMPLIANT** | SNS-PRS-250 | Avionics SenseTech | 100.0% | $590.00 | 21 d |
| REQ-007 | Electro-Hydraulic Flight Control Actuator | ACTUATOR | **COMPLIANT** | ACT-ELH-710 | Systèmes Vol Toulouse | 100.0% | $2450.00 | 35 d |
| REQ-008 | Écrou autofreiné haute température pour train d'atterrissage | FASTENER | **PARTIAL_COMPLIANCE** | A286-NUT-M14 | AéroVisserie Toulouse | 87.5% | $16.80 | 21 d |
| REQ-009 | Ultra-High-Pressure Bleed-Air Isolation Valve | VALVE | **NON_COMPLIANT** | VLV-BLEED-320 | Turbine Hardware Corp | 55.6% | $1950.00 | 42 d |
| REQ-010 | Tôle épaisse en alliage d'aluminium haute résistance | ALLOY | **PARTIAL_COMPLIANCE** | AL7075-PLT-16 | Constellium Aero | 87.5% | $185.00 | 12 d |

---

## 3. Detailed Requirement-by-Requirement Verification

### REQ-001: Primary Wing-Spar Titanium Hex Bolts

- **Category:** `FASTENER` | **Language:** `en` | **Overall Status:** **COMPLIANT**
- **Candidates Evaluated:** 10 | **Quarantined Excluded:** 4
- **Engineering Recommendation:** RECOMMEND TI64-BOLT-M8 (AeroFix Precision SA) — 100.0% compliant [$18.40, 14d lead] (4 quarantined catalog item(s) excluded). Alternatives: TI64-BOLT-M10, TI64-PIN-06.

**Top Ranked Candidate:** `TI64-BOLT-M8` — *AeroFix Precision SA* (`csv`, `VALID`, Score: **100.0%**)

| Criterion | Required | Actual | Passed | Margin / Verification Note |
| :--- | :--- | :--- | :---: | :--- |
| Material | Ti-6Al-4V | Ti-6Al-4V | PASS | Compatible material match |
| Nominal Dimension | 8.00 to 12.00 mm | 8.00 mm | PASS | Within range (+0.00 mm above min, +4.00 mm below max) |
| Max Tolerance | <= ±0.050 mm | ±0.025 mm | PASS | +0.025 mm tolerance margin |
| Min Operating Temp | <= -55.0 °C | -60.0 °C | PASS | +5.0 °C cold-end margin |
| Max Operating Temp | >= 180.0 °C | 220.0 °C | PASS | +40.0 °C hot-end margin |
| Standards Group 1 | AS9100D OR EN 9100 | AS9100D, AMS 4928, NASM21250 | PASS | Satisfied (AS9100D, EN 9100) |
| Standards Group 2 | AMS 4928 OR NASM21250 | AS9100D, AMS 4928, NASM21250 | PASS | Satisfied (AMS 4928, NASM21250) |



**Alternative Candidates:**
- `TI64-BOLT-M10` (Safran Fixations Lyon) — COMPLIANT (100.0%, $22.90, 14 d lead)
- `TI64-PIN-06` (AeroFix Precision SA) — PARTIAL_COMPLIANCE (85.7%, $12.10, 12 d lead)

---

### REQ-002: Vanne de régulation hydraulique haute pression

- **Category:** `VALVE` | **Language:** `fr` | **Overall Status:** **COMPLIANT**
- **Candidates Evaluated:** 9 | **Quarantined Excluded:** 4
- **Engineering Recommendation:** RECOMMEND VLV-REL-5000 (Valcor Flight Systems) — 100.0% compliant [$760.00, 21d lead] (4 quarantined catalog item(s) excluded). Alternatives: VLV-174PH-25, VLV-FR-3000.

**Top Ranked Candidate:** `VLV-REL-5000` — *Valcor Flight Systems* (`csv`, `VALID`, Score: **100.0%**)

| Criterion | Required | Actual | Passed | Margin / Verification Note |
| :--- | :--- | :--- | :---: | :--- |
| Material | 17-4PH OR Inconel 718 OR 316L | 17-4PH Stainless Steel | PASS | Compatible material match |
| Nominal Dimension | 12.70 to 38.10 mm | 19.05 mm | PASS | Within range (+6.35 mm above min, +19.05 mm below max) |
| Max Tolerance | <= ±0.080 mm | ±0.035 mm | PASS | +0.045 mm tolerance margin |
| Min Pressure | >= 20.68 MPa | 34.47 MPa | PASS | +13.79 MPa (+66.7% margin) |
| Min Operating Temp | <= -53.9 °C | -53.9 °C | PASS | +0.0 °C cold-end margin |
| Max Operating Temp | >= 135.0 °C | 135.0 °C | PASS | +0.0 °C hot-end margin |
| Standards Group 1 | AS9100D OR EN 9100 | AS9100D, MIL-PRF-5523, ISO 9001 | PASS | Satisfied (AS9100D, EN 9100) |
| Standards Group 2 | ISO 9001 | AS9100D, MIL-PRF-5523, ISO 9001 | PASS | Satisfied (ISO 9001) |



**Alternative Candidates:**
- `VLV-174PH-25` (HydraFlow Aerospace) — COMPLIANT (100.0%, $890.00, 28 d lead)
- `VLV-FR-3000` (MécaFluide Bordeaux) — COMPLIANT (100.0%, $945.00, 28 d lead)

---

### REQ-003: High-Strength Nickel Superalloy Turbine Bar Stock

- **Category:** `ALLOY` | **Language:** `en` | **Overall Status:** **COMPLIANT**
- **Candidates Evaluated:** 9 | **Quarantined Excluded:** 1
- **Engineering Recommendation:** RECOMMEND INC718-BAR-25 (Aubert & Duval Alloys) — 100.0% compliant [$420.00, 21d lead] (1 quarantined catalog item(s) excluded). Alternatives: INC718-BAR-40, SS174PH-ROD-22.

**Top Ranked Candidate:** `INC718-BAR-25` — *Aubert & Duval Alloys* (`csv`, `VALID`, Score: **100.0%**)

| Criterion | Required | Actual | Passed | Margin / Verification Note |
| :--- | :--- | :--- | :---: | :--- |
| Material | Inconel 718 | Inconel 718 | PASS | Compatible material match |
| Nominal Dimension | 20.00 to 55.00 mm | 25.40 mm | PASS | Within range (+5.40 mm above min, +29.60 mm below max) |
| Max Tolerance | <= ±0.100 mm | ±0.050 mm | PASS | +0.050 mm tolerance margin |
| Min Operating Temp | <= -50.0 °C | -100.0 °C | PASS | +50.0 °C cold-end margin |
| Max Operating Temp | >= 650.0 °C | 700.0 °C | PASS | +50.0 °C hot-end margin |
| Standards Group 1 | AS9100D OR EN 9100 | AS9100D, AMS 5662, NADCAP | PASS | Satisfied (AS9100D, EN 9100) |
| Standards Group 2 | AMS 5662 OR AMS 5663 | AS9100D, AMS 5662, NADCAP | PASS | Satisfied (AMS 5662) |



**Alternative Candidates:**
- `INC718-BAR-40` (Special Metals Aerospace) — COMPLIANT (100.0%, $615.00, 21 d lead)
- `SS174PH-ROD-22` (Aubert & Duval Alloys) — NON_COMPLIANT (57.1%, $162.00, 14 d lead)

---

### REQ-004: Joint torique fluorosilicone pour circuit carburant

- **Category:** `SEAL` | **Language:** `fr` | **Overall Status:** **COMPLIANT**
- **Candidates Evaluated:** 7 | **Quarantined Excluded:** 1
- **Engineering Recommendation:** RECOMMEND SEAL-FVMQ-028 (Joints Aéronautiques SA) — 100.0% compliant [$14.50, 10d lead] (1 quarantined catalog item(s) excluded). Alternatives: SEAL-FKM-035, SEAL-EPDM-025.

**Top Ranked Candidate:** `SEAL-FVMQ-028` — *Joints Aéronautiques SA* (`csv`, `VALID`, Score: **100.0%**)

| Criterion | Required | Actual | Passed | Margin / Verification Note |
| :--- | :--- | :--- | :---: | :--- |
| Material | Fluorosilicone OR FKM | Fluorosilicone (FVMQ) | PASS | Compatible material match |
| Nominal Dimension | 15.00 to 45.00 mm | 28.00 mm | PASS | Within range (+13.00 mm above min, +17.00 mm below max) |
| Max Tolerance | <= ±0.100 mm | ±0.050 mm | PASS | +0.050 mm tolerance margin |
| Min Pressure | >= 10.34 MPa | 14.50 MPa | PASS | +4.16 MPa (+40.2% margin) |
| Min Operating Temp | <= -55.0 °C | -60.0 °C | PASS | +5.0 °C cold-end margin |
| Max Operating Temp | >= 200.0 °C | 210.0 °C | PASS | +10.0 °C hot-end margin |
| Standards Group 1 | AS9100D OR EN 9100 | AS9100D, AMS-R-25988, AS568 | PASS | Satisfied (AS9100D, EN 9100) |
| Standards Group 2 | AS568 | AS9100D, AMS-R-25988, AS568 | PASS | Satisfied (AS568) |



**Alternative Candidates:**
- `SEAL-FKM-035` (Parker Aerospace Seals) — PARTIAL_COMPLIANCE (87.5%, $11.80, 9 d lead)
- `SEAL-EPDM-025` (Parker Aerospace Seals) — PARTIAL_COMPLIANCE (75.0%, $7.90, 7 d lead)

---

### REQ-005: Titanium Hydraulic Bulkhead Fitting

- **Category:** `FITTING` | **Language:** `en` | **Overall Status:** **COMPLIANT**
- **Candidates Evaluated:** 3 | **Quarantined Excluded:** 1
- **Engineering Recommendation:** RECOMMEND FIT-TI-012 (Raccords Aviation Nice) — 100.0% compliant [$132.00, 18d lead] (1 quarantined catalog item(s) excluded). Alternatives: TI-FIT-038, FIT-AN815-08.

**Top Ranked Candidate:** `FIT-TI-012` — *Raccords Aviation Nice* (`csv`, `VALID`, Score: **100.0%**)

| Criterion | Required | Actual | Passed | Margin / Verification Note |
| :--- | :--- | :--- | :---: | :--- |
| Material | Ti-6Al-4V | Ti-6Al-4V | PASS | Compatible material match |
| Nominal Dimension | 8.00 to 15.00 mm | 12.00 mm | PASS | Within range (+4.00 mm above min, +3.00 mm below max) |
| Max Tolerance | <= ±0.050 mm | ±0.025 mm | PASS | +0.025 mm tolerance margin |
| Min Pressure | >= 34.47 MPa | 35.00 MPa | PASS | +0.53 MPa (+1.5% margin) |
| Min Operating Temp | <= -50.0 °C | -55.0 °C | PASS | +5.0 °C cold-end margin |
| Max Operating Temp | >= 180.0 °C | 205.0 °C | PASS | +25.0 °C hot-end margin |
| Standards Group 1 | AS9100D | EN 9100, AS9100D, SAE AS4395 | PASS | Satisfied (AS9100D) |
| Standards Group 2 | SAE AS4395 | EN 9100, AS9100D, SAE AS4395 | PASS | Satisfied (SAE AS4395) |



**Alternative Candidates:**
- `TI-FIT-038` (Raccords Aviation Nice) — COMPLIANT (100.0%, $148.50, 14 d lead)
- `FIT-AN815-08` (AeroFluid Connectors) — PARTIAL_COMPLIANCE (62.5%, $29.00, 12 d lead)

---

### REQ-006: Capteur de pression différentielle avionique

- **Category:** `SENSOR` | **Language:** `fr` | **Overall Status:** **COMPLIANT**
- **Candidates Evaluated:** 3 | **Quarantined Excluded:** 1
- **Engineering Recommendation:** RECOMMEND SNS-PRS-250 (Avionics SenseTech) — 100.0% compliant [$590.00, 21d lead] (1 quarantined catalog item(s) excluded). Alternatives: DPS-SNS-404, SNS-TEMP-PT100.

**Top Ranked Candidate:** `SNS-PRS-250` — *Avionics SenseTech* (`csv`, `VALID`, Score: **100.0%**)

| Criterion | Required | Actual | Passed | Margin / Verification Note |
| :--- | :--- | :--- | :---: | :--- |
| Material | 316L Stainless Steel OR Inconel 625 | Inconel 625 | PASS | Compatible material match |
| Nominal Dimension | 10.00 to 20.00 mm | 15.00 mm | PASS | Within range (+5.00 mm above min, +5.00 mm below max) |
| Max Tolerance | <= ±0.050 mm | ±0.020 mm | PASS | +0.030 mm tolerance margin |
| Min Pressure | >= 20.68 MPa | 25.00 MPa | PASS | +4.32 MPa (+20.9% margin) |
| Min Operating Temp | <= -50.0 °C | -55.0 °C | PASS | +5.0 °C cold-end margin |
| Max Operating Temp | >= 140.0 °C | 175.0 °C | PASS | +35.0 °C hot-end margin |
| Standards Group 1 | AS9100D | AS9100D, DO-160G, MIL-STD-810 | PASS | Satisfied (AS9100D) |
| Standards Group 2 | DO-160G | AS9100D, DO-160G, MIL-STD-810 | PASS | Satisfied (DO-160G) |



**Alternative Candidates:**
- `DPS-SNS-404` (Avionics SenseTech) — COMPLIANT (100.0%, $680.00, 21 d lead)
- `SNS-TEMP-PT100` (Avionics SenseTech) — PARTIAL_COMPLIANCE (87.5%, $415.00, 21 d lead)

---

### REQ-007: Electro-Hydraulic Flight Control Actuator

- **Category:** `ACTUATOR` | **Language:** `en` | **Overall Status:** **COMPLIANT**
- **Candidates Evaluated:** 2 | **Quarantined Excluded:** 0
- **Engineering Recommendation:** RECOMMEND ACT-ELH-710 (Systèmes Vol Toulouse) — 100.0% compliant [$2450.00, 35d lead]. Alternatives: ACT-ROT-400.

**Top Ranked Candidate:** `ACT-ELH-710` — *Systèmes Vol Toulouse* (`pdf`, `VALID`, Score: **100.0%**)

| Criterion | Required | Actual | Passed | Margin / Verification Note |
| :--- | :--- | :--- | :---: | :--- |
| Material | 17-4PH Stainless Steel | 17-4PH Stainless Steel | PASS | Compatible material match |
| Nominal Dimension | 40.00 to 60.00 mm | 50.00 mm | PASS | Within range (+10.00 mm above min, +10.00 mm below max) |
| Max Tolerance | <= ±0.050 mm | ±0.020 mm | PASS | +0.030 mm tolerance margin |
| Min Pressure | >= 25.00 MPa | 28.00 MPa | PASS | +3.00 MPa (+12.0% margin) |
| Min Operating Temp | <= -50.0 °C | -54.0 °C | PASS | +4.0 °C cold-end margin |
| Max Operating Temp | >= 130.0 °C | 135.0 °C | PASS | +5.0 °C hot-end margin |
| Standards Group 1 | AS9100D | AS9100D, MIL-PRF-5440, NADCAP | PASS | Satisfied (AS9100D) |
| Standards Group 2 | MIL-PRF-5440 | AS9100D, MIL-PRF-5440, NADCAP | PASS | Satisfied (MIL-PRF-5440) |



**Alternative Candidates:**
- `ACT-ROT-400` (Systèmes Vol Toulouse) — PARTIAL_COMPLIANCE (87.5%, $2180.00, 35 d lead)

---

### REQ-008: Écrou autofreiné haute température pour train d'atterrissage

- **Category:** `FASTENER` | **Language:** `fr` | **Overall Status:** **PARTIAL_COMPLIANCE**
- **Candidates Evaluated:** 10 | **Quarantined Excluded:** 4
- **Engineering Recommendation:** CONDITIONAL / WAIVER REVIEW for A286-NUT-M14 (AéroVisserie Toulouse) — 87.5% score [$16.80, 21d lead]. Discrepancies: Max Operating Temp: required >= 450.0 °C, actual 420.0 °C (-30.0 °C shortfall below required max) (4 quarantined catalog item(s) excluded). Alternatives: INC718-STUD-38, TI64-BOLT-M10.

**Top Ranked Candidate:** `A286-NUT-M14` — *AéroVisserie Toulouse* (`csv`, `VALID`, Score: **87.5%**)

| Criterion | Required | Actual | Passed | Margin / Verification Note |
| :--- | :--- | :--- | :---: | :--- |
| Material | A286 OR Inconel 718 | A286 Stainless Steel | PASS | Compatible material match |
| Nominal Dimension | 12.00 to 16.00 mm | 14.00 mm | PASS | Within range (+2.00 mm above min, +2.00 mm below max) |
| Max Tolerance | <= ±0.020 mm | ±0.015 mm | PASS | +0.005 mm tolerance margin |
| Min Operating Temp | <= -65.0 °C | -65.0 °C | PASS | +0.0 °C cold-end margin |
| Max Operating Temp | >= 450.0 °C | 420.0 °C | FAIL | -30.0 °C shortfall below required max |
| Standards Group 1 | AS9100D | AS9100D, NASM25027, NADCAP | PASS | Satisfied (AS9100D) |
| Standards Group 2 | NASM25027 | AS9100D, NASM25027, NADCAP | PASS | Satisfied (NASM25027) |
| Standards Group 3 | NADCAP | AS9100D, NASM25027, NADCAP | PASS | Satisfied (NADCAP) |

**Discrepancies:**
- Max Operating Temp: required >= 450.0 °C, actual 420.0 °C (-30.0 °C shortfall below required max)

**Engineering Waiver & Warning Notes:**
- Thermal waiver candidate: 30.0 °C max-temp shortfall (420.0 °C vs 450.0 °C); assess peak duty-cycle duration or supplementary heat-soak qualification.

**Alternative Candidates:**
- `INC718-STUD-38` (Turbine Hardware Corp) — PARTIAL_COMPLIANCE (62.5%, $34.50, 21 d lead)
- `TI64-BOLT-M10` (Safran Fixations Lyon) — NON_COMPLIANT (37.5%, $22.90, 14 d lead)

---

### REQ-009: Ultra-High-Pressure Bleed-Air Isolation Valve

- **Category:** `VALVE` | **Language:** `en` | **Overall Status:** **NON_COMPLIANT**
- **Candidates Evaluated:** 9 | **Quarantined Excluded:** 4
- **Engineering Recommendation:** NON-COMPLIANT: Best available VLV-BLEED-320 (Turbine Hardware Corp) scored only 55.6%. Critical gaps: Max Tolerance: required <= ±0.030 mm, actual ±0.040 mm (Exceeds limit by 0.010 mm); Min Pressure: required >= 65.00 MPa, actual 32.00 MPa (-33.00 MPa (-50.8% shortfall)); Max Operating Temp: required >= 550.0 °C, actual 320.0 °C (-230.0 °C shortfall below required max) (4 quarantined catalog item(s) excluded). Issue external RFQ / custom engineering qualification.

**Top Ranked Candidate:** `VLV-BLEED-320` — *Turbine Hardware Corp* (`csv`, `VALID`, Score: **55.6%**)

| Criterion | Required | Actual | Passed | Margin / Verification Note |
| :--- | :--- | :--- | :---: | :--- |
| Material | Inconel 718 OR Haynes 230 | Inconel 718 | PASS | Compatible material match |
| Nominal Dimension | 20.00 to 40.00 mm | 30.00 mm | PASS | Within range (+10.00 mm above min, +10.00 mm below max) |
| Max Tolerance | <= ±0.030 mm | ±0.040 mm | FAIL | Exceeds limit by 0.010 mm |
| Min Pressure | >= 65.00 MPa | 32.00 MPa | FAIL | -33.00 MPa (-50.8% shortfall) |
| Min Operating Temp | <= -55.0 °C | -55.0 °C | PASS | +0.0 °C cold-end margin |
| Max Operating Temp | >= 550.0 °C | 320.0 °C | FAIL | -230.0 °C shortfall below required max |
| Standards Group 1 | AS9100D | AS9100D, NADCAP, EN 9100 | PASS | Satisfied (AS9100D) |
| Standards Group 2 | ARP9013 | AS9100D, NADCAP, EN 9100 | FAIL | Missing required standard (ARP9013) |
| Standards Group 3 | NADCAP | AS9100D, NADCAP, EN 9100 | PASS | Satisfied (NADCAP) |

**Discrepancies:**
- Max Tolerance: required <= ±0.030 mm, actual ±0.040 mm (Exceeds limit by 0.010 mm)
- Min Pressure: required >= 65.00 MPa, actual 32.00 MPa (-33.00 MPa (-50.8% shortfall))
- Max Operating Temp: required >= 550.0 °C, actual 320.0 °C (-230.0 °C shortfall below required max)
- Standards Group 2: required ARP9013, actual AS9100D, NADCAP, EN 9100 (Missing required standard (ARP9013))


**Alternative Candidates:**
- `VLV-SOL-12` (MécaFluide Bordeaux) — NON_COMPLIANT (44.4%, $1120.00, 30 d lead)
- `CRYO-VLV-112` (MécaFluide Bordeaux) — NON_COMPLIANT (44.4%, $1240.00, 28 d lead)

---

### REQ-010: Tôle épaisse en alliage d'aluminium haute résistance

- **Category:** `ALLOY` | **Language:** `fr` | **Overall Status:** **PARTIAL_COMPLIANCE**
- **Candidates Evaluated:** 9 | **Quarantined Excluded:** 1
- **Engineering Recommendation:** CONDITIONAL / WAIVER REVIEW for AL7075-PLT-16 (Constellium Aero) — 87.5% score [$185.00, 12d lead]. Discrepancies: Max Tolerance: required <= ±0.050 mm, actual ±0.080 mm (Exceeds limit by 0.030 mm) (1 quarantined catalog item(s) excluded). Alternatives: INC625-TUB-19, INC718-BAR-25.

**Top Ranked Candidate:** `AL7075-PLT-16` — *Constellium Aero* (`csv`, `VALID`, Score: **87.5%**)

| Criterion | Required | Actual | Passed | Margin / Verification Note |
| :--- | :--- | :--- | :---: | :--- |
| Material | 7075-T6 | Aluminum 7075-T6 | PASS | Compatible material match |
| Nominal Dimension | 10.00 to 30.00 mm | 16.00 mm | PASS | Within range (+6.00 mm above min, +14.00 mm below max) |
| Max Tolerance | <= ±0.050 mm | ±0.080 mm | FAIL | Exceeds limit by 0.030 mm |
| Min Operating Temp | <= -60.0 °C | -65.0 °C | PASS | +5.0 °C cold-end margin |
| Max Operating Temp | >= 150.0 °C | 160.0 °C | PASS | +10.0 °C hot-end margin |
| Standards Group 1 | AS9100D | AS9100D, AMS 4045, NADCAP | PASS | Satisfied (AS9100D) |
| Standards Group 2 | AMS 4045 | AS9100D, AMS 4045, NADCAP | PASS | Satisfied (AMS 4045) |
| Standards Group 3 | NADCAP | AS9100D, AMS 4045, NADCAP | PASS | Satisfied (NADCAP) |

**Discrepancies:**
- Max Tolerance: required <= ±0.050 mm, actual ±0.080 mm (Exceeds limit by 0.030 mm)

**Engineering Waiver & Warning Notes:**
- Tolerance waiver candidate: ±0.080 mm vs ±0.050 mm limit (+0.030 mm); candidate for MRB concession or secondary finish machining.

**Alternative Candidates:**
- `INC625-TUB-19` (Special Metals Aerospace) — PARTIAL_COMPLIANCE (75.0%, $375.00, 19 d lead)
- `INC718-BAR-25` (Aubert & Duval Alloys) — PARTIAL_COMPLIANCE (75.0%, $420.00, 21 d lead)

---


## 4. Data Quality & Quarantine Audit

| Part Number | Supplier | Category | Source | Anomaly Codes | Engineering Messages |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TI64-BOLT-M8` | AeroFix Precision SA | FASTENER | csv (row:11) | DUPLICATE_PART_NUMBER | Duplicate part number 'TI64-BOLT-M8'; first seen at supplier_catalog_dirty.csv:row:1 |
| `BAD-FST-TOL1` | LowCost Fasteners Ltd | FASTENER | csv (row:12) | TOLERANCE_OUT_OF_SPEC | Tolerance ±0.65 mm exceeds FASTENER envelope limit of ±0.15 mm |
| `BAD-FST-TOL2` | LowCost Fasteners Ltd | FASTENER | csv (row:13) | TOLERANCE_OUT_OF_SPEC | Tolerance ±2.032 mm exceeds FASTENER envelope limit of ±0.15 mm |
| `BAD-FST-NEG` | AéroVisserie Toulouse | FASTENER | csv (row:14) | NEGATIVE_OR_ZERO_DIMENSION | Nominal dimension must be > 0 mm (got -5.0 mm) |
| `BAD-VLV-NOPRES` | MécaFluide Bordeaux | VALVE | csv (row:23) | MISSING_PRESSURE_FOR_FLUID_PART | Missing max pressure rating for VALVE component |
| `BAD-VLV-NEGPRES` | Valcor Flight Systems | VALVE | csv (row:24) | NEGATIVE_PRESSURE | Max pressure must be > 0 MPa (got -1.5 MPa) |
| `BAD-VLV-UNPARSE` | LowCost Fasteners Ltd | VALVE | csv (row:25) | UNPARSEABLE_UNIT | Unparseable pressure 'high pressure': Unparseable pressure value: 'high pressure' |
| `BAD-VLV-INVTEMP` | HydraFlow Aerospace | VALVE | csv (row:26) | INVERTED_TEMP_RANGE | Inverted temperature range: min 200.0 °C >= max 50.0 °C |
| `BAD-ALY-UNCERT` | EuroFasten GmbH | ALLOY | csv (row:36) | MISSING_CERTIFICATION | Missing quality or aerospace certification standards |
| `BAD-SL-NOCERT` | LowCost Fasteners Ltd | SEAL | csv (row:43) | MISSING_CERTIFICATION | Missing quality or aerospace certification standards |
| `BAD-FIT-NODIM` | AeroFluid Connectors | FITTING | csv (row:49) | MISSING_DIMENSION | Missing nominal dimension for FITTING component |
| `BAD-UNK-001` | LowCost Fasteners Ltd | UNKNOWN | csv (row:50) | UNPARSEABLE_UNIT, UNKNOWN_CATEGORY | Unparseable nominal dimension 'approx half inch?': Unparseable length value: 'approx half inch?' ; Unrecognized component category: 'Unclassified Hardware' |
| `CRYO-SNS-999` | Avionics SenseTech | SENSOR | pdf (page:3:block:6) | IMPLAUSIBLE_TEMP_BELOW_ABS_ZERO | Operating temperature below absolute zero (-273.15 °C): [-300.0, 120.0] °C |
