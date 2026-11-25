"""Deterministic engineering compliance matching engine for RFP requirements."""

from __future__ import annotations

import math
import re

from rapidfuzz import fuzz

from src.models import (
    AnomalySeverity,
    CandidateMatch,
    ComplianceStatus,
    CriterionEvaluation,
    NormalizedComponent,
    RequirementComplianceResult,
    RFPRequirement,
)

# IAQG 9100 aerospace quality management equivalents (compact upper-case tokens).
_IAQG_9100_EQUIVALENTS: frozenset[str] = frozenset(
    {
        "AS9100",
        "AS9100C",
        "AS9100D",
        "EN9100",
        "JISQ9100",
    }
)


def _normalize_std(std: str) -> str:
    """Normalize whitespace and uppercase a standard identifier."""
    return re.sub(r"\s+", " ", std.strip()).upper()


def _compact_std(std: str) -> str:
    """Return an upper-case standard token with all whitespace removed."""
    return re.sub(r"\s+", "", std.strip()).upper()


def _is_iaqg_9100(std_compact: str) -> bool:
    """Return True if a compact standard code belongs to the IAQG 9100 family."""
    if std_compact in _IAQG_9100_EQUIVALENTS:
        return True
    return std_compact.startswith(("AS9100", "EN9100", "JISQ9100"))


def _strip_org_prefix(std_norm: str) -> str:
    """Strip optional leading issuing-organization prefixes like 'SAE '."""
    if std_norm.startswith("SAE "):
        return std_norm[4:].strip()
    return std_norm


def _prefix_family_match(req_norm: str, avail_norm: str) -> bool:
    """Check exact or boundary-safe prefix/family match between two normalized standards."""
    if req_norm == avail_norm:
        return True

    req_compact = req_norm.replace(" ", "")
    avail_compact = avail_norm.replace(" ", "")
    if req_compact == avail_compact:
        return True

    if avail_norm.startswith(req_norm):
        rest = avail_norm[len(req_norm) :]
        if not rest:
            return True
        if rest[0] in (":", "-", "/", " ", "."):
            return True
        if req_norm[-1].isdigit() and rest[0].isalpha():
            return True
        if req_norm.isalpha() and rest[0].isdigit():
            return True

    if avail_compact.startswith(req_compact):
        rest_c = avail_compact[len(req_compact) :]
        if not rest_c:
            return True
        if rest_c[0] in (":", "-", "/", "."):
            return True
        if req_compact[-1].isdigit() and rest_c[0].isalpha():
            return True
        if req_compact.isalpha() and rest_c[0].isdigit():
            return True

    return False


def standard_matches(required: str, available: list[str]) -> bool:
    """Return True if any available standard satisfies the required standard.

    Normalizes whitespace and case, treats AS9100 / AS9100D / EN 9100 / EN9100 /
    JISQ 9100 as IAQG 9100 equivalents, and supports boundary-safe prefix/family
    matching (e.g., ``NAS`` -> ``NAS6204``, ``ISO 9001`` -> ``ISO 9001:2015``,
    ``AS4395`` -> ``SAE AS4395``).
    """
    req_norm = _normalize_std(required)
    if not req_norm or not available:
        return False

    req_compact = _compact_std(required)
    req_stripped = _strip_org_prefix(req_norm)

    for cand in available:
        avail_norm = _normalize_std(cand)
        if not avail_norm:
            continue
        avail_compact = _compact_std(cand)

        if _is_iaqg_9100(req_compact) and _is_iaqg_9100(avail_compact):
            return True

        avail_stripped = _strip_org_prefix(avail_norm)
        for r_form in (req_norm, req_stripped):
            for a_form in (avail_norm, avail_stripped):
                if _prefix_family_match(r_form, a_form):
                    return True

    return False


def _token_boundary_contains(needle: str, haystack: str) -> bool:
    """Return True if needle appears in haystack at alphanumeric token boundaries."""
    if len(needle) < 2 or len(haystack) < 2:
        return False
    pattern = rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])"
    return re.search(pattern, haystack) is not None


