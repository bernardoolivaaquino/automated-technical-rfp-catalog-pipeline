"""Deterministic engineering validation and anomaly detection for normalized components."""

from __future__ import annotations

from src.models import (
    AnomalyCode,
    AnomalySeverity,
    ComponentCategory,
    NormalizedComponent,
    ValidationAnomaly,
)

CATEGORY_MAX_TOLERANCE_MM: dict[ComponentCategory, float] = {
    ComponentCategory.FASTENER: 0.15,
    ComponentCategory.VALVE: 0.25,
    ComponentCategory.FITTING: 0.25,
    ComponentCategory.SEAL: 0.25,
    ComponentCategory.ACTUATOR: 0.25,
    ComponentCategory.SENSOR: 0.25,
    ComponentCategory.ALLOY: 0.50,
}

RECOGNIZED_STANDARD_PREFIXES: tuple[str, ...] = (
    "AS9100",
    "EN 9100",
    "EN9100",
    "ISO",
    "AMS",
    "NAS",
    "MS",
    "AS",
    "NADCAP",
    "MIL",
    "DIN",
    "ASTM",
    "DO-160",
    "SAE",
    "ARP",
)

_DIM_ERROR_CATEGORIES: frozenset[ComponentCategory] = frozenset(
    {
        ComponentCategory.FASTENER,
        ComponentCategory.ALLOY,
        ComponentCategory.FITTING,
        ComponentCategory.SEAL,
    }
)

_PRESSURE_WARNING_CATEGORIES: frozenset[ComponentCategory] = frozenset(
    {
        ComponentCategory.FITTING,
        ComponentCategory.SEAL,
    }
)


def _is_recognized_standard(standard: str) -> bool:
    upper = standard.strip().upper()
    return any(upper.startswith(prefix.upper()) for prefix in RECOGNIZED_STANDARD_PREFIXES)


