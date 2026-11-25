"""Tests for LaTeX escaping, ERP exports, Markdown/LaTeX generation, and E2E pipeline."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import pytest

from src.doc_generator import escape_latex
from src.pipeline import run_pipeline


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, "---"),
        ("", "---"),
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
        ("±", r"$\pm$"),
        ("°C", r"\textdegree C"),
        ("°", r"\textdegree "),
        ("µ", r"$\mu$"),
        ("≥", r"$\ge$"),
        ("≤", r"$\le$"),
        ("–", "--"),
        ("—", "---"),
    ],
)
def test_escape_latex_special_characters(raw: object, expected: str) -> None:
    assert escape_latex(raw) == expected


def test_escape_latex_single_pass_no_double_escaping() -> None:
    sample = r"A\B & 50% $100 #1 _test_ {x} ~ ^ ±0.05 °C"
    escaped = escape_latex(sample)
    assert escaped == (
        r"A\textbackslash{}B \& 50\% \$100 \#1 \_test\_ \{x\} "
        r"\textasciitilde{} \textasciicircum{} $\pm$0.05 \textdegree C"
    )
    # Ensure no double-escaped backslashes like \\textbackslash
    assert r"\\" not in escaped


def _assert_latex_lint_clean(tex: str) -> None:
    """Programmatic structural and escaping lint checks for generated LaTeX."""
    stripped = tex.strip()
    assert stripped.startswith(r"\documentclass"), "LaTeX must start with \\documentclass"
    assert stripped.endswith(r"\end{document}"), "LaTeX must end with \\end{document}"

    # 1. Balanced \begin{...} / \end{...} environment nesting and counts
    env_stack: list[str] = []
    for match in re.finditer(r"\\(begin|end)\{([a-zA-Z0-9*]+)\}", tex):
        kind, env_name = match.group(1), match.group(2)
        if kind == "begin":
            env_stack.append(env_name)
        else:
            assert env_stack, f"Unmatched \\end{{{env_name}}}"
            top = env_stack.pop()
            assert top == env_name, f"Mismatched environment: \\begin{{{top}}} vs \\end{{{env_name}}}"
    assert not env_stack, f"Unclosed LaTeX environments: {env_stack}"

    # 2. Balanced { and } braces (both raw and total)
    assert tex.count("{") == tex.count("}"), "Unbalanced curly braces in LaTeX"

    # 3. Zero unescaped % and _ anywhere in document
    unescaped_percent = re.findall(r"(?<!\\)%", tex)
    assert unescaped_percent == [], f"Found unescaped % in LaTeX: {unescaped_percent}"

    unescaped_underscore = re.findall(r"(?<!\\)_", tex)
    assert unescaped_underscore == [], f"Found unescaped _ in LaTeX: {unescaped_underscore}"

    # 4. Zero unescaped & outside table environments, and consistent & counts per row inside tables
    table_pattern = re.compile(
        r"\\begin\{(tabular|longtable)\}\{([^\n]*?(?:\n[^\n]*?)*?)\}(.*?)\\end\{\1\}",
        re.DOTALL,
    )
    # Verify outside-table text has zero unescaped &
    outside_tables = table_pattern.sub("", tex)
    assert re.findall(r"(?<!\\)&", outside_tables) == [], "Found unescaped & outside table"

    # Verify table column counts per row inside each tabular/longtable
    tables = list(table_pattern.finditer(tex))
    assert len(tables) == 3, f"Expected 3 tables (summary + 2 longtables), got {len(tables)}"

    expected_ampersands_per_table = [7, 10, 6]  # 8 cols, 11 cols, 7 cols
    for idx, (table_match, expected_amps) in enumerate(
        zip(tables, expected_ampersands_per_table, strict=True)
    ):
        body = table_match.group(3)
        # Drop preamble lines of longtable/tabular rules and accumulate logical rows ending with \\
        logical_rows: list[str] = []
        current: list[str] = []
        for line in body.splitlines():
            s = line.strip()
            if not s or s.startswith(
                (
                    r"\toprule",
                    r"\midrule",
                    r"\bottomrule",
                    r"\endfirsthead",
                    r"\endhead",
                    r"\endfoot",
                    r"\endlastfoot",
                    "@{}",
                    ">",
                    "r",
                    "c",
                    "l",
                )
            ) and not current and r"&" not in s and r"\multicolumn" not in s:
                continue
            current.append(s)
            if s.endswith(r"\\"):
                logical_rows.append(" ".join(current))
                current = []

        assert logical_rows, f"Table {idx} had no logical rows"
        for row in logical_rows:
            if r"\multicolumn{" in row:
                continue
            unescaped_amps = re.findall(r"(?<!\\)&", row)
            assert len(unescaped_amps) == expected_amps, (
                f"Table {idx} row expected {expected_amps} '&', got {len(unescaped_amps)}: {row}"
            )


def test_full_e2e_pipeline_into_tmp_path(
    tmp_path: Path,
    supplier_csv_path: Path,
    supplier_pdf_path: Path,
    rfp_markdown_path: Path,
    templates_dir: Path,
) -> None:
    processed_dir = tmp_path / "processed"
    output_dir = tmp_path / "output"

    report = run_pipeline(
        csv_path=supplier_csv_path,
        pdf_path=supplier_pdf_path,
        rfp_path=rfp_markdown_path,
        processed_dir=processed_dir,
        template_dir=templates_dir,
        output_dir=output_dir,
    )

    # Verify metrics on returned PipelineReport
    assert report.rfp_id == "RFP-AERO-2026-042"
    assert report.metrics.total_raw_records == 56
    assert report.metrics.csv_records == 50
    assert report.metrics.pdf_records == 6
    assert report.metrics.valid_count == 41
    assert report.metrics.valid_with_warnings_count == 2
    assert report.metrics.quarantined_count == 13
    assert report.metrics.total_anomalies == 16
    assert report.metrics.total_requirements == 10
    assert report.metrics.compliant_count == 7
    assert report.metrics.partial_count == 2
    assert report.metrics.non_compliant_count == 1
    assert report.metrics.compliance_rate_pct == 70.0

    # Verify all 5 output files exist and are non-empty
    catalog_json_path = processed_dir / "erp_master_catalog.json"
    catalog_csv_path = processed_dir / "erp_master_catalog.csv"
    anomalies_json_path = processed_dir / "validation_anomalies.json"
    md_report_path = output_dir / "rfp_compliance_report.md"
    tex_datasheet_path = output_dir / "technical_datasheet.tex"

    for path in (
        catalog_json_path,
        catalog_csv_path,
        anomalies_json_path,
        md_report_path,
        tex_datasheet_path,
    ):
        assert path.exists(), f"Missing output artifact: {path}"
        assert path.stat().st_size > 0, f"Empty output artifact: {path}"

    # 1. Validate erp_master_catalog.json
    catalog_data = json.loads(catalog_json_path.read_text(encoding="utf-8"))
    assert catalog_data["metadata"]["rfp_id"] == "RFP-AERO-2026-042"
    assert catalog_data["metadata"]["total_components"] == 56
    assert catalog_data["metadata"]["approved_components_count"] == 43
    assert catalog_data["metadata"]["quarantined_components_count"] == 13
    assert len(catalog_data["components"]) == 56

    # 2. Validate erp_master_catalog.csv
    with catalog_csv_path.open("r", encoding="utf-8", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    assert len(csv_rows) == 56
    assert "nominal_dim_mm" in csv_rows[0]
    assert "validation_status" in csv_rows[0]

    # 3. Validate validation_anomalies.json
    anomalies_data = json.loads(anomalies_json_path.read_text(encoding="utf-8"))
    assert anomalies_data["summary"]["total_anomalies"] == 16
    assert anomalies_data["summary"]["flagged_records_count"] == 15
    assert len(anomalies_data["records"]) == 15

    # 4. Validate rfp_compliance_report.md
    md_text = md_report_path.read_text(encoding="utf-8")
    assert "RFP-AERO-2026-042" in md_text
    for i in range(1, 11):
        assert f"REQ-{i:03d}" in md_text
    assert "CRYO-SNS-999" in md_text

    # 5. Programmatic LaTeX lint checks on technical_datasheet.tex
    tex_text = tex_datasheet_path.read_text(encoding="utf-8")
    assert "RFP-AERO-2026-042" in tex_text
    _assert_latex_lint_clean(tex_text)