def material_matches(required_materials: list[str], component_material: str | None) -> bool:
    """Return True if component_material satisfies any required material specification.

    Returns True when ``required_materials`` is empty, and False when
    ``component_material`` is None or blank. Evaluates case-insensitive exact match,
    token-boundary substring containment, and ``rapidfuzz.fuzz.token_set_ratio >= 85``.
    """
    if not required_materials:
        return True
    if component_material is None or not component_material.strip():
        return False

    comp_norm = re.sub(r"\s+", " ", component_material.strip()).lower()

    for req_mat in required_materials:
        req_norm = re.sub(r"\s+", " ", req_mat.strip()).lower()
        if not req_norm:
            continue

        if req_norm == comp_norm:
            return True

        if _token_boundary_contains(req_norm, comp_norm) or _token_boundary_contains(
            comp_norm, req_norm
        ):
            return True

        if fuzz.token_set_ratio(req_norm, comp_norm) >= 85:
            return True

    return False


def _format_dim_requirement(dim_min_mm: float | None, dim_max_mm: float | None) -> str:
    """Format nominal dimension requirement bounds in SI millimeters."""
    if dim_min_mm is not None and dim_max_mm is not None:
        return f"{dim_min_mm:.2f} to {dim_max_mm:.2f} mm"
    if dim_min_mm is not None:
        return f">= {dim_min_mm:.2f} mm"
    return f"<= {dim_max_mm:.2f} mm"


def _evaluate_dimension(
    comp: NormalizedComponent, req: RFPRequirement
) -> CriterionEvaluation:
    """Evaluate nominal dimension against RFP min/max SI bounds."""
    required_str = _format_dim_requirement(req.dim_min_mm, req.dim_max_mm)
    if comp.nominal_dim_mm is None:
        return CriterionEvaluation(
            criterion="Nominal Dimension",
            required=required_str,
            actual="Not specified",
            passed=False,
            margin_note="Missing nominal dimension",
        )

    dim = comp.nominal_dim_mm
    actual_str = f"{dim:.2f} mm"
    above_min = req.dim_min_mm is None or dim >= req.dim_min_mm
    below_max = req.dim_max_mm is None or dim <= req.dim_max_mm
    passed = above_min and below_max

    if passed:
        if req.dim_min_mm is not None and req.dim_max_mm is not None:
            margin_low = dim - req.dim_min_mm
            margin_high = req.dim_max_mm - dim
            margin_note = (
                f"Within range (+{margin_low:.2f} mm above min, "
                f"+{margin_high:.2f} mm below max)"
            )
        elif req.dim_min_mm is not None:
            margin_note = f"+{dim - req.dim_min_mm:.2f} mm above min"
        else:
            assert req.dim_max_mm is not None
            margin_note = f"+{req.dim_max_mm - dim:.2f} mm below max"
    else:
        if not above_min and req.dim_min_mm is not None:
            margin_note = f"{dim - req.dim_min_mm:.2f} mm below min ({req.dim_min_mm:.2f} mm)"
        else:
            assert req.dim_max_mm is not None
            margin_note = f"+{dim - req.dim_max_mm:.2f} mm above max ({req.dim_max_mm:.2f} mm)"

    return CriterionEvaluation(
        criterion="Nominal Dimension",
        required=required_str,
        actual=actual_str,
        passed=passed,
        margin_note=margin_note,
    )


def _evaluate_tolerance(
    comp: NormalizedComponent, max_allowed_mm: float
) -> CriterionEvaluation:
    """Evaluate component tolerance against the RFP maximum allowable tolerance."""
    required_str = f"<= ±{max_allowed_mm:.3f} mm"
    if comp.tolerance_mm is None:
        return CriterionEvaluation(
            criterion="Max Tolerance",
            required=required_str,
            actual="Not specified",
            passed=False,
            margin_note="Missing tolerance specification",
        )

    tol = comp.tolerance_mm
    actual_str = f"±{tol:.3f} mm"
    passed = tol <= max_allowed_mm
    diff = max_allowed_mm - tol
    if passed:
        margin_note = f"+{diff:.3f} mm tolerance margin"
    else:
        margin_note = f"Exceeds limit by {abs(diff):.3f} mm"

    return CriterionEvaluation(
        criterion="Max Tolerance",
        required=required_str,
        actual=actual_str,
        passed=passed,
        margin_note=margin_note,
    )


