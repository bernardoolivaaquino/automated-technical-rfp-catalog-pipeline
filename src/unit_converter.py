"""Deterministic engineering unit conversion and parsing utilities (NIST/ISO)."""

from __future__ import annotations

import math
import re

from src.models import UnitConversionTrace

# Exact NIST / ISO conversion constants
INCH_TO_MM: float = 25.4
CM_TO_MM: float = 10.0
M_TO_MM: float = 1000.0
UM_TO_MM: float = 0.001

PSI_TO_MPA: float = 0.006894757293168361
BAR_TO_MPA: float = 0.1
KPA_TO_MPA: float = 0.001
PA_TO_MPA: float = 1e-6
GPA_TO_MPA: float = 1000.0
KSI_TO_MPA: float = 6.894757293168361

LB_TO_KG: float = 0.45359237
OZ_TO_KG: float = 0.028349523125

KELVIN_OFFSET: float = 273.15

G_TO_KG: float = 0.001
MG_TO_KG: float = 1e-6

_MISSING_TOKENS: frozenset[str] = frozenset(
    {"", "n/a", "na", "tbd", "none", "-", "—", "–"}
)

_MIXED_FRACTION_RE = re.compile(
    r"^([+-]?)\s*(\d+)\s*[-\s]\s*(\d+)\s*/\s*(\d+)$"
)
_SIMPLE_FRACTION_RE = re.compile(r"^([+-]?)\s*(\d+)\s*/\s*(\d+)$")
_SCIENTIFIC_OR_DECIMAL_RE = re.compile(
    r"^[+-]?[\d.,]+(?:[eE][+-]?\d+)?$"
)

_INLINE_TOL_RE = re.compile(
    r"^(?P<nom>.+?)\s*(?:±|\+/-|\+-)\s*(?P<tol>.+)$"
)

