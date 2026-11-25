# Data Dictionary & Anomaly Reference

This document defines the canonical schemas for the processed ERP outputs (`data/processed/erp_master_catalog.json`, `data/processed/erp_master_catalog.csv`, and `data/processed/validation_anomalies.json`) as defined in [`src/models.py`](../src/models.py) and exported by [`src/doc_generator.py`](../src/doc_generator.py), along with a complete reference for all **14** `AnomalyCode` rules enforced in [`src/validator.py`](../src/validator.py).

---

## 1. `erp_master_catalog.json` Top-Level Structure

`erp_master_catalog.json` contains two top-level keys:

| Key | Type | Description |
| :--- | :--- | :--- |
| `metadata` | `object` | Run provenance (`rfp_id`, `rfp_title`, `generated_at_utc`, `source_files`), catalog counts (`total_components`, `approved_components_count`, `quarantined_components_count`), and nested `PipelineMetrics` object (`metrics`). |
| `components` | `list[NormalizedComponent]` | Full ordered list of all ingested components (both approved and quarantined) in canonical SI units with conversion audit traces and validation anomalies. |

### `metadata.metrics` (`PipelineMetrics`)

| Field | Type | Description |
| :--- | :--- | :--- |
| `total_raw_records` | `int` | Total supplier records ingested across CSV and PDF sources. |
| `csv_records` | `int` | Count of records extracted from CSV input. |
| `pdf_records` | `int` | Count of records extracted from PDF spec sheet input. |
| `valid_count` | `int` | Components with `validation_status == "VALID"`. |
| `valid_with_warnings_count` | `int` | Components with `validation_status == "VALID_WITH_WARNINGS"`. |
| `quarantined_count` | `int` | Components with `validation_status == "QUARANTINED"`. |
| `total_anomalies` | `int` | Total `ValidationAnomaly` instances flagged across all components. |
| `total_requirements` | `int` | Count of RFP requirements parsed and evaluated. |
| `compliant_count` | `int` | Requirements whose `overall_status` is `COMPLIANT`. |
| `partial_count` | `int` | Requirements whose `overall_status` is `PARTIAL_COMPLIANCE`. |
| `non_compliant_count` | `int` | Requirements whose `overall_status` is `NON_COMPLIANT`. |
| `compliance_rate_pct` | `float` | Percentage of requirements achieving `COMPLIANT` (`round(100.0 * compliant_count / total_requirements, 1)`). |
| `execution_time_seconds` | `float` | Wall-clock pipeline runtime in seconds (`time.perf_counter()`). |

---

## 2. `NormalizedComponent` Schema

Each element in `components[]` conforms to the Pydantic v2 `NormalizedComponent` model:

