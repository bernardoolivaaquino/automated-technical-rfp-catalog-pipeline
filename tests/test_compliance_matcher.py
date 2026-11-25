"""Tests for deterministic RFP compliance scoring, equivalence rules, and quarantine safety."""

from __future__ import annotations

from src.compliance_matcher import (
    match_requirements,
    material_matches,
    standard_matches,
)
from src.models import (
    AnomalyCode,
    AnomalySeverity,
    ComplianceStatus,
    ComponentCategory,
    ValidationAnomaly,
)


def test_iaqg_9100_equivalence_and_prefix_family_matching() -> None:
    # IAQG 9100 mutual equivalence across AS9100D / EN 9100 / JISQ 9100 / AS 9100
    assert standard_matches("AS9100D", ["EN 9100", "NADCAP"]) is True
    assert standard_matches("EN 9100", ["AS9100D"]) is True
    assert standard_matches("AS9100C", ["JISQ 9100"]) is True
    assert standard_matches("AS 9100D", ["EN9100"]) is True

    # Boundary-safe prefix/family and SAE prefix handling
    assert standard_matches("NAS", ["NAS6204"]) is True
    assert standard_matches("ISO 9001", ["ISO 9001:2015"]) is True
    assert standard_matches("AS4395", ["SAE AS4395"]) is True
    assert standard_matches("SAE AS4395", ["AS4395"]) is True

    # Non-matching or missing standards
    assert standard_matches("NADCAP", ["AS9100D", "ISO 9001"]) is False
    assert standard_matches("AS9100D", []) is False


def test_material_matches_variants() -> None:
    assert material_matches(["Ti-6Al-4V"], "Ti-6Al-4V") is True
    assert material_matches(["17-4PH", "Inconel 718"], "17-4PH Stainless Steel") is True
    assert material_matches(["FKM"], "FKM (Viton)") is True
    assert material_matches(["316L Stainless Steel"], "316L Stainless Steel") is True
    assert material_matches(["Ti-6Al-4V"], "Aluminum 7075-T6") is False
    assert material_matches(["Ti-6Al-4V"], None) is False
    assert material_matches([], "Aluminum 7075-T6") is True


def test_compliance_outcomes_compliant_partial_and_non_compliant(
    make_normalized_component,
    make_rfp_requirement,
) -> None:
    req = make_rfp_requirement(
        req_id="REQ-100",
        category=ComponentCategory.FASTENER,
        required_materials=["Ti-6Al-4V"],
        dim_min_mm=8.0,
        dim_max_mm=12.0,
        max_allowed_tolerance_mm=0.05,
        min_pressure_mpa=None,
        required_temp_min_c=-55.0,
        required_temp_max_c=180.0,
        required_standard_groups=[["AS9100D", "EN 9100"], ["AMS 4928"]],
    )

    # 1. Fully COMPLIANT (6/6 criteria pass, EN 9100 satisfies AS9100D via IAQG equivalence)
    compliant_comp = make_normalized_component(
        part_number="COMP-OK",
        standards=["EN 9100", "AMS 4928"],
        nominal_dim_mm=10.0,
        tolerance_mm=0.025,
        temp_min_c=-60.0,
        temp_max_c=220.0,
    )
    res_ok = match_requirements([req], [compliant_comp])[0]
    assert res_ok.overall_status == ComplianceStatus.COMPLIANT
    assert res_ok.best_match is not None
    assert res_ok.best_match.part_number == "COMP-OK"
    assert res_ok.best_match.compliance_score == 100.0
    assert res_ok.best_match.discrepancies == []

    # 2. PARTIAL_COMPLIANCE (6/7 = 85.7% >= 60%, minor thermal shortfall -> waiver note)
    partial_comp = make_normalized_component(
        part_number="COMP-PARTIAL",
        standards=["AS9100D", "AMS 4928"],
        nominal_dim_mm=10.0,
        tolerance_mm=0.025,
        temp_min_c=-60.0,
        temp_max_c=160.0,  # 20 C shortfall below 180 C
    )
    res_partial = match_requirements([req], [partial_comp])[0]
    assert res_partial.overall_status == ComplianceStatus.PARTIAL_COMPLIANCE
    assert res_partial.best_match is not None
    assert res_partial.best_match.compliance_score == 85.7
    assert any("Thermal waiver candidate" in note for note in res_partial.best_match.waiver_notes)

    # 3. NON_COMPLIANT (< 60% score: fails material, dim, tol, temp_min, temp_max, std group 2 -> 1/7 or 1/6)
    non_comp = make_normalized_component(
        part_number="COMP-BAD",
        material_canonical="Aluminum 7075-T6",
        nominal_dim_mm=25.0,
        tolerance_mm=0.10,
        temp_min_c=-20.0,
        temp_max_c=100.0,
        standards=["AS9100D"],
    )
    res_bad = match_requirements([req], [non_comp])[0]
    assert res_bad.overall_status == ComplianceStatus.NON_COMPLIANT
    assert res_bad.best_match is not None
    assert res_bad.best_match.compliance_score < 60.0

    # 4. No eligible candidates in category -> NON_COMPLIANT with best_match=None
    res_empty = match_requirements([req], [])[0]
    assert res_empty.overall_status == ComplianceStatus.NON_COMPLIANT
    assert res_empty.best_match is None
    assert res_empty.evaluated_candidates_count == 0