def _evaluate_pressure(
    comp: NormalizedComponent, min_pressure_mpa: float
) -> CriterionEvaluation:
    """Evaluate component pressure rating against the RFP minimum requirement."""
    required_str = f">= {min_pressure_mpa:.2f} MPa"
    if comp.max_pressure_mpa is None:
        return CriterionEvaluation(
            criterion="Min Pressure",
            required=required_str,
            actual="Not specified",
            passed=False,
            margin_note="Missing pressure rating",
        )

    actual = comp.max_pressure_mpa
    actual_str = f"{actual:.2f} MPa"
    passed = actual >= min_pressure_mpa
    diff = actual - min_pressure_mpa
    pct = (diff / min_pressure_mpa * 100.0) if min_pressure_mpa > 0 else 0.0
    if passed:
        margin_note = f"+{diff:.2f} MPa (+{pct:.1f}% margin)"
    else:
        margin_note = f"{diff:.2f} MPa ({pct:.1f}% shortfall)"

    return CriterionEvaluation(
        criterion="Min Pressure",
        required=required_str,
        actual=actual_str,
        passed=passed,
        margin_note=margin_note,
    )


def _evaluate_temp_min(
    comp: NormalizedComponent, req_temp_min_c: float
) -> CriterionEvaluation:
    """Evaluate minimum operating temperature capability."""
    required_str = f"<= {req_temp_min_c:.1f} °C"
    if comp.temp_min_c is None:
        return CriterionEvaluation(
            criterion="Min Operating Temp",
            required=required_str,
            actual="Not specified",
            passed=False,
            margin_note="Missing minimum temperature rating",
        )

    actual = comp.temp_min_c
    passed = actual <= req_temp_min_c
    margin = req_temp_min_c - actual
    if passed:
        margin_note = f"+{margin:.1f} °C cold-end margin"
    else:
        margin_note = f"{abs(margin):.1f} °C warmer than required minimum"

    return CriterionEvaluation(
        criterion="Min Operating Temp",
        required=required_str,
        actual=f"{actual:.1f} °C",
        passed=passed,
        margin_note=margin_note,
    )


def _evaluate_temp_max(
    comp: NormalizedComponent, req_temp_max_c: float
) -> CriterionEvaluation:
    """Evaluate maximum operating temperature capability."""
    required_str = f">= {req_temp_max_c:.1f} °C"
    if comp.temp_max_c is None:
        return CriterionEvaluation(
            criterion="Max Operating Temp",
            required=required_str,
            actual="Not specified",
            passed=False,
            margin_note="Missing maximum temperature rating",
        )

    actual = comp.temp_max_c
    passed = actual >= req_temp_max_c
    margin = actual - req_temp_max_c
    if passed:
        margin_note = f"+{margin:.1f} °C hot-end margin"
    else:
        margin_note = f"{margin:.1f} °C shortfall below required max"

    return CriterionEvaluation(
        criterion="Max Operating Temp",
        required=required_str,
        actual=f"{actual:.1f} °C",
        passed=passed,
        margin_note=margin_note,
    )


def _build_waiver_notes(
    comp: NormalizedComponent,
    req: RFPRequirement,
    compliance_status: ComplianceStatus,
    checks: list[CriterionEvaluation],
) -> list[str]:
    """Generate engineering waiver notes for warning records or close partial deviations."""
    notes: list[str] = []

    if comp.validation_status == "VALID_WITH_WARNINGS":
        warning_anomalies = [
            a for a in comp.anomalies if a.severity == AnomalySeverity.WARNING
        ]
        if warning_anomalies:
            for anomaly in warning_anomalies:
                notes.append(
                    f"Catalog warning [{anomaly.code.value}]: {anomaly.message}"
                )
        else:
            notes.append(
                "Component carries VALID_WITH_WARNINGS status; verify catalog notes prior to PO."
            )

    if compliance_status == ComplianceStatus.PARTIAL_COMPLIANCE:
        for check in checks:
            if check.passed:
                continue
            if check.criterion == "Max Operating Temp" and comp.temp_max_c is not None and req.required_temp_max_c is not None:
                shortfall = req.required_temp_max_c - comp.temp_max_c
                if 0 < shortfall <= 50.0:
                    notes.append(
                        f"Thermal waiver candidate: {shortfall:.1f} °C max-temp shortfall "
                        f"({comp.temp_max_c:.1f} °C vs {req.required_temp_max_c:.1f} °C); "
                        "assess peak duty-cycle duration or supplementary heat-soak qualification."
                    )
            elif check.criterion == "Max Tolerance" and comp.tolerance_mm is not None and req.max_allowed_tolerance_mm is not None:
                excess = comp.tolerance_mm - req.max_allowed_tolerance_mm
                if 0 < excess <= req.max_allowed_tolerance_mm:
                    notes.append(
                        f"Tolerance waiver candidate: ±{comp.tolerance_mm:.3f} mm vs "
                        f"±{req.max_allowed_tolerance_mm:.3f} mm limit (+{excess:.3f} mm); "
                        "candidate for MRB concession or secondary finish machining."
                    )
            elif check.criterion == "Min Pressure" and comp.max_pressure_mpa is not None and req.min_pressure_mpa is not None:
                ratio = comp.max_pressure_mpa / req.min_pressure_mpa if req.min_pressure_mpa > 0 else 0.0
                if ratio >= 0.85:
                    notes.append(
                        f"Pressure waiver candidate: rated {comp.max_pressure_mpa:.2f} MPa vs "
                        f"{req.min_pressure_mpa:.2f} MPa ({ratio * 100:.1f}% of target); "
                        "evaluate proof-pressure requalification."
                    )
            elif check.criterion.startswith("Standards Group"):
                notes.append(
                    f"Certification gap ({check.required}): request supplier CoC/NADCAP "
                    "audit documentation or customer engineering deviation."
                )

    return notes