| Field | Type | Nullable | Description |
| :--- | :--- | :---: | :--- |
| `part_number` | `string` | No | Trimmed, uppercased supplier part number (e.g., `"TI64-BOLT-M8"`). |
| `supplier_name` | `string` | No | Trimmed supplier organization name. |
| `source_file` | `string` | No | Filename of the originating raw catalog (e.g., `"supplier_catalog_dirty.csv"`). |
| `source_type` | `"csv" \| "pdf"` | No | Ingestion channel type. |
| `source_location` | `string` | No | Exact source pointer: `"row:<n>"` for CSV or `"page:<p>:block:<b>"` for PDF. |
| `category` | `ComponentCategory` | No | Canonical enum: `FASTENER`, `VALVE`, `ALLOY`, `SEAL`, `FITTING`, `ACTUATOR`, `SENSOR`, or `UNKNOWN`. |
| `category_raw` | `string` | No | Original raw category label prior to EN/FR normalization. |
| `description_raw` | `string` | No | Original unstandardized description string. |
| `description_en` | `string` | No | Standardized English engineering description (translated from French or extracted from bilingual `" / "` pairs when needed). |
| `language_detected` | `"en" \| "fr" \| "bilingual"` | No | Detected source language of the component description. |
| `material_canonical` | `string \| null` | Yes | Canonical alloy/polymer designation (e.g., `"Ti-6Al-4V"`, `"17-4PH Stainless Steel"`, `"Fluorosilicone (FVMQ)"`). |
| `material_raw` | `string \| null` | Yes | Original trimmed material string prior to canonical mapping. |
| `nominal_dim_mm` | `float \| null` | Yes | Normalized nominal dimension in SI millimeters (`mm`). |
| `tolerance_mm` | `float \| null` | Yes | Normalized bilateral dimensional tolerance magnitude in SI millimeters (`mm`). |
| `max_pressure_mpa` | `float \| null` | Yes | Normalized maximum pressure rating in SI megapascals (`MPa`). |
| `temp_min_c` | `float \| null` | Yes | Normalized minimum operating temperature in degrees Celsius (`°C`). |
| `temp_max_c` | `float \| null` | Yes | Normalized maximum operating temperature in degrees Celsius (`°C`). |
| `mass_kg` | `float \| null` | Yes | Normalized component mass in SI kilograms (`kg`). |
| `standards` | `list[string]` | No | Deduplicated list of normalized certification/standard tokens (e.g., `["AS9100D", "AMS 4928", "NASM21250"]`). |
| `unit_price_usd` | `float \| null` | Yes | Parsed unit price in USD. |
| `lead_time_days` | `int \| null` | Yes | Normalized procurement lead time in integer days (converted from days/jours, weeks/semaines, or months/mois). |
| `conversion_traces` | `list[UnitConversionTrace]` | No | Ordered audit trail of every unit conversion performed on this record. |
| `anomalies` | `list[ValidationAnomaly]` | No | List of engineering or parsing anomalies flagged on this record. |
| `validation_status` | `"VALID" \| "VALID_WITH_WARNINGS" \| "QUARANTINED"` | No | Final governance gate status assigned by `validate_catalog()`. |

---

## 3. `UnitConversionTrace` Schema

Each entry in `NormalizedComponent.conversion_traces[]` records an immutable conversion audit step:

| Field | Type | Nullable | Description |
| :--- | :--- | :---: | :--- |
| `field` | `string` | No | Target logical field (`"nominal_dim"`, `"tolerance"`, `"max_pressure"`, `"temp_min"`, `"temp_max"`, or `"mass"`). |
| `raw_value` | `string` | No | Exact raw substring parsed (e.g., `"1/4\""`, `"±0.001 in"`, `"-65 °F"`, `"0.65 oz"`). |
| `original_value` | `float` | No | Parsed numeric value in the source unit (e.g., `0.25`, `-65.0`). |
| `original_unit` | `string` | No | Normalized source unit token (e.g., `"in"`, `"psi"`, `"bar"`, `"°F"`, `"K"`, `"oz"`, `"lb"`, `"g"`). |
| `si_value` | `float` | No | Exact converted SI value rounded to 9 decimal places (`_clean_round`). |
| `si_unit` | `string` | No | Target canonical SI unit (`"mm"`, `"MPa"`, `"°C"`, or `"kg"`). |
| `conversion_factor_note` | `string` | No | Human-readable formula or NIST/ISO constant note (e.g., `"1 in = 25.4 mm"`, `"°C = (°F - 32) * 5/9"`). |

---

## 4. `ValidationAnomaly` Schema

Each entry in `NormalizedComponent.anomalies[]` and `validation_anomalies.json` conforms to `ValidationAnomaly`:

| Field | Type | Nullable | Description |
| :--- | :--- | :---: | :--- |
| `code` | `AnomalyCode` | No | Machine-readable enum identifier (one of the 14 codes below). |
| `severity` | `AnomalySeverity` | No | `"ERROR"`, `"WARNING"`, or `"INFO"`. Any `ERROR` forces `validation_status = "QUARANTINED"`. |
| `field` | `string` | No | Field or domain key associated with the anomaly (e.g., `"nominal_dim_mm"`, `"tolerance_mm"`, `"operating_temp"`, `"standards"`). |
| `raw_value` | `string \| null` | Yes | Offending raw or converted value triggering the check, when applicable. |
| `message` | `string` | No | Actionable engineering explanation detailing the rule violation and observed values. |

