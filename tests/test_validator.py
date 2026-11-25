"""Tests for deterministic engineering validation and anomaly quarantine rules."""

from __future__ import annotations

import pytest

from src.models import AnomalyCode, AnomalySeverity, ComponentCategory, NormalizedComponent
from src.parser import normalize_record
from src.validator import validate_catalog


def _validate_single(raw_record) -> NormalizedComponent:
    return validate_catalog([normalize_record(raw_record)])[0]


def test_clean_component_validates_as_valid(make_raw_record) -> None:
    comp = _validate_single(make_raw_record())
    assert comp.validation_status == "VALID"
    assert comp.anomalies == []


@pytest.mark.parametrize("dim_raw", ["-5.0 mm", "0.0 mm"])
def test_negative_or_zero_dimension_quarantines(make_raw_record, dim_raw: str) -> None:
    comp = _validate_single(make_raw_record(nominal_dim_raw=dim_raw))
    assert comp.validation_status == "QUARANTINED"
    assert any(
        a.code == AnomalyCode.NEGATIVE_OR_ZERO_DIMENSION
        and a.severity == AnomalySeverity.ERROR
        for a in comp.anomalies
    )


@pytest.mark.parametrize("tol_raw", ["±0.65 mm", "±0.08 in"])
def test_fastener_tolerance_out_of_spec_quarantines(
    make_raw_record, tol_raw: str
) -> None:
    comp = _validate_single(
        make_raw_record(category_raw="Fastener", tolerance_raw=tol_raw)
    )
    assert comp.validation_status == "QUARANTINED"
    assert any(
        a.code == AnomalyCode.TOLERANCE_OUT_OF_SPEC
        and a.severity == AnomalySeverity.ERROR
        for a in comp.anomalies
    )


def test_negative_tolerance_quarantines(make_normalized_component) -> None:
    comp = validate_catalog([make_normalized_component(tolerance_mm=-0.02)])[0]
    assert comp.validation_status == "QUARANTINED"
    assert any(a.code == AnomalyCode.TOLERANCE_OUT_OF_SPEC for a in comp.anomalies)


@pytest.mark.parametrize("temp_raw", ["200 C to 50 C", "100 °C to 100 °C"])
def test_inverted_temp_range_quarantines(make_raw_record, temp_raw: str) -> None:
    comp = _validate_single(make_raw_record(operating_temp_raw=temp_raw))
    assert comp.validation_status == "QUARANTINED"
    assert any(
        a.code == AnomalyCode.INVERTED_TEMP_RANGE
        and a.severity == AnomalySeverity.ERROR
        for a in comp.anomalies
    )


def test_implausible_temp_below_abs_zero_quarantines(make_raw_record) -> None:
    comp = _validate_single(make_raw_record(operating_temp_raw="-300 °C to 120 °C"))
    assert comp.validation_status == "QUARANTINED"
    assert any(
        a.code == AnomalyCode.IMPLAUSIBLE_TEMP_BELOW_ABS_ZERO
        and a.severity == AnomalySeverity.ERROR
        for a in comp.anomalies
    )


def test_missing_pressure_for_valve_is_error_quarantined(make_raw_record) -> None:
    comp = _validate_single(
        make_raw_record(
            category_raw="Valve",
            description="Hydraulic control valve",
            max_pressure_raw="",
        )
    )
    assert comp.validation_status == "QUARANTINED"
    assert any(
        a.code == AnomalyCode.MISSING_PRESSURE_FOR_FLUID_PART
        and a.severity == AnomalySeverity.ERROR
        for a in comp.anomalies
    )


@pytest.mark.parametrize("cat_raw", ["Fitting", "Seal"])
def test_missing_pressure_for_fitting_or_seal_is_warning(
    make_raw_record, cat_raw: str
) -> None:
    comp = _validate_single(
        make_raw_record(
            category_raw=cat_raw,
            description=f"Aerospace {cat_raw}",
            max_pressure_raw="",
        )
    )
    assert comp.validation_status == "VALID_WITH_WARNINGS"
    assert any(
        a.code == AnomalyCode.MISSING_PRESSURE_FOR_FLUID_PART
        and a.severity == AnomalySeverity.WARNING
        for a in comp.anomalies
    )


@pytest.mark.parametrize("pres_raw", ["-15 bar", "0 MPa"])
def test_negative_or_zero_pressure_quarantines(
    make_raw_record, pres_raw: str
) -> None:
    comp = _validate_single(
        make_raw_record(
            category_raw="Valve",
            description="Hydraulic valve",
            max_pressure_raw=pres_raw,
        )
    )
    assert comp.validation_status == "QUARANTINED"
    assert any(
        a.code == AnomalyCode.NEGATIVE_PRESSURE
        and a.severity == AnomalySeverity.ERROR
        for a in comp.anomalies
    )