def _evaluate_candidate(
    comp: NormalizedComponent, req: RFPRequirement
) -> CandidateMatch:
    """Score a single non-quarantined component against all active RFP criteria."""
    checks: list[CriterionEvaluation] = []

    if req.required_materials:
        mat_passed = material_matches(req.required_materials, comp.material_canonical)
        req_mat_str = " OR ".join(req.required_materials)
        act_mat_str = comp.material_canonical or "Not specified"
        checks.append(
            CriterionEvaluation(
                criterion="Material",
                required=req_mat_str,
                actual=act_mat_str,
                passed=mat_passed,
                margin_note=(
                    "Compatible material match"
                    if mat_passed
                    else f"Mismatch ({act_mat_str} vs {req_mat_str})"
                ),
            )
        )

    if req.dim_min_mm is not None or req.dim_max_mm is not None:
        checks.append(_evaluate_dimension(comp, req))

    if req.max_allowed_tolerance_mm is not None:
        checks.append(_evaluate_tolerance(comp, req.max_allowed_tolerance_mm))

    if req.min_pressure_mpa is not None:
        checks.append(_evaluate_pressure(comp, req.min_pressure_mpa))

    if req.required_temp_min_c is not None:
        checks.append(_evaluate_temp_min(comp, req.required_temp_min_c))

    if req.required_temp_max_c is not None:
        checks.append(_evaluate_temp_max(comp, req.required_temp_max_c))

    for idx, group in enumerate(req.required_standard_groups, start=1):
        matched_reqs = [s for s in group if standard_matches(s, comp.standards)]
        std_passed = len(matched_reqs) > 0
        req_std_str = " OR ".join(group)
        act_std_str = ", ".join(comp.standards) if comp.standards else "None"
        checks.append(
            CriterionEvaluation(
                criterion=f"Standards Group {idx}",
                required=req_std_str,
                actual=act_std_str,
                passed=std_passed,
                margin_note=(
                    f"Satisfied ({', '.join(matched_reqs)})"
                    if std_passed
                    else f"Missing required standard ({req_std_str})"
                ),
            )
        )

    total_count = len(checks)
    passed_count = sum(1 for c in checks if c.passed)
    compliance_score = (
        round(100.0 * passed_count / total_count, 1) if total_count > 0 else 100.0
    )

    if passed_count == total_count:
        compliance_status = ComplianceStatus.COMPLIANT
    elif compliance_score >= 60.0:
        compliance_status = ComplianceStatus.PARTIAL_COMPLIANCE
    else:
        compliance_status = ComplianceStatus.NON_COMPLIANT

    discrepancies = [
        f"{c.criterion}: required {c.required}, actual {c.actual} ({c.margin_note})"
        for c in checks
        if not c.passed
    ]
    waiver_notes = _build_waiver_notes(comp, req, compliance_status, checks)

    return CandidateMatch(
        part_number=comp.part_number,
        supplier_name=comp.supplier_name,
        source_type=comp.source_type,
        validation_status=comp.validation_status,
        compliance_status=compliance_status,
        compliance_score=compliance_score,
        criteria_checks=checks,
        discrepancies=discrepancies,
        waiver_notes=waiver_notes,
        unit_price_usd=comp.unit_price_usd,
        lead_time_days=comp.lead_time_days,
    )


