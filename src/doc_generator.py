"""ERP master data exporter and Jinja2 Markdown / LaTeX document generator."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.models import PipelineReport

_LATEX_ESCAPES: dict[str, str] = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "°C": r"\textdegree C",
    "°": r"\textdegree ",
    "±": r"$\pm$",
    "µ": r"$\mu$",
    "\u03bc": r"$\mu$",
    "≥": r"$\ge$",
    "≤": r"$\le$",
    "–": r"--",
    "—": r"---",
}

_LATEX_ESCAPE_PATTERN = re.compile(
    "|".join(
        re.escape(k)
        for k in sorted(_LATEX_ESCAPES.keys(), key=len, reverse=True)
    )
)

_ERP_CSV_COLUMNS: list[str] = [
    "part_number",
    "supplier_name",
    "category",
    "description_en",
    "language_detected",
    "material_canonical",
    "nominal_dim_mm",
    "tolerance_mm",
    "max_pressure_mpa",
    "temp_min_c",
    "temp_max_c",
    "mass_kg",
    "standards",
    "unit_price_usd",
    "lead_time_days",
    "validation_status",
    "anomaly_codes",
    "source_type",
    "source_location",
]


def escape_latex(value: object) -> str:
    """Deterministically escape LaTeX special characters and common SI Unicode symbols.

    Returns ``"---"`` when ``value`` is ``None``. Uses a single-pass regex ordered
    longest-key-first so backslashes and replacement braces/dollars are never
    double-escaped.
    """
    if value is None:
        return "---"
    text = str(value)
    if not text:
        return "---"
    return _LATEX_ESCAPE_PATTERN.sub(lambda m: _LATEX_ESCAPES[m.group(0)], text)


def export_erp_master_data(
    report: PipelineReport, processed_dir: Path
) -> tuple[Path, Path, Path]:
    """Export ERP-ready JSON catalog, flat SI CSV catalog, and validation anomalies JSON."""
    processed_dir.mkdir(parents=True, exist_ok=True)

    catalog_json_path = processed_dir / "erp_master_catalog.json"
    catalog_csv_path = processed_dir / "erp_master_catalog.csv"
    anomalies_json_path = processed_dir / "validation_anomalies.json"

    approved_count = sum(
        1 for c in report.components if c.validation_status != "QUARANTINED"
    )
    quarantined_count = sum(
        1 for c in report.components if c.validation_status == "QUARANTINED"
    )

    catalog_payload = {
        "metadata": {
            "rfp_id": report.rfp_id,
            "rfp_title": report.rfp_title,
            "generated_at_utc": report.generated_at_utc,
            "source_files": report.source_files,
            "total_components": len(report.components),
            "approved_components_count": approved_count,
            "quarantined_components_count": quarantined_count,
            "metrics": report.metrics.model_dump(mode="json"),
        },
        "components": [comp.model_dump(mode="json") for comp in report.components],
    }
    catalog_json_path.write_text(
        json.dumps(catalog_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    with catalog_csv_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=_ERP_CSV_COLUMNS)
        writer.writeheader()
        for comp in report.components:
            writer.writerow(
                {
                    "part_number": comp.part_number,
                    "supplier_name": comp.supplier_name,
                    "category": comp.category.value,
                    "description_en": comp.description_en,
                    "language_detected": comp.language_detected,
                    "material_canonical": comp.material_canonical or "",
                    "nominal_dim_mm": (
                        "" if comp.nominal_dim_mm is None else comp.nominal_dim_mm
                    ),
                    "tolerance_mm": (
                        "" if comp.tolerance_mm is None else comp.tolerance_mm
                    ),
                    "max_pressure_mpa": (
                        "" if comp.max_pressure_mpa is None else comp.max_pressure_mpa
                    ),
                    "temp_min_c": "" if comp.temp_min_c is None else comp.temp_min_c,
                    "temp_max_c": "" if comp.temp_max_c is None else comp.temp_max_c,
                    "mass_kg": "" if comp.mass_kg is None else comp.mass_kg,
                    "standards": "; ".join(comp.standards),
                    "unit_price_usd": (
                        "" if comp.unit_price_usd is None else comp.unit_price_usd
                    ),
                    "lead_time_days": (
                        "" if comp.lead_time_days is None else comp.lead_time_days
                    ),
                    "validation_status": comp.validation_status,
                    "anomaly_codes": "; ".join(a.code.value for a in comp.anomalies),
                    "source_type": comp.source_type,
                    "source_location": comp.source_location,
                }
            )

    code_counts: Counter[str] = Counter()
    severity_counts: Counter[str] = Counter()
    flagged_records: list[dict[str, object]] = []

    for comp in report.components:
        for anomaly in comp.anomalies:
            code_counts[anomaly.code.value] += 1
            severity_counts[anomaly.severity.value] += 1
        if comp.validation_status in ("QUARANTINED", "VALID_WITH_WARNINGS") or comp.anomalies:
            flagged_records.append(
                {
                    "part_number": comp.part_number,
                    "supplier_name": comp.supplier_name,
                    "category": comp.category.value,
                    "validation_status": comp.validation_status,
                    "source_file": comp.source_file,
                    "source_type": comp.source_type,
                    "source_location": comp.source_location,
                    "anomalies": [a.model_dump(mode="json") for a in comp.anomalies],
                }
            )

    anomalies_payload = {
        "summary": {
            "rfp_id": report.rfp_id,
            "generated_at_utc": report.generated_at_utc,
            "total_components": len(report.components),
            "valid_count": report.metrics.valid_count,
            "valid_with_warnings_count": report.metrics.valid_with_warnings_count,
            "quarantined_count": report.metrics.quarantined_count,
            "total_anomalies": report.metrics.total_anomalies,
            "flagged_records_count": len(flagged_records),
            "anomaly_counts_by_severity": dict(sorted(severity_counts.items())),
            "anomaly_counts_by_code": dict(sorted(code_counts.items())),
        },
        "records": flagged_records,
    }
    anomalies_json_path.write_text(
        json.dumps(anomalies_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return catalog_json_path, catalog_csv_path, anomalies_json_path


def generate_markdown_report(
    report: PipelineReport, template_dir: Path, output_path: Path
) -> Path:
    """Render the executive RFP compliance report in Markdown via Jinja2."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("rfp_compliance_report.md.j2")
    quarantined_components = [
        c for c in report.components if c.validation_status == "QUARANTINED"
    ]
    warning_components = [
        c for c in report.components if c.validation_status == "VALID_WITH_WARNINGS"
    ]
    rendered = template.render(
        report=report,
        quarantined_components=quarantined_components,
        warning_components=warning_components,
    )
    output_path.write_text(rendered, encoding="utf-8")
    return output_path


def generate_latex_datasheet(
    report: PipelineReport, template_dir: Path, output_path: Path
) -> Path:
    """Render the standalone LaTeX SI engineering datasheet using custom Jinja2 delimiters."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        block_start_string="\\BLOCK{",
        block_end_string="}",
        variable_start_string="\\VAR{",
        variable_end_string="}",
        comment_start_string="\\#{",
        comment_end_string="}",
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["escape_latex"] = escape_latex
    template = env.get_template("technical_datasheet.tex.j2")
    approved_components = [
        c for c in report.components if c.validation_status != "QUARANTINED"
    ]
    quarantined_components = [
        c for c in report.components if c.validation_status == "QUARANTINED"
    ]
    rendered = template.render(
        report=report,
        approved_components=approved_components,
        quarantined_components=quarantined_components,
    )
    output_path.write_text(rendered, encoding="utf-8")
    return output_path
