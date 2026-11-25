"""Tests for CSV/PDF/RFP Markdown parsers and bilingual EN/FR normalizers."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.models import AnomalyCode, ComponentCategory, RawSupplierRecord
from src.parser import (
    normalize_category,
    normalize_material,
    normalize_record,
    normalize_standards,
    parse_rfp_markdown,
    parse_supplier_csv,
    parse_supplier_pdf,
    standardize_description_en,
)


def test_parse_supplier_csv_returns_50_rows(supplier_csv_path: Path) -> None:
    records = parse_supplier_csv(supplier_csv_path)
    assert len(records) == 50
    assert all(r.source_type == "csv" for r in records)
    assert all(r.source_file == "supplier_catalog_dirty.csv" for r in records)
    assert records[0].part_number == "TI64-BOLT-M8"
    assert records[0].source_location == "row:1"
    assert records[-1].part_number == "BAD-UNK-001"
    assert records[-1].source_location == "row:50"


def test_parse_supplier_pdf_returns_6_rows_with_preserved_accents(
    supplier_pdf_path: Path,
) -> None:
    records = parse_supplier_pdf(supplier_pdf_path)
    assert len(records) == 6
    assert [r.part_number for r in records] == [
        "TI-FIT-038",
        "CRYO-VLV-112",
        "DPS-SNS-404",
        "ACT-ELH-710",
        "TI-SEAL-088",
        "CRYO-SNS-999",
    ]
    assert all(r.source_type == "pdf" for r in records)

    # Verify French accents extracted cleanly with zero replacement/garbled characters
    all_text = " ".join(
        f"{r.supplier_name} {r.category_raw} {r.description} {r.operating_temp_raw}"
        for r in records
    )
    assert "\ufffd" not in all_text
    assert "MécaFluide Bordeaux" in all_text
    assert "Systèmes Vol Toulouse" in all_text
    assert "Joints Aéronautiques SA" in all_text
    assert "Capteur thermique défectueux" in all_text
    assert "Actionneur électro-hydraulique" in all_text


@pytest.mark.parametrize(
    ("raw_cat", "description", "expected"),
    [
        ("Fastener", "", ComponentCategory.FASTENER),
        ("Fixation", "", ComponentCategory.FASTENER),
        ("Visserie", "", ComponentCategory.FASTENER),
        ("Boulonnerie", "", ComponentCategory.FASTENER),
        ("Hydraulic Valve", "", ComponentCategory.VALVE),
        ("Vanne", "", ComponentCategory.VALVE),
        ("Électrovanne", "", ComponentCategory.VALVE),
        ("Superalloy", "", ComponentCategory.ALLOY),
        ("Alliage aéronautique", "", ComponentCategory.ALLOY),
        ("Joint d'étanchéité", "", ComponentCategory.SEAL),
        ("O-Ring Seal", "", ComponentCategory.SEAL),
        ("Raccord", "", ComponentCategory.FITTING),
        ("Fitting / Raccord hydraulique", "", ComponentCategory.FITTING),
        ("Actionneur", "", ComponentCategory.ACTUATOR),
        ("Capteur", "", ComponentCategory.SENSOR),
        ("Unclassified Hardware", "Ambiguous bracket", ComponentCategory.UNKNOWN),
        ("", "Titanium structural bolt", ComponentCategory.FASTENER),
    ],
)
def test_normalize_category_en_fr(
    raw_cat: str, description: str, expected: ComponentCategory
) -> None:
    assert normalize_category(raw_cat, description) == expected


@pytest.mark.parametrize(
    ("raw_mat", "expected"),
    [
        ("Ti-6Al-4V (Grade 5)", "Ti-6Al-4V"),
        ("Titane Ti-6Al-4V", "Ti-6Al-4V"),
        ("Inconel 718 (UNS N07718)", "Inconel 718"),
        ("17-4PH", "17-4PH Stainless Steel"),
        ("Acier inoxydable 316L", "316L Stainless Steel"),
        ("A286 Superalloy", "A286 Stainless Steel"),
        ("7075-T6 Aluminum", "Aluminum 7075-T6"),
        ("Fluorosilicone", "Fluorosilicone (FVMQ)"),
        ("FKM (Viton)", "FKM (Viton)"),
        ("N/A", None),
        ("", None),
    ],
)
def test_normalize_material_en_fr(raw_mat: str, expected: str | None) -> None:
    assert normalize_material(raw_mat) == expected


def test_standardize_description_en_languages() -> None:
    en_text, lang_en = standardize_description_en(
        "Titanium hex head structural bolt for wing-spar attachment"
    )
    assert lang_en == "en"
    assert en_text == "Titanium hex head structural bolt for wing-spar attachment"

    fr_text, lang_fr = standardize_description_en(
        "Vis hexagonale structurale en titane pour longeron de voilure"
    )
    assert lang_fr == "fr"
    assert "titanium" in fr_text.lower()
    assert "hex bolt" in fr_text.lower()

    bi_text, lang_bi = standardize_description_en(
        "Goupille de cisaillement en titane / Titanium shear pin"
    )
    assert lang_bi == "bilingual"
    assert bi_text == "Titanium shear pin"


def test_normalize_standards() -> None:
    assert normalize_standards("AS 9100D, EN 9100; as9100d, NADCAP") == [
        "AS9100D",
        "EN 9100",
        "NADCAP",
    ]
    assert normalize_standards("Non certifié") == []
    assert normalize_standards("N/A") == []


def test_normalize_record_conversion_traces_and_unparseable_flag(
    make_raw_record,
) -> None:
    clean_raw: RawSupplierRecord = make_raw_record(
        part_number="  ti64-bolt-m8 ",
        nominal_dim_raw='1/4"',
        tolerance_raw="±0.001 in",
        operating_temp_raw="-65 °F to 275 °F",
        mass_raw="0.65 oz",
        lead_time_days="2 semaines",
    )
    comp = normalize_record(clean_raw)
    assert comp.part_number == "TI64-BOLT-M8"
    assert comp.nominal_dim_mm == pytest.approx(6.35)
    assert comp.tolerance_mm == pytest.approx(0.0254)
    assert comp.temp_max_c == pytest.approx(135.0)
    assert comp.lead_time_days == 14
    assert comp.anomalies == []
    assert {t.field for t in comp.conversion_traces} == {
        "nominal_dim",
        "tolerance",
        "temp_min",
        "temp_max",
        "mass",
    }

    bad_raw: RawSupplierRecord = make_raw_record(
        nominal_dim_raw="approx half inch?",
        max_pressure_raw="high pressure",
    )
    bad_comp = normalize_record(bad_raw)
    codes = [(a.code, a.field) for a in bad_comp.anomalies]
    assert (AnomalyCode.UNPARSEABLE_UNIT, "nominal_dim_mm") in codes
    assert (AnomalyCode.UNPARSEABLE_UNIT, "max_pressure_mpa") in codes


def test_parse_rfp_markdown_returns_expected_requirements(
    rfp_markdown_path: Path,
) -> None:
    rfp_id, title, requirements = parse_rfp_markdown(rfp_markdown_path)
    assert rfp_id == "RFP-AERO-2026-042"
    assert "Next-Generation Wing" in title
    assert len(requirements) == 10

    by_id = {req.req_id: req for req in requirements}

    req1 = by_id["REQ-001"]
    assert req1.category == ComponentCategory.FASTENER
    assert req1.dim_min_mm == pytest.approx(8.0)
    assert req1.dim_max_mm == pytest.approx(12.0)
    assert req1.max_allowed_tolerance_mm == pytest.approx(0.05)
    assert req1.min_pressure_mpa is None
    assert req1.required_standard_groups == [
        ["AS9100D", "EN 9100"],
        ["AMS 4928", "NASM21250"],
    ]

    # REQ-002 has imperial dimensions, psi pressure, and °F temperature range in French
    req2 = by_id["REQ-002"]
    assert req2.category == ComponentCategory.VALVE
    assert req2.language == "fr"
    assert req2.dim_min_mm == pytest.approx(12.7)
    assert req2.dim_max_mm == pytest.approx(38.1)
    assert req2.min_pressure_mpa == pytest.approx(20.68427188)
    assert req2.required_temp_min_c == pytest.approx(-53.888888889)
    assert req2.required_temp_max_c == pytest.approx(135.0)

    req9 = by_id["REQ-009"]
    assert req9.min_pressure_mpa == pytest.approx(65.0)
    assert req9.required_temp_max_c == pytest.approx(550.0)