def validate_catalog(components: list[NormalizedComponent]) -> list[NormalizedComponent]:
    """Validate physical plausibility, tolerances, duplicates, and completeness for components."""
    validated: list[NormalizedComponent] = []
    seen_part_numbers: dict[str, str] = {}

    for raw_comp in components:
        comp = raw_comp.model_copy(deep=True)
        anomalies = list(comp.anomalies)
        unparseable_fields = {
            a.field for a in anomalies if a.code == AnomalyCode.UNPARSEABLE_UNIT
        }

        # 1. Duplicate part_number check (case-insensitive, trimmed)
        pn_key = comp.part_number.strip().upper()
        if pn_key:
            if pn_key in seen_part_numbers:
                anomalies.append(
                    ValidationAnomaly(
                        code=AnomalyCode.DUPLICATE_PART_NUMBER,
                        severity=AnomalySeverity.ERROR,
                        field="part_number",
                        raw_value=comp.part_number,
                        message=(
                            f"Duplicate part number {pn_key!r}; first seen at "
                            f"{seen_part_numbers[pn_key]}"
                        ),
                    )
                )
            else:
                seen_part_numbers[pn_key] = f"{comp.source_file}:{comp.source_location}"

        # 2. Physical plausibility checks
        if comp.nominal_dim_mm is not None and comp.nominal_dim_mm <= 0:
            anomalies.append(
                ValidationAnomaly(
                    code=AnomalyCode.NEGATIVE_OR_ZERO_DIMENSION,
                    severity=AnomalySeverity.ERROR,
                    field="nominal_dim_mm",
                    raw_value=str(comp.nominal_dim_mm),
                    message=f"Nominal dimension must be > 0 mm (got {comp.nominal_dim_mm} mm)",
                )
            )

        if comp.tolerance_mm is not None and comp.tolerance_mm < 0:
            anomalies.append(
                ValidationAnomaly(
                    code=AnomalyCode.TOLERANCE_OUT_OF_SPEC,
                    severity=AnomalySeverity.ERROR,
                    field="tolerance_mm",
                    raw_value=str(comp.tolerance_mm),
                    message=f"Negative tolerance is invalid (got {comp.tolerance_mm} mm)",
                )
            )

        if comp.max_pressure_mpa is not None and comp.max_pressure_mpa <= 0:
            anomalies.append(
                ValidationAnomaly(
                    code=AnomalyCode.NEGATIVE_PRESSURE,
                    severity=AnomalySeverity.ERROR,
                    field="max_pressure_mpa",
                    raw_value=str(comp.max_pressure_mpa),
                    message=f"Max pressure must be > 0 MPa (got {comp.max_pressure_mpa} MPa)",
                )
            )

        if (comp.temp_min_c is not None and comp.temp_min_c < -273.15) or (
            comp.temp_max_c is not None and comp.temp_max_c < -273.15
        ):
            anomalies.append(
                ValidationAnomaly(
                    code=AnomalyCode.IMPLAUSIBLE_TEMP_BELOW_ABS_ZERO,
                    severity=AnomalySeverity.ERROR,
                    field="operating_temp",
                    raw_value=f"{comp.temp_min_c}..{comp.temp_max_c}",
                    message=(
                        f"Operating temperature below absolute zero (-273.15 °C): "
                        f"[{comp.temp_min_c}, {comp.temp_max_c}] °C"
                    ),
                )
            )

        if (
            comp.temp_min_c is not None
            and comp.temp_max_c is not None
            and comp.temp_min_c >= comp.temp_max_c
        ):
            anomalies.append(
                ValidationAnomaly(
                    code=AnomalyCode.INVERTED_TEMP_RANGE,
                    severity=AnomalySeverity.ERROR,
                    field="operating_temp",
                    raw_value=f"{comp.temp_min_c}..{comp.temp_max_c}",
                    message=(
                        f"Inverted temperature range: min {comp.temp_min_c} °C >= "
                        f"max {comp.temp_max_c} °C"
                    ),
                )
            )

        # 3. Category tolerance envelope check
        if (
            comp.tolerance_mm is not None
            and comp.tolerance_mm >= 0
            and comp.category in CATEGORY_MAX_TOLERANCE_MM
        ):
            max_allowed = CATEGORY_MAX_TOLERANCE_MM[comp.category]
            if comp.tolerance_mm > max_allowed:
                anomalies.append(
                    ValidationAnomaly(
                        code=AnomalyCode.TOLERANCE_OUT_OF_SPEC,
                        severity=AnomalySeverity.ERROR,
                        field="tolerance_mm",
                        raw_value=str(comp.tolerance_mm),
                        message=(
                            f"Tolerance ±{comp.tolerance_mm} mm exceeds {comp.category.value} "
                            f"envelope limit of ±{max_allowed} mm"
                        ),
                    )
                )

        # 4. Completeness & category/certification checks
        if comp.nominal_dim_mm is None and "nominal_dim_mm" not in unparseable_fields:
            dim_severity = (
                AnomalySeverity.ERROR
                if comp.category in _DIM_ERROR_CATEGORIES
                else AnomalySeverity.WARNING
            )
            anomalies.append(
                ValidationAnomaly(
                    code=AnomalyCode.MISSING_DIMENSION,
                    severity=dim_severity,
                    field="nominal_dim_mm",
                    raw_value=None,
                    message=f"Missing nominal dimension for {comp.category.value} component",
                )
            )

        if comp.max_pressure_mpa is None and "max_pressure_mpa" not in unparseable_fields:
            if comp.category == ComponentCategory.VALVE:
                anomalies.append(
                    ValidationAnomaly(
                        code=AnomalyCode.MISSING_PRESSURE_FOR_FLUID_PART,
                        severity=AnomalySeverity.ERROR,
                        field="max_pressure_mpa",
                        raw_value=None,
                        message="Missing max pressure rating for VALVE component",
                    )
                )
            elif comp.category in _PRESSURE_WARNING_CATEGORIES:
                anomalies.append(
                    ValidationAnomaly(
                        code=AnomalyCode.MISSING_PRESSURE_FOR_FLUID_PART,
                        severity=AnomalySeverity.WARNING,
                        field="max_pressure_mpa",
                        raw_value=None,
                        message=(
                            f"Missing max pressure rating for {comp.category.value} fluid component"
                        ),
                    )
                )

        if comp.material_canonical is None and "material_canonical" not in unparseable_fields:
            anomalies.append(
                ValidationAnomaly(
                    code=AnomalyCode.MISSING_MATERIAL,
                    severity=AnomalySeverity.WARNING,
                    field="material_canonical",
                    raw_value=comp.material_raw,
                    message="Missing canonical material specification",
                )
            )

        if (
            comp.temp_min_c is None or comp.temp_max_c is None
        ) and "operating_temp" not in unparseable_fields:
            anomalies.append(
                ValidationAnomaly(
                    code=AnomalyCode.MISSING_TEMP_RANGE,
                    severity=AnomalySeverity.WARNING,
                    field="operating_temp",
                    raw_value=None,
                    message="Missing operating temperature range",
                )
            )

        if comp.category == ComponentCategory.UNKNOWN:
            anomalies.append(
                ValidationAnomaly(
                    code=AnomalyCode.UNKNOWN_CATEGORY,
                    severity=AnomalySeverity.ERROR,
                    field="category",
                    raw_value=comp.category_raw,
                    message=f"Unrecognized component category: {comp.category_raw!r}",
                )
            )

        if len(comp.standards) == 0:
            anomalies.append(
                ValidationAnomaly(
                    code=AnomalyCode.MISSING_CERTIFICATION,
                    severity=AnomalySeverity.ERROR,
                    field="standards",
                    raw_value=None,
                    message="Missing quality or aerospace certification standards",
                )
            )
        elif not any(_is_recognized_standard(std) for std in comp.standards):
            anomalies.append(
                ValidationAnomaly(
                    code=AnomalyCode.UNVERIFIED_QUALITY_STANDARD,
                    severity=AnomalySeverity.WARNING,
                    field="standards",
                    raw_value=", ".join(comp.standards),
                    message=f"No recognized aerospace/ISO quality standard in {comp.standards}",
                )
            )

        # 5. Final validation status
        has_error = any(a.severity == AnomalySeverity.ERROR for a in anomalies)
        has_warning = any(a.severity == AnomalySeverity.WARNING for a in anomalies)
        if has_error:
            status = "QUARANTINED"
        elif has_warning:
            status = "VALID_WITH_WARNINGS"
        else:
            status = "VALID"

        comp.anomalies = anomalies
        comp.validation_status = status
        validated.append(comp)

    return validated
