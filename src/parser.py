"""Deterministic parsers and normalizers for CSV catalogs, PDF spec sheets, and RFP specs."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Literal

import pymupdf

from src.models import (
    AnomalyCode,
    AnomalySeverity,
    ComponentCategory,
    NormalizedComponent,
    RawSupplierRecord,
    RFPRequirement,
    ValidationAnomaly,
)
from src.unit_converter import (
    UnitParseError,
    is_missing_value,
    parse_lead_time_days,
    parse_length_range_to_mm,
    parse_length_to_mm,
    parse_mass_to_kg,
    parse_pressure_to_mpa,
    parse_price_usd,
    parse_temp_range_to_c,
    parse_temp_threshold_to_c,
    parse_tolerance_to_mm,
)

# Canonical category keyword mapping (evaluated in deterministic priority order)
_CATEGORY_RULES: tuple[tuple[ComponentCategory, tuple[str, ...]], ...] = (
    (
        ComponentCategory.FASTENER,
        (
            "fastener",
            "fixation",
            "boulonnerie",
            "visserie",
            "bolt",
            "nut",
            "screw",
            "rivet",
            "stud",
            "écrou",
            "ecrou",
            "boulon",
        ),
    ),
    (
        ComponentCategory.VALVE,
        (
            "électrovanne",
            "electrovanne",
            "valve",
            "vanne",
        ),
    ),
    (
        ComponentCategory.ALLOY,
        (
            "superalloy",
            "superalliage",
            "alliage",
            "alloy",
        ),
    ),
    (
        ComponentCategory.SEAL,
        (
            "o-ring",
            "seal",
            "joint",
            "torique",
            "étanchéité",
            "etancheite",
        ),
    ),
    (
        ComponentCategory.FITTING,
        (
            "fitting",
            "raccord",
            "connector",
        ),
    ),
    (
        ComponentCategory.ACTUATOR,
        (
            "actuator",
            "actionneur",
        ),
    ),
    (
        ComponentCategory.SENSOR,
        (
            "sensor",
            "capteur",
            "transducer",
            "sonde",
            "probe",
        ),
    ),
)

_MATERIAL_MAP: dict[str, str] = {
    "ti-6al-4v": "Ti-6Al-4V",
    "ti-6al-4v (grade 5)": "Ti-6Al-4V",
    "grade 5 titanium": "Ti-6Al-4V",
    "titane ti-6al-4v": "Ti-6Al-4V",
    "inconel 718": "Inconel 718",
    "inconel 718 (uns n07718)": "Inconel 718",
    "alloy 718": "Inconel 718",
    "inconel 625": "Inconel 625",
    "inconel 625 (uns n06625)": "Inconel 625",
    "inconel x-750": "Inconel X-750",
    "inconel x750": "Inconel X-750",
    "17-4ph": "17-4PH Stainless Steel",
    "17-4 ph": "17-4PH Stainless Steel",
    "17-4ph stainless steel": "17-4PH Stainless Steel",
    "acier 17-4ph": "17-4PH Stainless Steel",
    "316l": "316L Stainless Steel",
    "316l stainless steel": "316L Stainless Steel",
    "acier inoxydable 316l": "316L Stainless Steel",
    "a286": "A286 Stainless Steel",
    "a286 superalloy": "A286 Stainless Steel",
    "a286 stainless": "A286 Stainless Steel",
    "a286 stainless steel": "A286 Stainless Steel",
    "7075-t6": "Aluminum 7075-T6",
    "7075-t6 aluminum": "Aluminum 7075-T6",
    "aluminum 7075-t6": "Aluminum 7075-T6",
    "aluminium 7075-t6": "Aluminum 7075-T6",
    "alliage 7075-t6": "Aluminum 7075-T6",
    "2024-t3": "Aluminum 2024-T3",
    "2024-t3 aluminum": "Aluminum 2024-T3",
    "aluminum 2024-t3": "Aluminum 2024-T3",
    "alclad 2024-t3": "Aluminum 2024-T3",
    "6061-t6": "Aluminum 6061-T6",
    "6061-t6 aluminum": "Aluminum 6061-T6",
    "aluminum 6061-t6": "Aluminum 6061-T6",
    "4340 alloy steel": "4340 Alloy Steel",
    "4340 steel": "4340 Alloy Steel",
    "fluorosilicone": "Fluorosilicone (FVMQ)",
    "fvmq": "Fluorosilicone (FVMQ)",
    "fluorosilicone (fvmq)": "Fluorosilicone (FVMQ)",
    "fkm": "FKM (Viton)",
    "viton": "FKM (Viton)",
    "fkm (viton)": "FKM (Viton)",
    "viton (fkm)": "FKM (Viton)",
    "ffkm": "FFKM (Kalrez)",
    "kalrez": "FFKM (Kalrez)",
    "ffkm (kalrez)": "FFKM (Kalrez)",
    "ptfe": "PTFE",
    "teflon": "PTFE",
    "epdm": "EPDM",
    "haynes 230": "Haynes 230",
}

_FRENCH_ACCENT_RE = re.compile(r"[àâäéèêëîïôöùûüçÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ]")
_FRENCH_WORDS_RE = re.compile(
    r"\b(?:pour|avec|sans|haute|basse|acier|titane|alliage|inoxydable|vanne|"
    r"écrou|boulon|vis|rivet|joint|raccord|capteur|actionneur|barre|tôle|"
    r"voilure|longeron|carburant|kérosène|pression|température|défectueux|"
    r"coudé|torique|affleurant|autofreiné|forgée|ronde|épaisse|résistant|"
    r"spécifiée|qualifiée|traçabilité|certifiée|plage|degrés|atterrissage|"
    r"régulation|hydraulique|matière|chimique|inertie|statique|structurale|"
    r"arbre|exige|demande|requiert|nécessite|collecteurs|nervures|semaines)\b",
    re.IGNORECASE,
)

# Ordered longest-phrase-first French -> English engineering glossary
_FR_TO_EN_GLOSSARY: tuple[tuple[str, str], ...] = (
    ("vis hexagonale structurale en titane pour longeron de voilure", "titanium structural hex bolt for wing-spar"),
    ("écrou autofreiné haute température pour train d'atterrissage", "high-temperature self-locking nut for landing gear"),
    ("rivet structural affleurant alliage aluminium", "flush structural aluminum alloy rivet"),
    ("vanne de régulation hydraulique haute pression en acier", "high-pressure hydraulic control valve in steel"),
    ("vanne hydraulique sans pression nominale spécifiée", "hydraulic valve without specified nominal pressure"),
    ("barre forgée en superalliage", "forged superalloy bar"),
    ("pour arbre haute température", "for high-temperature shaft"),
    ("tôle épaisse en alliage d'aluminium", "thick aluminum alloy plate"),
    ("barre ronde en acier inoxydable", "stainless steel round bar"),
    ("barre d'alliage non certifiée sans traçabilité matière", "uncertified alloy bar without material traceability"),
    ("joint torique fluorosilicone résistant au kérosène", "kerosene-resistant fluorosilicone O-ring"),
    ("joint perfluoroélastomère haute inertie chimique", "high chemical-inertia perfluoroelastomer seal"),
    ("joint statique sans plage de température qualifiée", "static seal without qualified temperature range"),
    ("raccord hydraulique coudé 90 degrés en titane haute pression", "high-pressure titanium 90-degree elbow hydraulic fitting"),
    ("plage de température qualifiée", "qualified temperature range"),
    ("pression nominale spécifiée", "specified nominal pressure"),
    ("traçabilité matière", "material traceability"),
    ("train d'atterrissage", "landing gear"),
    ("longeron de voilure", "wing spar"),
    ("acier inoxydable", "stainless steel"),
    ("alliage d'aluminium", "aluminum alloy"),
    ("alliage aluminium", "aluminum alloy"),
    ("haute température", "high-temperature"),
    ("haute pression", "high-pressure"),
    ("haute résistance", "high-strength"),
    ("haute inertie chimique", "high chemical inertia"),
    ("sans", "without"),
    ("avec", "with"),
    ("pour", "for"),
    ("résistant au", "resistant to"),
    ("résistant", "resistant"),
    ("en titane", "titanium"),
    ("en acier", "steel"),
    ("en", "in"),
    ("de", "of"),
)

_UNCERTIFIED_TOKENS: frozenset[str] = frozenset(
    {"non certifié", "non certifie", "uncertified", "none", "n/a", "na", "tbd", "-"}
)

_PDF_BLOCK_HEADER_RE = re.compile(r"^---\s*Component Spec Block\s*#(\d+)\s*---\s*$")


def parse_supplier_csv(path: Path) -> list[RawSupplierRecord]:
    """Parse a supplier CSV catalog (UTF-8 with optional BOM) into RawSupplierRecord items."""
    records: list[RawSupplierRecord] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for idx, row in enumerate(reader, start=1):
            records.append(
                RawSupplierRecord(
                    source_file=path.name,
                    source_type="csv",
                    source_location=f"row:{idx}",
                    part_number=(row.get("part_number") or ""),
                    supplier_name=(row.get("supplier_name") or ""),
                    category_raw=(row.get("category_raw") or ""),
                    description=(row.get("description") or ""),
                    material_spec=(row.get("material_spec") or ""),
                    nominal_dim_raw=(row.get("nominal_dim_raw") or ""),
                    tolerance_raw=(row.get("tolerance_raw") or ""),
                    max_pressure_raw=(row.get("max_pressure_raw") or ""),
                    operating_temp_raw=(row.get("operating_temp_raw") or ""),
                    mass_raw=(row.get("mass_raw") or ""),
                    standards_raw=(row.get("standards_raw") or ""),
                    unit_price_usd=(row.get("unit_price_usd") or ""),
                    lead_time_days=(row.get("lead_time_days") or ""),
                )
            )
    return records


def _assign_pdf_field(fields: dict[str, str], label: str, value: str) -> None:
    key = label.strip().lower()
    val = value.strip()
    if key.startswith("part number") or "référence" in key:
        fields["part_number"] = val
    elif key.startswith("supplier") or "fournisseur" in key:
        fields["supplier_name"] = val
    elif key.startswith("category") or "catégorie" in key:
        fields["category_raw"] = val
    elif key.startswith("description"):
        fields["description"] = val
    elif key.startswith("material") or "matériau" in key:
        fields["material_spec"] = val
    elif key.startswith("nominal dimension") or "dimension nominale" in key:
        fields["nominal_dim_raw"] = val
    elif key.startswith("tolerance") or "tolérance" in key:
        fields["tolerance_raw"] = val
    elif key.startswith("max pressure") or "pression max" in key:
        fields["max_pressure_raw"] = val
    elif key.startswith("operating temp") or "température" in key:
        fields["operating_temp_raw"] = val
    elif key.startswith("mass") or key.startswith("masse"):
        fields["mass_raw"] = val
    elif key.startswith("standards") or "normes" in key:
        fields["standards_raw"] = val
    elif key.startswith("unit price") or "prix unitaire" in key:
        fields["unit_price_usd"] = val
    elif key.startswith("lead time") or "délai" in key:
        fields["lead_time_days"] = val


def parse_supplier_pdf(path: Path) -> list[RawSupplierRecord]:
    """Extract structured component spec blocks from a supplier PDF via PyMuPDF."""
    records: list[RawSupplierRecord] = []
    with pymupdf.open(path) as doc:
        current_fields: dict[str, str] | None = None
        current_page = 1
        current_block = 0

        def _flush() -> None:
            if current_fields and current_fields.get("part_number"):
                records.append(
                    RawSupplierRecord(
                        source_file=path.name,
                        source_type="pdf",
                        source_location=f"page:{current_page}:block:{current_block}",
                        **current_fields,
                    )
                )

        for page_idx, page in enumerate(doc, start=1):
            text = page.get_text("text")
            for raw_line in text.splitlines():
                line = raw_line.strip()
                if not line:
                    continue
                header_match = _PDF_BLOCK_HEADER_RE.match(line)
                if header_match:
                    _flush()
                    current_fields = {}
                    current_page = page_idx
                    current_block = int(header_match.group(1))
                    continue
                if current_fields is not None and ":" in line:
                    label, value = line.split(":", 1)
                    _assign_pdf_field(current_fields, label, value)
        _flush()

    return records


def normalize_category(raw: str, description: str = "") -> ComponentCategory:
    """Map EN/FR raw category strings to a canonical ComponentCategory enum."""
    text = raw.strip().lower()
    if text:
        for category, keywords in _CATEGORY_RULES:
            if any(kw in text for kw in keywords):
                return category
        return ComponentCategory.UNKNOWN

    desc = description.strip().lower()
    if desc:
        for category, keywords in _CATEGORY_RULES:
            if any(kw in desc for kw in keywords):
                return category
    return ComponentCategory.UNKNOWN


def normalize_material(raw: str) -> str | None:
    """Normalize EN/FR material specification variants to canonical material names."""
    if is_missing_value(raw):
        return None
    cleaned = re.sub(r"\s+", " ", raw.strip())
    key = cleaned.lower()
    if key in _MATERIAL_MAP:
        return _MATERIAL_MAP[key]

    # Secondary normalization for parenthetical grade/UNS variants
    base = re.sub(r"\s*\([^)]*\)\s*", " ", key).strip()
    if base in _MATERIAL_MAP:
        return _MATERIAL_MAP[base]
    return cleaned


def _looks_french(text: str) -> bool:
    return bool(_FRENCH_ACCENT_RE.search(text) or _FRENCH_WORDS_RE.search(text))


def _translate_fr_to_en(text: str) -> str:
    result = text.strip()
    for fr_phrase, en_phrase in _FR_TO_EN_GLOSSARY:
        pattern = re.compile(rf"(?<!\w){re.escape(fr_phrase)}(?!\w)", re.IGNORECASE)
        result = pattern.sub(en_phrase, result)
    result = re.sub(r"\s+", " ", result).strip()
    if result:
        result = result[0].upper() + result[1:]
    return result


def standardize_description_en(raw: str) -> tuple[str, Literal["en", "fr", "bilingual"]]:
    """Standardize a description to English and detect source language ('en'|'fr'|'bilingual')."""
    stripped = re.sub(r"\s+", " ", raw.strip())
    if not stripped:
        return "", "en"

    if " / " in stripped:
        parts = [p.strip() for p in stripped.split(" / ") if p.strip()]
        if len(parts) >= 2:
            fr_parts = [p for p in parts if _looks_french(p)]
            en_parts = [p for p in parts if not _looks_french(p)]
            if fr_parts and en_parts:
                return en_parts[-1], "bilingual"
            if len(parts) == 2:
                return parts[1], "bilingual"

    if _looks_french(stripped):
        return _translate_fr_to_en(stripped), "fr"

    return stripped, "en"


def normalize_standards(raw: str) -> list[str]:
    """Split, normalize, and filter certification/quality standards into canonical tokens."""
    if is_missing_value(raw):
        return []

    tokens = re.split(r"[;,/]+", raw)
    result: list[str] = []
    seen: set[str] = set()
    for tok in tokens:
        cleaned = re.sub(r"\s+", " ", tok.strip())
        if not cleaned or cleaned.lower() in _UNCERTIFIED_TOKENS:
            continue
        cleaned = re.sub(
            r"\bAS\s+9100([A-Za-z]?)\b",
            lambda m: f"AS9100{m.group(1).upper()}",
            cleaned,
            flags=re.IGNORECASE,
        )
        key = cleaned.upper()
        if key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


def normalize_record(raw: RawSupplierRecord) -> NormalizedComponent:
    """Convert a RawSupplierRecord into a NormalizedComponent with SI values and conversion traces."""
    traces = []
    anomalies: list[ValidationAnomaly] = []

    part_number = raw.part_number.strip().upper()
    supplier_name = raw.supplier_name.strip()
    category = normalize_category(raw.category_raw, raw.description)
    description_en, language_detected = standardize_description_en(raw.description)
    material_raw = raw.material_spec.strip() or None
    material_canonical = normalize_material(raw.material_spec)
    standards = normalize_standards(raw.standards_raw)

    nominal_dim_mm: float | None = None
    tolerance_mm: float | None = None
    max_pressure_mpa: float | None = None
    temp_min_c: float | None = None
    temp_max_c: float | None = None
    mass_kg: float | None = None
    unit_price_usd: float | None = None
    lead_time_days: int | None = None

    try:
        dim_res = parse_length_to_mm(raw.nominal_dim_raw, field_name="nominal_dim")
        if dim_res is not None:
            nominal_dim_mm, inline_tol, dim_traces = dim_res
            traces.extend(dim_traces)
            if inline_tol is not None:
                tolerance_mm = inline_tol
    except UnitParseError as exc:
        anomalies.append(
            ValidationAnomaly(
                code=AnomalyCode.UNPARSEABLE_UNIT,
                severity=AnomalySeverity.ERROR,
                field="nominal_dim_mm",
                raw_value=raw.nominal_dim_raw.strip() or None,
                message=f"Unparseable nominal dimension {raw.nominal_dim_raw!r}: {exc}",
            )
        )

    try:
        tol_res = parse_tolerance_to_mm(raw.tolerance_raw)
        if tol_res is not None:
            tolerance_mm, tol_trace = tol_res
            traces.append(tol_trace)
    except UnitParseError as exc:
        anomalies.append(
            ValidationAnomaly(
                code=AnomalyCode.UNPARSEABLE_UNIT,
                severity=AnomalySeverity.ERROR,
                field="tolerance_mm",
                raw_value=raw.tolerance_raw.strip() or None,
                message=f"Unparseable tolerance {raw.tolerance_raw!r}: {exc}",
            )
        )

    try:
        pres_res = parse_pressure_to_mpa(raw.max_pressure_raw)
        if pres_res is not None:
            max_pressure_mpa, pres_trace = pres_res
            traces.append(pres_trace)
    except UnitParseError as exc:
        anomalies.append(
            ValidationAnomaly(
                code=AnomalyCode.UNPARSEABLE_UNIT,
                severity=AnomalySeverity.ERROR,
                field="max_pressure_mpa",
                raw_value=raw.max_pressure_raw.strip() or None,
                message=f"Unparseable pressure {raw.max_pressure_raw!r}: {exc}",
            )
        )

    try:
        temp_res = parse_temp_range_to_c(raw.operating_temp_raw)
        if temp_res is not None:
            temp_min_c, temp_max_c, temp_traces = temp_res
            traces.extend(temp_traces)
    except UnitParseError as exc:
        anomalies.append(
            ValidationAnomaly(
                code=AnomalyCode.UNPARSEABLE_UNIT,
                severity=AnomalySeverity.ERROR,
                field="operating_temp",
                raw_value=raw.operating_temp_raw.strip() or None,
                message=f"Unparseable temperature range {raw.operating_temp_raw!r}: {exc}",
            )
        )

    try:
        mass_res = parse_mass_to_kg(raw.mass_raw)
        if mass_res is not None:
            mass_kg, mass_trace = mass_res
            traces.append(mass_trace)
    except UnitParseError as exc:
        anomalies.append(
            ValidationAnomaly(
                code=AnomalyCode.UNPARSEABLE_UNIT,
                severity=AnomalySeverity.ERROR,
                field="mass_kg",
                raw_value=raw.mass_raw.strip() or None,
                message=f"Unparseable mass {raw.mass_raw!r}: {exc}",
            )
        )

    try:
        unit_price_usd = parse_price_usd(raw.unit_price_usd)
    except UnitParseError as exc:
        anomalies.append(
            ValidationAnomaly(
                code=AnomalyCode.UNPARSEABLE_UNIT,
                severity=AnomalySeverity.ERROR,
                field="unit_price_usd",
                raw_value=raw.unit_price_usd.strip() or None,
                message=f"Unparseable unit price {raw.unit_price_usd!r}: {exc}",
            )
        )

    try:
        lead_time_days = parse_lead_time_days(raw.lead_time_days)
    except UnitParseError as exc:
        anomalies.append(
            ValidationAnomaly(
                code=AnomalyCode.UNPARSEABLE_UNIT,
                severity=AnomalySeverity.ERROR,
                field="lead_time_days",
                raw_value=raw.lead_time_days.strip() or None,
                message=f"Unparseable lead time {raw.lead_time_days!r}: {exc}",
            )
        )

    return NormalizedComponent(
        part_number=part_number,
        supplier_name=supplier_name,
        source_file=raw.source_file,
        source_type=raw.source_type,
        source_location=raw.source_location,
        category=category,
        category_raw=raw.category_raw.strip(),
        description_raw=raw.description.strip(),
        description_en=description_en,
        language_detected=language_detected,
        material_canonical=material_canonical,
        material_raw=material_raw,
        nominal_dim_mm=nominal_dim_mm,
        tolerance_mm=tolerance_mm,
        max_pressure_mpa=max_pressure_mpa,
        temp_min_c=temp_min_c,
        temp_max_c=temp_max_c,
        mass_kg=mass_kg,
        standards=standards,
        unit_price_usd=unit_price_usd,
        lead_time_days=lead_time_days,
        conversion_traces=traces,
        anomalies=anomalies,
        validation_status="VALID",
    )


def _parse_standard_groups(raw: str) -> list[list[str]]:
    if is_missing_value(raw):
        return []
    groups: list[list[str]] = []
    for and_part in raw.split(";"):
        and_part = and_part.strip()
        if not and_part:
            continue
        or_items: list[str] = []
        for item in re.split(r"\s+OR\s+", and_part, flags=re.IGNORECASE):
            cleaned = re.sub(r"\s+", " ", item.strip())
            if not cleaned or cleaned.lower() in _UNCERTIFIED_TOKENS:
                continue
            cleaned = re.sub(
                r"\bAS\s+9100([A-Za-z]?)\b",
                lambda m: f"AS9100{m.group(1).upper()}",
                cleaned,
                flags=re.IGNORECASE,
            )
            or_items.append(cleaned)
        if or_items:
            groups.append(or_items)
    return groups


def parse_rfp_markdown(path: Path) -> tuple[str, str, list[RFPRequirement]]:
    """Parse a structured EN/FR RFP Markdown file into (rfp_id, rfp_title, requirements)."""
    text = path.read_text(encoding="utf-8")

    rfp_id = ""
    rfp_title = ""
    id_match = re.search(r"^\s*-\s*\*\*RFP ID:\*\*\s*(.+)$", text, re.MULTILINE)
    if id_match:
        rfp_id = id_match.group(1).strip()
    title_match = re.search(r"^\s*-\s*\*\*Title:\*\*\s*(.+)$", text, re.MULTILINE)
    if title_match:
        rfp_title = title_match.group(1).strip()

    if not rfp_id:
        h1_match = re.search(r"^#\s+(RFP-[A-Z0-9-]+):\s*(.+)$", text, re.MULTILINE)
        if h1_match:
            rfp_id = h1_match.group(1).strip()
            if not rfp_title:
                rfp_title = h1_match.group(2).strip()

    req_header_re = re.compile(r"^###\s+(REQ-\d+):\s*(.+)$", re.MULTILINE)
    matches = list(req_header_re.finditer(text))
    requirements: list[RFPRequirement] = []

    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        block = text[start:end].strip()

        req_id = match.group(1).strip()
        title = match.group(2).strip()

        prose_lines: list[str] = []
        kv: dict[str, str] = {}
        for line in block.splitlines()[1:]:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("- ") and ":" in stripped:
                key, val = stripped[2:].split(":", 1)
                kv[key.strip().lower()] = val.strip()
            else:
                prose_lines.append(stripped)

        sample_text = f"{title}. {' '.join(prose_lines)}".strip()
        _, language = standardize_description_en(sample_text)

        category = normalize_category(kv.get("category", ""), sample_text)

        mat_raw = kv.get("material", "")
        if is_missing_value(mat_raw):
            required_materials: list[str] = []
        else:
            required_materials = [
                m.strip()
                for m in re.split(r"\s+OR\s+", mat_raw, flags=re.IGNORECASE)
                if m.strip() and not is_missing_value(m)
            ]

        dim_range = parse_length_range_to_mm(kv.get("nominal dimension", ""))
        dim_min_mm = dim_range[0] if dim_range else None
        dim_max_mm = dim_range[1] if dim_range else None

        tol_res = parse_tolerance_to_mm(kv.get("max tolerance", ""))
        max_allowed_tolerance_mm = tol_res[0] if tol_res else None

        pres_res = parse_pressure_to_mpa(kv.get("min pressure", ""))
        min_pressure_mpa = pres_res[0] if pres_res else None

        temp_min_c, temp_max_c = parse_temp_threshold_to_c(
            kv.get("operating temperature", "")
        )

        required_standard_groups = _parse_standard_groups(
            kv.get("required standards", "")
        )

        requirements.append(
            RFPRequirement(
                req_id=req_id,
                title=title,
                language=language,
                category=category,
                required_materials=required_materials,
                dim_min_mm=dim_min_mm,
                dim_max_mm=dim_max_mm,
                max_allowed_tolerance_mm=max_allowed_tolerance_mm,
                min_pressure_mpa=min_pressure_mpa,
                required_temp_min_c=temp_min_c,
                required_temp_max_c=temp_max_c,
                required_standard_groups=required_standard_groups,
                raw_text=block,
            )
        )

    return rfp_id, rfp_title, requirements