def test_quarantined_components_never_selected_even_with_perfect_specs(
    make_normalized_component,
    make_rfp_requirement,
) -> None:
    """Quarantined records must never appear in best_match or alternative_matches."""
    req = make_rfp_requirement(
        req_id="REQ-SAFETY",
        category=ComponentCategory.VALVE,
        required_materials=["Inconel 718"],
        dim_min_mm=20.0,
        dim_max_mm=30.0,
        max_allowed_tolerance_mm=0.05,
        min_pressure_mpa=20.0,
        required_temp_min_c=-50.0,
        required_temp_max_c=200.0,
        required_standard_groups=[["AS9100D"]],
    )

    # Perfect numeric specs + super cheap/fast, but QUARANTINED (e.g. duplicate PN)
    quarantined_perfect = make_normalized_component(
        part_number="QUAR-PERFECT-CHEAP",
        category=ComponentCategory.VALVE,
        material_canonical="Inconel 718",
        nominal_dim_mm=25.0,
        tolerance_mm=0.01,
        max_pressure_mpa=40.0,
        temp_min_c=-60.0,
        temp_max_c=300.0,
        standards=["AS9100D"],
        unit_price_usd=1.0,
        lead_time_days=1,
        validation_status="QUARANTINED",
        anomalies=[
            ValidationAnomaly(
                code=AnomalyCode.DUPLICATE_PART_NUMBER,
                severity=AnomalySeverity.ERROR,
                field="part_number",
                raw_value="QUAR-PERFECT-CHEAP",
                message="Duplicate part number",
            )
        ],
    )

    # Legitimate but expensive/slower valid candidate
    valid_candidate = make_normalized_component(
        part_number="VALID-ELIGIBLE",
        category=ComponentCategory.VALVE,
        material_canonical="Inconel 718",
        nominal_dim_mm=25.4,
        tolerance_mm=0.04,
        max_pressure_mpa=24.0,
        temp_min_c=-55.0,
        temp_max_c=220.0,
        standards=["EN 9100"],
        unit_price_usd=1500.0,
        lead_time_days=30,
        validation_status="VALID",
    )

    # Case A: both quarantined and eligible exist
    res = match_requirements([req], [quarantined_perfect, valid_candidate])[0]
    assert res.quarantined_excluded_count == 1
    assert res.evaluated_candidates_count == 1
    assert res.best_match is not None
    assert res.best_match.part_number == "VALID-ELIGIBLE"
    assert all(
        alt.part_number != "QUAR-PERFECT-CHEAP" for alt in res.alternative_matches
    )

    # Case B: ONLY quarantined candidate exists -> must return None, never leak quarantined
    res_only_quar = match_requirements([req], [quarantined_perfect])[0]
    assert res_only_quar.quarantined_excluded_count == 1
    assert res_only_quar.evaluated_candidates_count == 0
    assert res_only_quar.best_match is None
    assert res_only_quar.alternative_matches == []
    assert res_only_quar.overall_status == ComplianceStatus.NON_COMPLIANT


def test_synthetic_dataset_compliance_matrix(validated_catalog, parsed_rfp) -> None:
    _, _, requirements = parsed_rfp
    results = match_requirements(requirements, validated_catalog)
    assert len(results) == 10

    statuses = [r.overall_status for r in results]
    assert statuses.count(ComplianceStatus.COMPLIANT) == 7
    assert statuses.count(ComplianceStatus.PARTIAL_COMPLIANCE) == 2
    assert statuses.count(ComplianceStatus.NON_COMPLIANT) == 1

    by_id = {r.requirement.req_id: r for r in results}
    assert by_id["REQ-008"].overall_status == ComplianceStatus.PARTIAL_COMPLIANCE
    assert by_id["REQ-010"].overall_status == ComplianceStatus.PARTIAL_COMPLIANCE
    assert by_id["REQ-009"].overall_status == ComplianceStatus.NON_COMPLIANT

    # Verify zero quarantined components anywhere in best_match or alternative_matches.
    # Note: TI64-BOLT-M8 has a valid record (row:1) and a duplicate quarantined record (row:11),
    # so exclude part numbers that also have an eligible record from the strictly-quarantined set.
    eligible_pns = {
        c.part_number
        for c in validated_catalog
        if c.validation_status != "QUARANTINED"
    }
    strictly_quarantined_pns = {
        c.part_number
        for c in validated_catalog
        if c.validation_status == "QUARANTINED" and c.part_number not in eligible_pns
    }
    for r in results:
        if r.best_match is not None:
            assert r.best_match.validation_status != "QUARANTINED"
            assert r.best_match.part_number not in strictly_quarantined_pns
        for alt in r.alternative_matches:
            assert alt.validation_status != "QUARANTINED"
            assert alt.part_number not in strictly_quarantined_pns