---

## 5. `erp_master_catalog.csv` Column Reference

The flat ERP export (`data/processed/erp_master_catalog.csv`) serializes all 56 components across **19** ordered columns (`_ERP_CSV_COLUMNS` in `src/doc_generator.py`):

| # | Column Name | Source Field / Formatting |
| :---: | :--- | :--- |
| 1 | `part_number` | `NormalizedComponent.part_number` |
| 2 | `supplier_name` | `NormalizedComponent.supplier_name` |
| 3 | `category` | `NormalizedComponent.category.value` |
| 4 | `description_en` | `NormalizedComponent.description_en` |
| 5 | `language_detected` | `NormalizedComponent.language_detected` |
| 6 | `material_canonical` | `NormalizedComponent.material_canonical` (or `""` if `None`) |
| 7 | `nominal_dim_mm` | `NormalizedComponent.nominal_dim_mm` (or `""` if `None`) |
| 8 | `tolerance_mm` | `NormalizedComponent.tolerance_mm` (or `""` if `None`) |
| 9 | `max_pressure_mpa` | `NormalizedComponent.max_pressure_mpa` (or `""` if `None`) |
| 10 | `temp_min_c` | `NormalizedComponent.temp_min_c` (or `""` if `None`) |
| 11 | `temp_max_c` | `NormalizedComponent.temp_max_c` (or `""` if `None`) |
| 12 | `mass_kg` | `NormalizedComponent.mass_kg` (or `""` if `None`) |
| 13 | `standards` | Semicolon-joined list (`"; ".join(comp.standards)`) |
| 14 | `unit_price_usd` | `NormalizedComponent.unit_price_usd` (or `""` if `None`) |
| 15 | `lead_time_days` | `NormalizedComponent.lead_time_days` (or `""` if `None`) |
| 16 | `validation_status` | `"VALID"`, `"VALID_WITH_WARNINGS"`, or `"QUARANTINED"` |
| 17 | `anomaly_codes` | Semicolon-joined `AnomalyCode` values (`"; ".join(a.code.value ...)`) |
| 18 | `source_type` | `"csv"` or `"pdf"` |
| 19 | `source_location` | `"row:<n>"` or `"page:<p>:block:<b>"` |

---

## 6. `validation_anomalies.json` Structure

`data/processed/validation_anomalies.json` aggregates audit statistics for rapid QA triage:

- **`summary`**: `rfp_id`, `generated_at_utc`, `total_components`, `valid_count`, `valid_with_warnings_count`, `quarantined_count`, `total_anomalies`, `flagged_records_count`, `anomaly_counts_by_severity`, `anomaly_counts_by_code`.
- **`records[]`**: Every component with `validation_status` in `("QUARANTINED", "VALID_WITH_WARNINGS")` or non-empty `anomalies`, containing `part_number`, `supplier_name`, `category`, `validation_status`, `source_file`, `source_type`, `source_location`, and `anomalies[]`.

---

## 7. Complete `AnomalyCode` Reference (All 14 Codes)