def test_duplicate_part_number_case_and_whitespace_quarantines(
    make_raw_record,
) -> None:
    first = normalize_record(
        make_raw_record(part_number="TI64-BOLT-M8", source_location="row:1")
    )
    dup = normalize_record(
        make_raw_record(part_number="ti64-bolt-m8 ", source_location="row:11")
    )
    res = validate_catalog([first, dup])
    assert res[0].validation_status == "VALID"
    assert res[1].validation_status == "QUARANTINED"
    assert any(
        a.code == AnomalyCode.DUPLICATE_PART_NUMBER
        and a.severity == AnomalySeverity.ERROR
        for a in res[1].anomalies
    )


@pytest.mark.parametrize(
    ("field_overrides", "expected_field"),
    [
        ({"nominal_dim_raw": "approx half inch?"}, "nominal_dim_mm"),
        (
            {
                "category_raw": "Valve",
                "description": "Valve",
                "max_pressure_raw": "high pressure",
            },
            "max_pressure_mpa",
        ),
    ],
)
def test_unparseable_unit_quarantines_without_double_missing_flag(
    make_raw_record, field_overrides: dict[str, str], expected_field: str
) -> None:
    comp = _validate_single(make_raw_record(**field_overrides))
    assert comp.validation_status == "QUARANTINED"
    unparseable = [
        a for a in comp.anomalies if a.code == AnomalyCode.UNPARSEABLE_UNIT
    ]
    assert len(unparseable) == 1
    assert unparseable[0].field == expected_field
    # Should not emit MISSING_DIMENSION / MISSING_PRESSURE_FOR_FLUID_PART for the same unparseable field
    assert all(
        a.code
        not in (
            AnomalyCode.MISSING_DIMENSION,
            AnomalyCode.MISSING_PRESSURE_FOR_FLUID_PART,
        )
        for a in comp.anomalies
    )


def test_missing_certification_unknown_category_and_unverified_standard(
    make_raw_record,
) -> None:
    no_cert = _validate_single(make_raw_record(standards_raw="Non certifié"))
    assert no_cert.validation_status == "QUARANTINED"
    assert any(
        a.code == AnomalyCode.MISSING_CERTIFICATION
        and a.severity == AnomalySeverity.ERROR
        for a in no_cert.anomalies
    )

    unknown_cat = _validate_single(
        make_raw_record(
            category_raw="Unclassified Hardware",
            description="Ambiguous bracket",
        )
    )
    assert unknown_cat.validation_status == "QUARANTINED"
    assert any(
        a.code == AnomalyCode.UNKNOWN_CATEGORY
        and a.severity == AnomalySeverity.ERROR
        for a in unknown_cat.anomalies
    )

    unverified_std = _validate_single(make_raw_record(standards_raw="CUSTOM-SPEC-99"))
    assert unverified_std.validation_status == "VALID_WITH_WARNINGS"
    assert any(
        a.code == AnomalyCode.UNVERIFIED_QUALITY_STANDARD
        and a.severity == AnomalySeverity.WARNING
        for a in unverified_std.anomalies
    )


def test_missing_dimension_material_and_temp_range_rules(make_raw_record) -> None:
    missing_fit_dim = _validate_single(
        make_raw_record(
            category_raw="Fitting",
            description="Hydraulic fitting",
            nominal_dim_raw="",
            max_pressure_raw="28 MPa",
        )
    )
    assert missing_fit_dim.validation_status == "QUARANTINED"
    assert any(
        a.code == AnomalyCode.MISSING_DIMENSION
        and a.severity == AnomalySeverity.ERROR
        for a in missing_fit_dim.anomalies
    )

    missing_mat = _validate_single(make_raw_record(material_spec="N/A"))
    assert missing_mat.validation_status == "VALID_WITH_WARNINGS"
    assert any(
        a.code == AnomalyCode.MISSING_MATERIAL
        and a.severity == AnomalySeverity.WARNING
        for a in missing_mat.anomalies
    )

    missing_temp = _validate_single(make_raw_record(operating_temp_raw=""))
    assert missing_temp.validation_status == "VALID_WITH_WARNINGS"
    assert any(
        a.code == AnomalyCode.MISSING_TEMP_RANGE
        and a.severity == AnomalySeverity.WARNING
        for a in missing_temp.anomalies
    )


def test_synthetic_dataset_validation_counts(
    validated_catalog: list[NormalizedComponent],
) -> None:
    assert len(validated_catalog) == 56
    valid = [c for c in validated_catalog if c.validation_status == "VALID"]
    warnings = [
        c for c in validated_catalog if c.validation_status == "VALID_WITH_WARNINGS"
    ]
    quarantined = [
        c for c in validated_catalog if c.validation_status == "QUARANTINED"
    ]
    assert len(valid) == 41
    assert len(warnings) == 2
    assert len(quarantined) == 13
    assert {c.part_number for c in warnings} == {"BAD-ALY-NOMAT", "BAD-SL-NOTEMP"}
    assert sum(len(c.anomalies) for c in validated_catalog) == 16
    assert any(
        c.part_number == "CRYO-SNS-999" and c.category == ComponentCategory.SENSOR
        for c in quarantined
    )
