"""Core Pydantic v2 data models and domain enums for the technical RFP pipeline."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class ComponentCategory(str, Enum):
    """Canonical aerospace and industrial component categories."""

    FASTENER = "FASTENER"
    VALVE = "VALVE"
    ALLOY = "ALLOY"
    SEAL = "SEAL"
    FITTING = "FITTING"
    ACTUATOR = "ACTUATOR"
    SENSOR = "SENSOR"
    UNKNOWN = "UNKNOWN"


class AnomalySeverity(str, Enum):
    """Severity level assigned to a detected catalog data anomaly."""

    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class AnomalyCode(str, Enum):
    """Machine-readable codes for engineering catalog validation anomalies."""

    MISSING_DIMENSION = "MISSING_DIMENSION"
    MISSING_MATERIAL = "MISSING_MATERIAL"
    MISSING_TEMP_RANGE = "MISSING_TEMP_RANGE"
    MISSING_PRESSURE_FOR_FLUID_PART = "MISSING_PRESSURE_FOR_FLUID_PART"
    MISSING_CERTIFICATION = "MISSING_CERTIFICATION"
    NEGATIVE_OR_ZERO_DIMENSION = "NEGATIVE_OR_ZERO_DIMENSION"
    NEGATIVE_PRESSURE = "NEGATIVE_PRESSURE"
    INVERTED_TEMP_RANGE = "INVERTED_TEMP_RANGE"
    IMPLAUSIBLE_TEMP_BELOW_ABS_ZERO = "IMPLAUSIBLE_TEMP_BELOW_ABS_ZERO"
    TOLERANCE_OUT_OF_SPEC = "TOLERANCE_OUT_OF_SPEC"
    UNPARSEABLE_UNIT = "UNPARSEABLE_UNIT"
    DUPLICATE_PART_NUMBER = "DUPLICATE_PART_NUMBER"
    UNKNOWN_CATEGORY = "UNKNOWN_CATEGORY"
    UNVERIFIED_QUALITY_STANDARD = "UNVERIFIED_QUALITY_STANDARD"


class ValidationAnomaly(BaseModel):
    """Individual anomaly flagged during normalization or engineering validation."""

    code: AnomalyCode
    severity: AnomalySeverity
    field: str
    raw_value: str | None = None
    message: str


class UnitConversionTrace(BaseModel):
    """Audit trail entry documenting a raw-to-SI unit conversion."""

    field: str
    raw_value: str
    original_value: float
    original_unit: str
    si_value: float
    si_unit: str
    conversion_factor_note: str


class RawSupplierRecord(BaseModel):
    """Unparsed supplier catalog record extracted from CSV or PDF sources."""

    source_file: str
    source_type: Literal["csv", "pdf"]
    source_location: str
    part_number: str = ""
    supplier_name: str = ""
    category_raw: str = ""
    description: str = ""
    material_spec: str = ""
    nominal_dim_raw: str = ""
    tolerance_raw: str = ""
    max_pressure_raw: str = ""
    operating_temp_raw: str = ""
    mass_raw: str = ""
    standards_raw: str = ""
    unit_price_usd: str = ""
    lead_time_days: str = ""


class NormalizedComponent(BaseModel):
    """Normalized component record in canonical SI units with audit traces."""

    part_number: str
    supplier_name: str
    source_file: str
    source_type: Literal["csv", "pdf"]
    source_location: str
    category: ComponentCategory
    category_raw: str
    description_raw: str
    description_en: str
    language_detected: Literal["en", "fr", "bilingual"]
    material_canonical: str | None = None
    material_raw: str | None = None
    nominal_dim_mm: float | None = None
    tolerance_mm: float | None = None
    max_pressure_mpa: float | None = None
    temp_min_c: float | None = None
    temp_max_c: float | None = None
    mass_kg: float | None = None
    standards: list[str] = Field(default_factory=list)
    unit_price_usd: float | None = None
    lead_time_days: int | None = None
    conversion_traces: list[UnitConversionTrace] = Field(default_factory=list)
    anomalies: list[ValidationAnomaly] = Field(default_factory=list)
    validation_status: Literal["VALID", "VALID_WITH_WARNINGS", "QUARANTINED"] = "VALID"


class RFPRequirement(BaseModel):
    """Structured technical requirement parsed from an RFP Markdown specification."""

    req_id: str
    title: str
    language: Literal["en", "fr", "bilingual"]
    category: ComponentCategory
    required_materials: list[str] = Field(default_factory=list)
    dim_min_mm: float | None = None
    dim_max_mm: float | None = None
    max_allowed_tolerance_mm: float | None = None
    min_pressure_mpa: float | None = None
    required_temp_min_c: float | None = None
    required_temp_max_c: float | None = None
    required_standard_groups: list[list[str]] = Field(default_factory=list)
    raw_text: str


class ComplianceStatus(str, Enum):
    """Compliance classification for a requirement or candidate component."""

    COMPLIANT = "COMPLIANT"
    PARTIAL_COMPLIANCE = "PARTIAL_COMPLIANCE"
    NON_COMPLIANT = "NON_COMPLIANT"


class CriterionEvaluation(BaseModel):
    """Evaluation outcome for a single technical criterion against an RFP limit."""

    criterion: str
    required: str
    actual: str
    passed: bool
    margin_note: str


class CandidateMatch(BaseModel):
    """Scored candidate component evaluated against a single RFP requirement."""

    part_number: str
    supplier_name: str
    source_type: Literal["csv", "pdf"]
    validation_status: str
    compliance_status: ComplianceStatus
    compliance_score: float
    criteria_checks: list[CriterionEvaluation] = Field(default_factory=list)
    discrepancies: list[str] = Field(default_factory=list)
    waiver_notes: list[str] = Field(default_factory=list)
    unit_price_usd: float | None = None
    lead_time_days: int | None = None


class RequirementComplianceResult(BaseModel):
    """Aggregated compliance assessment and recommendation for one RFP requirement."""

    requirement: RFPRequirement
    overall_status: ComplianceStatus
    best_match: CandidateMatch | None = None
    alternative_matches: list[CandidateMatch] = Field(default_factory=list)
    evaluated_candidates_count: int
    quarantined_excluded_count: int
    recommendation: str


class PipelineMetrics(BaseModel):
    """Aggregate execution, quality, and compliance metrics for a pipeline run."""

    total_raw_records: int
    csv_records: int
    pdf_records: int
    valid_count: int
    valid_with_warnings_count: int
    quarantined_count: int
    total_anomalies: int
    total_requirements: int
    compliant_count: int
    partial_count: int
    non_compliant_count: int
    compliance_rate_pct: float
    execution_time_seconds: float


class PipelineReport(BaseModel):
    """Complete serializable output report produced by the RFP compliance pipeline."""

    rfp_id: str
    rfp_title: str
    generated_at_utc: str
    source_files: list[str]
    metrics: PipelineMetrics
    components: list[NormalizedComponent]
    compliance_results: list[RequirementComplianceResult]