_STATUS_RANK: dict[ComplianceStatus, int] = {
    ComplianceStatus.COMPLIANT: 0,
    ComplianceStatus.PARTIAL_COMPLIANCE: 1,
    ComplianceStatus.NON_COMPLIANT: 2,
}


def _candidate_sort_key(
    match: CandidateMatch,
) -> tuple[int, float, int, int, float, float]:
    """Deterministic ranking key prioritizing compliance, validity, and commercial terms."""
    return (
        _STATUS_RANK[match.compliance_status],
        -match.compliance_score,
        0 if match.validation_status == "VALID" else 1,
        len(match.discrepancies),
        match.unit_price_usd if match.unit_price_usd is not None else math.inf,
        float(match.lead_time_days) if match.lead_time_days is not None else math.inf,
    )


def _build_recommendation(
    req: RFPRequirement,
    best: CandidateMatch | None,
    alternatives: list[CandidateMatch],
    quarantined_excluded_count: int,
) -> str:
    """Write a concise engineering recommendation string for an RFP requirement."""
    quarantine_note = (
        f" ({quarantined_excluded_count} quarantined catalog item(s) excluded)."
        if quarantined_excluded_count > 0
        else "."
    )
    if best is None:
        return (
            f"NO CANDIDATES FOUND for {req.req_id} in category {req.category.value}"
            f"{quarantine_note} Initiate custom supplier RFQ or catalog sourcing."
        )

    price_str = (
        f"${best.unit_price_usd:.2f}" if best.unit_price_usd is not None else "N/A"
    )
    lead_str = f"{best.lead_time_days}d" if best.lead_time_days is not None else "N/A"
    alt_str = (
        f" Alternatives: {', '.join(a.part_number for a in alternatives)}."
        if alternatives
        else ""
    )

    if best.compliance_status == ComplianceStatus.COMPLIANT:
        warn_note = (
            " Note: catalog record has VALID_WITH_WARNINGS; verify warning items before PO."
            if best.validation_status != "VALID"
            else ""
        )
        return (
            f"RECOMMEND {best.part_number} ({best.supplier_name}) — 100.0% compliant "
            f"[{price_str}, {lead_str} lead]{quarantine_note}{warn_note}{alt_str}"
        )

    if best.compliance_status == ComplianceStatus.PARTIAL_COMPLIANCE:
        gap_summary = "; ".join(best.discrepancies[:2])
        return (
            f"CONDITIONAL / WAIVER REVIEW for {best.part_number} ({best.supplier_name}) — "
            f"{best.compliance_score:.1f}% score [{price_str}, {lead_str} lead]. "
            f"Discrepancies: {gap_summary}{quarantine_note}{alt_str}"
        )

    gap_summary = "; ".join(best.discrepancies[:3])
    return (
        f"NON-COMPLIANT: Best available {best.part_number} ({best.supplier_name}) "
        f"scored only {best.compliance_score:.1f}%. Critical gaps: {gap_summary}"
        f"{quarantine_note} Issue external RFQ / custom engineering qualification."
    )


def match_requirements(
    requirements: list[RFPRequirement],
    components: list[NormalizedComponent],
) -> list[RequirementComplianceResult]:
    """Evaluate all RFP requirements against non-quarantined catalog components."""
    results: list[RequirementComplianceResult] = []

    for req in requirements:
        category_components = [c for c in components if c.category == req.category]
        quarantined_excluded_count = sum(
            1 for c in category_components if c.validation_status == "QUARANTINED"
        )
        eligible = [
            c for c in category_components if c.validation_status != "QUARANTINED"
        ]

        evaluated = [_evaluate_candidate(comp, req) for comp in eligible]
        evaluated.sort(key=_candidate_sort_key)

        best_match = evaluated[0] if evaluated else None
        alternative_matches = evaluated[1:3]
        overall_status = (
            best_match.compliance_status
            if best_match is not None
            else ComplianceStatus.NON_COMPLIANT
        )
        recommendation = _build_recommendation(
            req, best_match, alternative_matches, quarantined_excluded_count
        )

        results.append(
            RequirementComplianceResult(
                requirement=req,
                overall_status=overall_status,
                best_match=best_match,
                alternative_matches=alternative_matches,
                evaluated_candidates_count=len(eligible),
                quarantined_excluded_count=quarantined_excluded_count,
                recommendation=recommendation,
            )
        )

    return results