| # | `AnomalyCode` | Severity | Trigger Condition | Operational Impact |
| :---: | :--- | :---: | :--- | :--- |
| 1 | `MISSING_DIMENSION` | `ERROR` or `WARNING` | `nominal_dim_mm is None` (when not already `UNPARSEABLE_UNIT`). `ERROR` for `FASTENER`, `ALLOY`, `FITTING`, `SEAL`; `WARNING` for `VALVE`, `ACTUATOR`, `SENSOR`, `UNKNOWN`. | Quarantines structural/dimensional parts (`ERROR`) or flags fluid/electromechanical items (`WARNING`) for dimensional verification prior to PO. |
| 2 | `MISSING_MATERIAL` | `WARNING` | `material_canonical is None` (and not `UNPARSEABLE_UNIT`). | Component remains eligible as `VALID_WITH_WARNINGS` but fails material-constrained RFP criteria and emits a catalog warning note. |
| 3 | `MISSING_TEMP_RANGE` | `WARNING` | `temp_min_c is None` or `temp_max_c is None` (and `operating_temp` not `UNPARSEABLE_UNIT`). | Component remains eligible as `VALID_WITH_WARNINGS` but fails thermal envelope checks and requires engineering waiver verification. |
| 4 | `MISSING_PRESSURE_FOR_FLUID_PART` | `ERROR` or `WARNING` | `max_pressure_mpa is None` (and not `UNPARSEABLE_UNIT`). `ERROR` for `VALVE`; `WARNING` for `FITTING` and `SEAL`. | Quarantines unrated valves (`ERROR`) to prevent pressurized system failure; flags unrated fittings/seals (`WARNING`). |
| 5 | `MISSING_CERTIFICATION` | `ERROR` | `len(standards) == 0` (including records whose raw standard was `"Non certifié"`, `"TBD"`, `"N/A"`, etc.). | Quarantines component; uncertified hardware cannot be proposed on aerospace/industrial RFPs. |
| 6 | `NEGATIVE_OR_ZERO_DIMENSION` | `ERROR` | `nominal_dim_mm <= 0` (e.g., corrupted CAD import `-5.0 mm`). | Quarantines component; prevents physically impossible geometry from entering ERP master data. |
| 7 | `NEGATIVE_PRESSURE` | `ERROR` | `max_pressure_mpa <= 0` (e.g., `-15 bar`). | Quarantines component; rejects corrupted fluid pressure ratings prior to compliance scoring. |
| 8 | `INVERTED_TEMP_RANGE` | `ERROR` | `temp_min_c >= temp_max_c` (both non-null). | Quarantines component; flags swapped or mis-entered thermal limits (e.g., `200 °C to -50 °C`). |
| 9 | `IMPLAUSIBLE_TEMP_BELOW_ABS_ZERO` | `ERROR` | `temp_min_c < -273.15` or `temp_max_c < -273.15` (0 K physical lower bound). | Quarantines component; catches physically impossible cryogenic/sensor transcription errors (e.g., `CRYO-SNS-999`). |
| 10 | `TOLERANCE_OUT_OF_SPEC` | `ERROR` | `tolerance_mm < 0`, OR `tolerance_mm > CATEGORY_MAX_TOLERANCE_MM[category]` (`0.15 mm` for `FASTENER`; `0.25 mm` for `VALVE`/`FITTING`/`SEAL`/`ACTUATOR`/`SENSOR`; `0.50 mm` for `ALLOY`). | Quarantines component; blocks loose or negative tolerances from aerospace structural/fluid assemblies. |
| 11 | `UNPARSEABLE_UNIT` | `ERROR` | `UnitParseError` raised during parsing of `nominal_dim_raw`, `tolerance_raw`, `max_pressure_raw`, `operating_temp_raw`, `mass_raw`, `unit_price_usd`, or `lead_time_days`. | Quarantines component; prevents silent data loss or misinterpretation of malformed units/numbers (e.g., `"approx"`, `"TBD psi"`). |
| 12 | `DUPLICATE_PART_NUMBER` | `ERROR` | Normalized `part_number.strip().upper()` already seen in `seen_part_numbers`. | Quarantines duplicate occurrence while preserving the first occurrence and logging exact original `source_file:source_location`. |
| 13 | `UNKNOWN_CATEGORY` | `ERROR` | `category == ComponentCategory.UNKNOWN` after EN/FR rule matching. | Quarantines component; ensures unclassified items are triaged before ERP taxonomy import or RFP category matching. |
| 14 | `UNVERIFIED_QUALITY_STANDARD` | `WARNING` | `standards` is non-empty, but no token matches `RECOGNIZED_STANDARD_PREFIXES` (`AS9100`, `EN 9100`, `EN9100`, `ISO`, `AMS`, `NAS`, `MS`, `AS`, `NADCAP`, `MIL`, `DIN`, `ASTM`, `DO-160`, `SAE`, `ARP`). | Flags component as `VALID_WITH_WARNINGS` so QA/procurement verifies unrecognized supplier standards prior to PO issuance. |
