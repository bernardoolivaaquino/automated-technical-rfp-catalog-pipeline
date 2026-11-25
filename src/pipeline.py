"""End-to-end CLI and programmatic orchestrator for the RFP compliance pipeline."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.compliance_matcher import match_requirements
from src.doc_generator import (
    export_erp_master_data,
    generate_latex_datasheet,
    generate_markdown_report,
)
from src.models import (
    ComplianceStatus,
    PipelineMetrics,
    PipelineReport,
)
from src.parser import (
    normalize_record,
    parse_rfp_markdown,
    parse_supplier_csv,
    parse_supplier_pdf,
)
from src.validator import validate_catalog

REPO_ROOT = Path(__file__).resolve().parent.parent

app = typer.Typer(
    name="rfp-pipeline",
    help="Deterministic Aerospace & Industrial Catalog Normalization and RFP Compliance Pipeline.",
    add_completion=False,
)


def run_pipeline(
    csv_path: Path = REPO_ROOT / "data" / "raw" / "supplier_catalog_dirty.csv",
    pdf_path: Path | None = REPO_ROOT / "data" / "raw" / "supplier_spec_sheet_dirty.pdf",
    rfp_path: Path = REPO_ROOT / "data" / "raw" / "rfp_requirements_sample.md",
    processed_dir: Path = REPO_ROOT / "data" / "processed",
    template_dir: Path = REPO_ROOT / "templates",
    output_dir: Path = REPO_ROOT / "output",
) -> PipelineReport:
    """Execute ingestion, SI normalization, validation, RFP matching, and document export."""
    started = time.perf_counter()

    csv_records = parse_supplier_csv(csv_path) if csv_path.exists() else []
    pdf_records = (
        parse_supplier_pdf(pdf_path)
        if pdf_path is not None and pdf_path.exists()
        else []
    )
    raw_records = [*csv_records, *pdf_records]

    normalized = [normalize_record(record) for record in raw_records]
    validated = validate_catalog(normalized)

    rfp_id, rfp_title, requirements = parse_rfp_markdown(rfp_path)
    compliance_results = match_requirements(requirements, validated)

    valid_count = sum(1 for c in validated if c.validation_status == "VALID")
    warning_count = sum(
        1 for c in validated if c.validation_status == "VALID_WITH_WARNINGS"
    )
    quarantined_count = sum(
        1 for c in validated if c.validation_status == "QUARANTINED"
    )
    total_anomalies = sum(len(c.anomalies) for c in validated)

    compliant_count = sum(
        1
        for res in compliance_results
        if res.overall_status == ComplianceStatus.COMPLIANT
    )
    partial_count = sum(
        1
        for res in compliance_results
        if res.overall_status == ComplianceStatus.PARTIAL_COMPLIANCE
    )
    non_compliant_count = sum(
        1
        for res in compliance_results
        if res.overall_status == ComplianceStatus.NON_COMPLIANT
    )
    total_reqs = len(compliance_results)
    compliance_rate_pct = (
        round(100.0 * compliant_count / total_reqs, 1) if total_reqs > 0 else 0.0
    )

    elapsed = round(time.perf_counter() - started, 4)

    source_files = [csv_path.name]
    if pdf_path is not None and pdf_path.exists():
        source_files.append(pdf_path.name)
    source_files.append(rfp_path.name)

    metrics = PipelineMetrics(
        total_raw_records=len(raw_records),
        csv_records=len(csv_records),
        pdf_records=len(pdf_records),
        valid_count=valid_count,
        valid_with_warnings_count=warning_count,
        quarantined_count=quarantined_count,
        total_anomalies=total_anomalies,
        total_requirements=total_reqs,
        compliant_count=compliant_count,
        partial_count=partial_count,
        non_compliant_count=non_compliant_count,
        compliance_rate_pct=compliance_rate_pct,
        execution_time_seconds=elapsed,
    )

    report = PipelineReport(
        rfp_id=rfp_id,
        rfp_title=rfp_title,
        generated_at_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        source_files=source_files,
        metrics=metrics,
        components=validated,
        compliance_results=compliance_results,
    )

    export_erp_master_data(report, processed_dir)
    generate_markdown_report(
        report, template_dir, output_dir / "rfp_compliance_report.md"
    )
    generate_latex_datasheet(
        report, template_dir, output_dir / "technical_datasheet.tex"
    )

    return report


def _render_console_summary(
    report: PipelineReport,
    processed_dir: Path,
    output_dir: Path,
) -> None:
    """Print a structured Rich execution summary to stdout."""
    console = Console()
    m = report.metrics

    console.print(
        Panel.fit(
            f"[bold cyan]{report.rfp_id}[/bold cyan] — {report.rfp_title}\n"
            f"Ingested: [bold]{m.total_raw_records}[/bold] parts "
            f"({m.csv_records} CSV + {m.pdf_records} PDF) | "
            f"Valid: [green]{m.valid_count}[/green] | "
            f"Warnings: [yellow]{m.valid_with_warnings_count}[/yellow] | "
            f"Quarantined: [red]{m.quarantined_count}[/red] | "
            f"Runtime: [bold]{m.execution_time_seconds:.4f}s[/bold]",
            title="Automated Technical RFP Catalog Pipeline",
        )
    )

    table = Table(title=f"RFP Compliance Matrix ({m.compliance_rate_pct:.1f}% Full Compliance)")
    table.add_column("REQ ID", style="bold cyan", no_wrap=True)
    table.add_column("Category", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Recommended P/N", no_wrap=True)
    table.add_column("Score", justify="right")

    for res in report.compliance_results:
        status = res.overall_status.value
        color = {
            "COMPLIANT": "green",
            "PARTIAL_COMPLIANCE": "yellow",
            "NON_COMPLIANT": "red",
        }.get(status, "white")
        best_pn = res.best_match.part_number if res.best_match else "—"
        score = f"{res.best_match.compliance_score:.1f}%" if res.best_match else "0.0%"
        table.add_row(
            res.requirement.req_id,
            res.requirement.category.value,
            f"[{color}]{status}[/{color}]",
            best_pn,
            score,
        )

    console.print(table)
    console.print(
        f"[bold]Outputs written:[/bold]\n"
        f"  - {processed_dir / 'erp_master_catalog.json'}\n"
        f"  - {processed_dir / 'erp_master_catalog.csv'}\n"
        f"  - {processed_dir / 'validation_anomalies.json'}\n"
        f"  - {output_dir / 'rfp_compliance_report.md'}\n"
        f"  - {output_dir / 'technical_datasheet.tex'}"
    )


@app.command()
def main(
    csv_path: Path = typer.Option(
        REPO_ROOT / "data" / "raw" / "supplier_catalog_dirty.csv",
        "--csv",
        help="Path to raw dirty supplier CSV catalog.",
    ),
    pdf_path: Path = typer.Option(
        REPO_ROOT / "data" / "raw" / "supplier_spec_sheet_dirty.pdf",
        "--pdf",
        help="Path to supplemental supplier spec sheet PDF.",
    ),
    rfp_path: Path = typer.Option(
        REPO_ROOT / "data" / "raw" / "rfp_requirements_sample.md",
        "--rfp",
        help="Path to bilingual RFP requirements Markdown file.",
    ),
    processed_dir: Path = typer.Option(
        REPO_ROOT / "data" / "processed",
        "--processed-dir",
        help="Directory for ERP-ready JSON/CSV outputs.",
    ),
    template_dir: Path = typer.Option(
        REPO_ROOT / "templates",
        "--template-dir",
        help="Directory containing Jinja2 Markdown and LaTeX templates.",
    ),
    output_dir: Path = typer.Option(
        REPO_ROOT / "output",
        "--output-dir",
        help="Directory for client-ready Markdown and LaTeX deliverables.",
    ),
) -> None:
    """Run the end-to-end catalog normalization, validation, and RFP compliance pipeline."""
    report = run_pipeline(
        csv_path=csv_path,
        pdf_path=pdf_path,
        rfp_path=rfp_path,
        processed_dir=processed_dir,
        template_dir=template_dir,
        output_dir=output_dir,
    )
    _render_console_summary(report, processed_dir, output_dir)


if __name__ == "__main__":
    app()
