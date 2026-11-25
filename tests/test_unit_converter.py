"""Tests for deterministic NIST/ISO unit conversion and parsing utilities."""

from __future__ import annotations

import pytest

from src.unit_converter import (
    INCH_TO_MM,
    KELVIN_OFFSET,
    LB_TO_KG,
    OZ_TO_KG,
    PSI_TO_MPA,
    UnitParseError,
    is_missing_value,
    parse_lead_time_days,
    parse_length_range_to_mm,
    parse_length_to_mm,
    parse_mass_to_kg,
    parse_number,
    parse_pressure_to_mpa,
    parse_price_usd,
    parse_temp_range_to_c,
    parse_temp_threshold_to_c,
    parse_tolerance_to_mm,
)


@pytest.mark.parametrize("token", ["", "   ", "N/A", "na", "TBD", "tbd", "None", "-", "—", "–"])
def test_missing_tokens_return_none(token: str) -> None:
    """Empty strings and standard N/A or TBD placeholders must return None across parsers."""
    assert is_missing_value(token) is True
    assert parse_length_to_mm(token) is None
    assert parse_tolerance_to_mm(token) is None
    assert parse_pressure_to_mpa(token) is None
    assert parse_temp_range_to_c(token) is None
    assert parse_length_range_to_mm(token) is None
    assert parse_temp_threshold_to_c(token) == (None, None)
    assert parse_mass_to_kg(token) is None
    assert parse_price_usd(token) is None
    assert parse_lead_time_days(token) is None


def test_is_missing_value_none() -> None:
    assert is_missing_value(None) is True
    assert is_missing_value("10.0 mm") is False


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("25.4", 25.4),
        ("25,4", 25.4),
        ("1/4", 0.25),
        ("3/8", 0.375),
        ("1-1/2", 1.5),
        ("1 1/2", 1.5),
        ("-5.0", -5.0),
        ("- 5.0", -5.0),
        ("1,250.50", 1250.5),
        ("1.250,50", 1250.5),
    ],
)
def test_parse_number_formats(raw: str, expected: float) -> None:
    assert parse_number(raw) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("raw", "expected_mm", "expected_orig_unit"),
    [
        ("1 in", INCH_TO_MM, "in"),
        ("0.25 in", 6.35, "in"),
        ('1/4"', 6.35, "in"),
        ("3/8 in", 9.525, "in"),
        ("1-1/2 in", 38.1, "in"),
        ("1 1/2 in", 38.1, "in"),
        ("3/4 pouce", 19.05, "in"),
        ("3.2 cm", 32.0, "cm"),
        ("0.05 m", 50.0, "m"),
        ("250 µm", 0.25, "µm"),
        ("500 um", 0.5, "µm"),
        ("25,4 mm", 25.4, "mm"),
        ("10,0 mm", 10.0, "mm"),
        ("-5.0 mm", -5.0, "mm"),
    ],
)
def test_parse_length_to_mm_nist_conversions(
    raw: str, expected_mm: float, expected_orig_unit: str
) -> None:
    res = parse_length_to_mm(raw)
    assert res is not None
    nom_mm, tol_mm, traces = res
    assert nom_mm == pytest.approx(expected_mm, rel=1e-9)
    assert tol_mm is None
    assert len(traces) == 1
    assert traces[0].original_unit == expected_orig_unit
    assert traces[0].si_unit == "mm"
    assert traces[0].si_value == pytest.approx(expected_mm, rel=1e-9)


def test_parse_length_to_mm_inline_tolerance() -> None:
    res = parse_length_to_mm("18.0 mm ±0.05 mm")
    assert res is not None
    nom_mm, tol_mm, traces = res
    assert nom_mm == pytest.approx(18.0)
    assert tol_mm == pytest.approx(0.05)
    assert len(traces) == 2
    assert traces[0].field == "nominal_dim"
    assert traces[1].field == "tolerance"

    # Also verify shared trailing unit (e.g. "18.0 ± 0.05 mm")
    res_shared = parse_length_to_mm("18.0 ± 0.05 mm")
    assert res_shared is not None
    assert res_shared[0] == pytest.approx(18.0)
    assert res_shared[1] == pytest.approx(0.05)


@pytest.mark.parametrize(
    ("raw", "expected_mm"),
    [
        ("±0.025 mm", 0.025),
        ("±0,03 mm", 0.03),
        ("±0.001 in", 0.0254),
        ("+/- 0.08 in", 2.032),
        ("+-0.05 mm", 0.05),
    ],
)
def test_parse_tolerance_to_mm(raw: str, expected_mm: float) -> None:
    res = parse_tolerance_to_mm(raw)
    assert res is not None
    tol_mm, trace = res
    assert tol_mm == pytest.approx(expected_mm, rel=1e-9)
    assert trace.si_unit == "mm"