_LENGTH_UNIT_RE = re.compile(
    r"""
    ^\s*(?P<num>.+?)\s*
    (?P<unit>
        millimet(?:er|re)s? |
        centimet(?:er|re)s? |
        micromet(?:er|re)s? |
        microns? |
        m[eè]tres? |
        meters? |
        inches |
        inch |
        pouces? |
        mm |
        cm |
        [µμu]m |
        in |
        po |
        m |
        '' |
        "
    )\s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

_PRESSURE_UNIT_RE = re.compile(
    r"""
    ^\s*(?P<num>.+?)\s*
    (?P<unit>
        lbf/in\^2 |
        lbf/in² |
        lbf/in2 |
        bars? |
        psig |
        psia |
        psi |
        ksi |
        gpa |
        mpa |
        kpa |
        pa
    )\s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

_MASS_UNIT_RE = re.compile(
    r"""
    ^\s*(?P<num>.+?)\s*
    (?P<unit>
        kilogram(?:me)?s? |
        milligrams? |
        grams? |
        grammes? |
        pounds? |
        ounces? |
        kg |
        mg |
        lbs? |
        oz |
        g
    )\s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

_TEMP_ENDPOINT_RE = re.compile(
    r"""
    ^\s*(?P<num>[+-]?\s*[\d.,]+)\s*
    (?P<unit>(?:°\s*[CF]|deg\s*[CF]|[CFK]))?\s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

_TEMP_RANGE_RE = re.compile(
    r"""
    ^\s*(?P<min_part>.+?)\s*
    (?:
        \s+(?:to|à)\s+ |
        \s*/\s* |
        \s*[–—]\s* |
        \s+-\s+ |
        (?<=[CFKcfk])\s*-\s*
    )
    \s*(?P<max_part>.+?)\s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

_RANGE_SPLIT_RE = re.compile(
    r"\s+(?:to|à)\s+|\s*/\s*|\s*[–—]\s*|\s+-\s+",
    re.IGNORECASE,
)

_TEMP_SINGLE_LOWER_RE = re.compile(
    r"^\s*(?:>=|≥|>|at\s+least|min(?:imum)?)\s*(?P<expr>.+?)\s*$",
    re.IGNORECASE,
)
_TEMP_SINGLE_UPPER_RE = re.compile(
    r"^\s*(?:<=|≤|<|at\s+most|max(?:imum)?|up\s+to|jusqu['’]à)\s*(?P<expr>.+?)\s*$",
    re.IGNORECASE,
)

_LEAD_TIME_RE = re.compile(
    r"""
    ^\s*(?P<num>.+?)\s*
    (?P<unit>
        semaines? |
        weeks? |
        wks? |
        months? |
        mois |
        jours? |
        days? |
        sem |
        mo |
        w |
        d |
        j
    )?\s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)


class UnitParseError(ValueError):
    """Raised when a numeric value, unit, or range cannot be parsed deterministically."""


def is_missing_value(raw: str | None) -> bool:
    """Return True if the raw string represents an empty or missing engineering value."""
    if raw is None:
        return True
    return raw.strip().lower() in _MISSING_TOKENS


def _clean_round(value: float, digits: int = 9) -> float:
    """Round floating-point artifacts while preserving full NIST/ISO precision."""
    rounded = round(value, digits)
    return 0.0 if rounded == 0.0 else rounded


def parse_number(text: str) -> float:
    """Parse mixed fractions, simple fractions, French comma decimals, or English thousands.

    Raises UnitParseError on empty or unparseable text.
    """
    if text is None:
        raise UnitParseError("Cannot parse None as a number")
    s = text.strip()
    if not s:
        raise UnitParseError("Empty numeric string")

    if s.startswith("±"):
        s = s[1:].strip()
        if not s or s[0] in "+-±":
            raise UnitParseError(f"Unparseable number: {text!r}")

    mixed_match = _MIXED_FRACTION_RE.match(s)
    if mixed_match:
        sign_str, whole_s, num_s, den_s = mixed_match.groups()
        den = int(den_s)
        if den == 0:
            raise UnitParseError(f"Division by zero in fraction: {text!r}")
        sign = -1.0 if sign_str == "-" else 1.0
        return sign * (int(whole_s) + int(num_s) / den)

    simple_match = _SIMPLE_FRACTION_RE.match(s)
    if simple_match:
        sign_str, num_s, den_s = simple_match.groups()
        den = int(den_s)
        if den == 0:
            raise UnitParseError(f"Division by zero in fraction: {text!r}")
        sign = -1.0 if sign_str == "-" else 1.0
        return sign * (int(num_s) / den)

    # Collapse space immediately after leading sign (e.g. "- 5.0")
    if len(s) >= 2 and s[0] in "+-" and s[1] == " ":
        s = s[0] + s[1:].lstrip()

    if not _SCIENTIFIC_OR_DECIMAL_RE.match(s):
        raise UnitParseError(f"Unparseable number: {text!r}")

    # Split optional exponent so comma/dot handling applies only to the mantissa
    mantissa = s
    exponent = ""
    exp_idx = max(s.find("e"), s.find("E"))
    if exp_idx != -1:
        mantissa = s[:exp_idx]
        exponent = s[exp_idx:]

    if "," in mantissa and "." in mantissa:
        if mantissa.rfind(",") < mantissa.rfind("."):
            # English thousands comma + decimal point (e.g., 1,250.00)
            mantissa = mantissa.replace(",", "")
        else:
            # European thousands dot + decimal comma (e.g., 1.250,50)
            mantissa = mantissa.replace(".", "").replace(",", ".")
    elif "," in mantissa:
        if mantissa.count(",") > 1:
            mantissa = mantissa.replace(",", "")
        else:
            mantissa = mantissa.replace(",", ".")

    normalized = mantissa + exponent
    try:
        value = float(normalized)
    except ValueError as exc:
        raise UnitParseError(f"Unparseable number: {text!r}") from exc

    if not math.isfinite(value):
        raise UnitParseError(f"Non-finite numeric value: {text!r}")
    return value


def _length_unit_spec(unit_raw: str) -> tuple[str, float, str]:
    u = unit_raw.strip().lower()
    if u in {"mm", "millimeter", "millimeters", "millimetre", "millimetres", "millimètre", "millimètres"}:
        return "mm", 1.0, "1 mm = 1.0 mm (identity)"
    if u in {"cm", "centimeter", "centimeters", "centimetre", "centimetres", "centimètre", "centimètres"}:
        return "cm", CM_TO_MM, "1 cm = 10.0 mm"
    if u in {"m", "meter", "meters", "metre", "metres", "mètre", "mètres"}:
        return "m", M_TO_MM, "1 m = 1000.0 mm"
    if u in {"um", "µm", "μm", "micron", "microns", "micrometer", "micrometers", "micrometre", "micrometres"}:
        return "µm", UM_TO_MM, "1 µm = 0.001 mm"
    if u in {"in", "inch", "inches", '"', "''", "po", "pouce", "pouces"}:
        return "in", INCH_TO_MM, "1 in = 25.4 mm"
    raise UnitParseError(f"Unsupported length unit: {unit_raw!r}")


def _parse_single_length(
    text: str,
    field_name: str,
    raw_for_trace: str,
    default_unit: str | None = None,
) -> tuple[float, str, UnitConversionTrace]:
    match = _LENGTH_UNIT_RE.match(text)
    if match:
        num_str = match.group("num")
        unit_raw = match.group("unit")
    elif default_unit is not None:
        num_str = text.strip()
        unit_raw = default_unit
    else:
        raise UnitParseError(f"Unparseable length value: {text!r}")

    orig_val = parse_number(num_str)
    canonical_unit, factor, note = _length_unit_spec(unit_raw)
    si_val = _clean_round(orig_val * factor)
    trace = UnitConversionTrace(
        field=field_name,
        raw_value=raw_for_trace.strip(),
        original_value=orig_val,
        original_unit=canonical_unit,
        si_value=si_val,
        si_unit="mm",
        conversion_factor_note=note,
    )
    return si_val, canonical_unit, trace


def parse_length_to_mm(
    raw: str,
    field_name: str = "nominal_dim",
) -> tuple[float, float | None, list[UnitConversionTrace]] | None:
    """Parse a length string (with optional inline tolerance) to millimeters."""
    if is_missing_value(raw):
        return None

    stripped = raw.strip()
    inline_match = _INLINE_TOL_RE.match(stripped)
    if inline_match:
        nom_part = inline_match.group("nom").strip()
        tol_part = inline_match.group("tol").strip()

        tol_unit_match = _LENGTH_UNIT_RE.match(tol_part)
        nom_unit_match = _LENGTH_UNIT_RE.match(nom_part)

        inferred_unit: str | None = None
        if not nom_unit_match and tol_unit_match:
            inferred_unit = tol_unit_match.group("unit")

        nom_mm, nom_unit, nom_trace = _parse_single_length(
            nom_part,
            field_name=field_name,
            raw_for_trace=stripped,
            default_unit=inferred_unit,
        )
        tol_mm, _, tol_trace = _parse_single_length(
            tol_part,
            field_name="tolerance",
            raw_for_trace=tol_part,
            default_unit=nom_unit,
        )
        return nom_mm, tol_mm, [nom_trace, tol_trace]

    nom_mm, _, nom_trace = _parse_single_length(
        stripped,
        field_name=field_name,
        raw_for_trace=stripped,
    )
    return nom_mm, None, [nom_trace]


def parse_tolerance_to_mm(raw: str) -> tuple[float, UnitConversionTrace] | None:
    """Parse a dimensional tolerance string (e.g. '±0.025 mm', '±0.001 in') to mm."""
    if is_missing_value(raw):
        return None

    stripped = raw.strip()
    cleaned = stripped
    for prefix in ("±", "+/-", "+-"):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
            break

    if not cleaned:
        raise UnitParseError(f"Unparseable tolerance value: {raw!r}")

    tol_mm, _, trace = _parse_single_length(
        cleaned,
        field_name="tolerance",
        raw_for_trace=stripped,
    )
    return tol_mm, trace


def parse_pressure_to_mpa(raw: str) -> tuple[float, UnitConversionTrace] | None:
    """Parse a pressure rating to MPa."""
    if is_missing_value(raw):
        return None

    stripped = raw.strip()
    match = _PRESSURE_UNIT_RE.match(stripped)
    if not match:
        raise UnitParseError(f"Unparseable pressure value: {raw!r}")

    orig_val = parse_number(match.group("num"))
    unit_raw = match.group("unit").lower()

    if unit_raw == "mpa":
        unit, factor, note = "MPa", 1.0, "1 MPa = 1.0 MPa (identity)"
    elif unit_raw == "gpa":
        unit, factor, note = "GPa", GPA_TO_MPA, "1 GPa = 1000.0 MPa"
    elif unit_raw == "kpa":
        unit, factor, note = "kPa", KPA_TO_MPA, "1 kPa = 0.001 MPa"
    elif unit_raw == "pa":
        unit, factor, note = "Pa", PA_TO_MPA, "1 Pa = 1e-6 MPa"
    elif unit_raw in {"bar", "bars"}:
        unit, factor, note = "bar", BAR_TO_MPA, "1 bar = 0.1 MPa"
    elif unit_raw == "ksi":
        unit, factor, note = "ksi", KSI_TO_MPA, f"1 ksi = {KSI_TO_MPA} MPa"
    elif unit_raw in {"psi", "psig", "psia", "lbf/in2", "lbf/in^2", "lbf/in²"}:
        unit = "lbf/in2" if unit_raw.startswith("lbf") else unit_raw
        factor = PSI_TO_MPA
        note = f"1 {unit} = {PSI_TO_MPA} MPa"
    else:
        raise UnitParseError(f"Unsupported pressure unit: {raw!r}")

    si_val = _clean_round(orig_val * factor)
    trace = UnitConversionTrace(
        field="max_pressure",
        raw_value=stripped,
        original_value=orig_val,
        original_unit=unit,
        si_value=si_val,
        si_unit="MPa",
        conversion_factor_note=note,
    )
    return si_val, trace


def _normalize_temp_unit(unit_raw: str) -> str:
    cleaned = unit_raw.strip().lower().replace("°", "").replace("deg", "").strip()
    if cleaned == "c":
        return "°C"
    if cleaned == "f":
        return "°F"
    if cleaned == "k":
        return "K"
    raise UnitParseError(f"Unsupported temperature unit: {unit_raw!r}")


def _convert_temp_to_c(
    val: float,
    unit: str,
    field_name: str,
    raw_value: str,
) -> tuple[float, UnitConversionTrace]:
    if unit == "°C":
        si_val = _clean_round(val)
        note = "1 °C = 1 °C (identity)"
    elif unit == "°F":
        si_val = _clean_round((val - 32.0) * 5.0 / 9.0)
        note = "°C = (°F - 32) * 5/9"
    elif unit == "K":
        si_val = _clean_round(val - KELVIN_OFFSET)
        note = f"°C = K - {KELVIN_OFFSET}"
    else:
        raise UnitParseError(f"Unsupported temperature unit: {unit!r}")

    trace = UnitConversionTrace(
        field=field_name,
        raw_value=raw_value,
        original_value=val,
        original_unit=unit,
        si_value=si_val,
        si_unit="°C",
        conversion_factor_note=note,
    )
    return si_val, trace


def _parse_temp_endpoint(
    part: str,
    default_unit: str | None = None,
) -> tuple[float, str]:
    match = _TEMP_ENDPOINT_RE.match(part)
    if not match:
        raise UnitParseError(f"Unparseable temperature value: {part!r}")
    val = parse_number(match.group("num"))
    unit_raw = match.group("unit")
    if unit_raw:
        unit = _normalize_temp_unit(unit_raw)
    elif default_unit is not None:
        unit = default_unit
    else:
        raise UnitParseError(f"Missing temperature unit in: {part!r}")
    return val, unit


def parse_temp_range_to_c(
    raw: str,
) -> tuple[float, float, list[UnitConversionTrace]] | None:
    """Parse a temperature range string into (temp_min_c, temp_max_c, traces)."""
    if is_missing_value(raw):
        return None

    stripped = raw.strip()
    range_match = _TEMP_RANGE_RE.match(stripped)
    if not range_match:
        raise UnitParseError(f"Unparseable temperature range: {raw!r}")

    min_part = range_match.group("min_part").strip()
    max_part = range_match.group("max_part").strip()

    max_val, max_unit = _parse_temp_endpoint(max_part)
    min_val, min_unit = _parse_temp_endpoint(min_part, default_unit=max_unit)

    min_c, min_trace = _convert_temp_to_c(
        min_val, min_unit, field_name="temp_min", raw_value=min_part
    )
    max_c, max_trace = _convert_temp_to_c(
        max_val, max_unit, field_name="temp_max", raw_value=max_part
    )
    return min_c, max_c, [min_trace, max_trace]


def parse_length_range_to_mm(raw: str) -> tuple[float, float] | None:
    """Parse an RFP length range string (e.g. '8.0 mm to 12.0 mm') to (min_mm, max_mm)."""
    if is_missing_value(raw):
        return None

    stripped = raw.strip()
    parts = _RANGE_SPLIT_RE.split(stripped, maxsplit=1)
    if len(parts) != 2:
        raise UnitParseError(f"Unparseable length range: {raw!r}")

    left, right = parts[0].strip(), parts[1].strip()
    max_mm, right_unit, _ = _parse_single_length(
        right, field_name="dim_max", raw_for_trace=right
    )
    min_mm, _, _ = _parse_single_length(
        left, field_name="dim_min", raw_for_trace=left, default_unit=right_unit
    )
    return min_mm, max_mm


def parse_temp_threshold_to_c(raw: str) -> tuple[float | None, float | None]:
    """Parse an RFP temperature range or single-ended threshold into (min_c, max_c)."""
    if is_missing_value(raw):
        return None, None

    stripped = raw.strip()
    lower_match = _TEMP_SINGLE_LOWER_RE.match(stripped)
    if lower_match:
        val, unit = _parse_temp_endpoint(lower_match.group("expr"))
        temp_c, _ = _convert_temp_to_c(val, unit, "required_temp_max", stripped)
        return None, temp_c

    upper_match = _TEMP_SINGLE_UPPER_RE.match(stripped)
    if upper_match:
        val, unit = _parse_temp_endpoint(upper_match.group("expr"))
        temp_c, _ = _convert_temp_to_c(val, unit, "required_temp_min", stripped)
        return temp_c, None

    parsed_range = parse_temp_range_to_c(stripped)
    if parsed_range is None:
        return None, None
    return parsed_range[0], parsed_range[1]


def parse_mass_to_kg(raw: str) -> tuple[float, UnitConversionTrace] | None:
    """Parse a mass string (kg, g, mg, lb/lbs, oz) to kilograms."""
    if is_missing_value(raw):
        return None

    stripped = raw.strip()
    match = _MASS_UNIT_RE.match(stripped)
    if not match:
        raise UnitParseError(f"Unparseable mass value: {raw!r}")

    orig_val = parse_number(match.group("num"))
    unit_raw = match.group("unit").lower()

    if unit_raw in {"kg", "kilogram", "kilograms", "kilogramme", "kilogrammes"}:
        unit, factor, note = "kg", 1.0, "1 kg = 1.0 kg (identity)"
    elif unit_raw in {"g", "gram", "grams", "gramme", "grammes"}:
        unit, factor, note = "g", G_TO_KG, "1 g = 0.001 kg"
    elif unit_raw in {"mg", "milligram", "milligrams"}:
        unit, factor, note = "mg", MG_TO_KG, "1 mg = 1e-6 kg"
    elif unit_raw in {"lb", "lbs", "pound", "pounds"}:
        unit, factor, note = "lb", LB_TO_KG, f"1 lb = {LB_TO_KG} kg"
    elif unit_raw in {"oz", "ounce", "ounces"}:
        unit, factor, note = "oz", OZ_TO_KG, f"1 oz = {OZ_TO_KG} kg"
    else:
        raise UnitParseError(f"Unsupported mass unit: {raw!r}")

    si_val = _clean_round(orig_val * factor)
    trace = UnitConversionTrace(
        field="mass",
        raw_value=stripped,
        original_value=orig_val,
        original_unit=unit,
        si_value=si_val,
        si_unit="kg",
        conversion_factor_note=note,
    )
    return si_val, trace


def parse_price_usd(raw: str) -> float | None:
    """Parse a USD price string into a float."""
    if is_missing_value(raw):
        return None

    cleaned = raw.strip()
    cleaned = re.sub(r"(?i)(?:us\$|\$|usd)", "", cleaned).strip()
    if re.fullmatch(r"[+-]?\d{1,3}(?:,\d{3})+", cleaned):
        cleaned = cleaned.replace(",", "")
    return _clean_round(parse_number(cleaned), digits=4)


def parse_lead_time_days(raw: str) -> int | None:
    """Parse a lead-time string (days/jours, weeks/semaines, months/mois) to integer days."""
    if is_missing_value(raw):
        return None

    stripped = raw.strip()
    match = _LEAD_TIME_RE.match(stripped)
    if not match:
        raise UnitParseError(f"Unparseable lead time: {raw!r}")

    val = parse_number(match.group("num"))
    unit_raw = (match.group("unit") or "days").lower()

    if unit_raw in {"d", "day", "days", "j", "jour", "jours"}:
        mult = 1
    elif unit_raw in {"w", "wk", "wks", "week", "weeks", "sem", "semaine", "semaines"}:
        mult = 7
    elif unit_raw in {"mo", "month", "months", "mois"}:
        mult = 30
    else:
        raise UnitParseError(f"Unsupported lead time unit: {raw!r}")

    return int(round(val * mult))