@pytest.mark.parametrize(
    ("raw", "expected_mpa"),
    [
        ("3000 psi", 3000.0 * PSI_TO_MPA),
        ("5000 PSI", 5000.0 * PSI_TO_MPA),
        ("300 bar", 30.0),
        ("2200 kPa", 2.2),
        ("14,5 MPa", 14.5),
        ("32 MPa", 32.0),
        ("4000 lbf/in2", 4000.0 * PSI_TO_MPA),
        ("1000000 Pa", 1.0),
        ("0.5 GPa", 500.0),
        ("10 ksi", 10.0 * PSI_TO_MPA * 1000.0),
        ("-15 bar", -1.5),
    ],
)
def test_parse_pressure_to_mpa(raw: str, expected_mpa: float) -> None:
    res = parse_pressure_to_mpa(raw)
    assert res is not None
    mpa, trace = res
    assert mpa == pytest.approx(expected_mpa, rel=1e-9)
    assert trace.si_unit == "MPa"


@pytest.mark.parametrize(
    ("raw", "expected_min_c", "expected_max_c"),
    [
        ("-65 °F to 275 °F", (-65.0 - 32.0) * 5.0 / 9.0, 135.0),
        ("-65 °F to 800 °F", (-65.0 - 32.0) * 5.0 / 9.0, (800.0 - 32.0) * 5.0 / 9.0),
        ("210 K to 473 K", 210.0 - KELVIN_OFFSET, 473.0 - KELVIN_OFFSET),
        ("-60 °C à 220 °C", -60.0, 220.0),
        ("-40°C / +150°C", -40.0, 150.0),
        ("200 C to 50 C", 200.0, 50.0),
        ("-300 °C to 120 °C", -300.0, 120.0),
    ],
)
def test_parse_temp_range_to_c(
    raw: str, expected_min_c: float, expected_max_c: float
) -> None:
    res = parse_temp_range_to_c(raw)
    assert res is not None
    min_c, max_c, traces = res
    assert min_c == pytest.approx(expected_min_c, rel=1e-7)
    assert max_c == pytest.approx(expected_max_c, rel=1e-7)
    assert len(traces) == 2
    assert traces[0].si_unit == "°C"
    assert traces[1].si_unit == "°C"


@pytest.mark.parametrize(
    ("raw", "expected_kg"),
    [
        ("14.5 g", 0.0145),
        ("1.45 kg", 1.45),
        ("0.65 oz", 0.65 * OZ_TO_KG),
        ("2.4 lb", 2.4 * LB_TO_KG),
        ("0.18 lb", 0.18 * LB_TO_KG),
        ("500 mg", 0.0005),
    ],
)
def test_parse_mass_to_kg(raw: str, expected_kg: float) -> None:
    res = parse_mass_to_kg(raw)
    assert res is not None
    kg, trace = res
    assert kg == pytest.approx(round(expected_kg, 9), abs=1e-9)
    assert trace.si_unit == "kg"


@pytest.mark.parametrize(
    ("raw", "expected_days"),
    [
        ("3 weeks", 21),
        ("2 semaines", 14),
        ("14 days", 14),
        ("10 jours", 10),
        ("2 mois", 60),
        ("14", 14),
    ],
)
def test_parse_lead_time_days(raw: str, expected_days: int) -> None:
    assert parse_lead_time_days(raw) == expected_days


def test_parse_length_range_and_temp_threshold_and_price() -> None:
    assert parse_length_range_to_mm("0.5 in to 1.5 in") == pytest.approx((12.7, 38.1))
    assert parse_temp_threshold_to_c("-65°F to 275°F") == pytest.approx(
        (-53.888888889, 135.0)
    )
    assert parse_temp_threshold_to_c("<= 150 °C") == pytest.approx((150.0, None))
    assert parse_temp_threshold_to_c(">= -55 °C") == pytest.approx((None, -55.0))
    assert parse_price_usd("$1,250.50 USD") == pytest.approx(1250.5)


@pytest.mark.parametrize(
    ("parser_fn", "bad_input"),
    [
        (parse_length_to_mm, "approx half inch?"),
        (parse_length_to_mm, "12.5 lightyears"),
        (parse_tolerance_to_mm, "±"),
        (parse_tolerance_to_mm, "tight tolerance"),
        (parse_pressure_to_mpa, "high pressure"),
        (parse_pressure_to_mpa, "3000"),
        (parse_temp_range_to_c, "ambient"),
        (parse_mass_to_kg, "heavy"),
        (parse_lead_time_days, "two weeks"),
        (parse_length_range_to_mm, "10 mm"),
    ],
)
def test_unparseable_inputs_raise_unit_parse_error(
    parser_fn: object, bad_input: str
) -> None:
    with pytest.raises(UnitParseError):
        parser_fn(bad_input)  # type: ignore[operator]
