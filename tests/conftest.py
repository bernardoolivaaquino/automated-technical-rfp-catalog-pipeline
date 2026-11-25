"""Shared pytest fixtures and model factory helpers."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Literal

import pytest

from src.models import (
    ComponentCategory,
    NormalizedComponent,
    RawSupplierRecord,
    RFPRequirement,
    ValidationAnomaly,
)
from src.parser import (
    normalize_record,
    parse_rfp_markdown,
    parse_supplier_csv,
    parse_supplier_pdf,
)
from src.validator import validate_catalog

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Return the repository root directory."""
    return REPO_ROOT


@pytest.fixture(scope="session")
def raw_data_dir() -> Path:
    """Return the path to raw input fixtures."""
    return REPO_ROOT / "data" / "raw"


@pytest.fixture(scope="session")
def supplier_csv_path(raw_data_dir: Path) -> Path:
    """Return the path to the synthetic dirty supplier CSV catalog."""
    return raw_data_dir / "supplier_catalog_dirty.csv"


@pytest.fixture(scope="session")
def supplier_pdf_path(raw_data_dir: Path) -> Path:
    """Return the path to the synthetic bilingual supplier PDF spec sheet."""
    return raw_data_dir / "supplier_spec_sheet_dirty.pdf"


@pytest.fixture(scope="session")
def rfp_markdown_path(raw_data_dir: Path) -> Path:
    """Return the path to the synthetic bilingual RFP Markdown specification."""
    return raw_data_dir / "rfp_requirements_sample.md"


@pytest.fixture(scope="session")
def templates_dir() -> Path:
    """Return the path to Jinja2 Markdown and LaTeX templates."""
    return REPO_ROOT / "templates"


@pytest.fixture(scope="session")
def raw_csv_records(supplier_csv_path: Path) -> list[RawSupplierRecord]:
    """Parse and cache raw CSV records for the session."""
    return parse_supplier_csv(supplier_csv_path)


@pytest.fixture(scope="session")
def raw_pdf_records(supplier_pdf_path: Path) -> list[RawSupplierRecord]:
    """Parse and cache raw PDF records for the session."""
    return parse_supplier_pdf(supplier_pdf_path)


@pytest.fixture(scope="session")
def validated_catalog(
    raw_csv_records: list[RawSupplierRecord],
    raw_pdf_records: list[RawSupplierRecord],
) -> list[NormalizedComponent]:
    """Return the normalized and validated 56-component synthetic catalog."""
    normalized = [normalize_record(r) for r in [*raw_csv_records, *raw_pdf_records]]
    return validate_catalog(normalized)


@pytest.fixture(scope="session")
def parsed_rfp(rfp_markdown_path: Path) -> tuple[str, str, list[RFPRequirement]]:
    """Return parsed (rfp_id, rfp_title, requirements) from the sample RFP file."""
    return parse_rfp_markdown(rfp_markdown_path)


@pytest.fixture
def make_raw_record() -> Callable[..., RawSupplierRecord]:
    """Factory helper to build RawSupplierRecord instances with valid defaults."""

    def _factory(**overrides: object) -> RawSupplierRecord:
        defaults: dict[str, object] = {
            "source_file": "test_catalog.csv",
            "source_type": "csv",
            "source_location": "row:1",
            "part_number": "TEST-PART-001",
            "supplier_name": "AeroTest Supply",
            "category_raw": "Fastener",
            "description": "Titanium hex bolt for structural joint",
            "material_spec": "Ti-6Al-4V",
            "nominal_dim_raw": "10.0 mm",
            "tolerance_raw": "±0.02 mm",
            "max_pressure_raw": "",
            "operating_temp_raw": "-55 °C to 180 °C",
            "mass_raw": "15.0 g",
            "standards_raw": "AS9100D, AMS 4928",
            "unit_price_usd": "20.00",
            "lead_time_days": "14",
        }
        defaults.update(overrides)
        return RawSupplierRecord(**defaults)  # type: ignore[arg-type]

    return _factory


@pytest.fixture
def make_normalized_component() -> Callable[..., NormalizedComponent]:
    """Factory helper to build clean NormalizedComponent instances in SI units."""

    def _factory(
        *,
        part_number: str = "NORM-PART-001",
        supplier_name: str = "AeroTest Supply",
        source_file: str = "test_catalog.csv",
        source_type: Literal["csv", "pdf"] = "csv",
        source_location: str = "row:1",
        category: ComponentCategory = ComponentCategory.FASTENER,
        category_raw: str = "Fastener",
        description_raw: str = "Titanium structural bolt",
        description_en: str = "Titanium structural bolt",
        language_detected: Literal["en", "fr", "bilingual"] = "en",
        material_canonical: str | None = "Ti-6Al-4V",
        material_raw: str | None = "Ti-6Al-4V",
        nominal_dim_mm: float | None = 10.0,
        tolerance_mm: float | None = 0.02,
        max_pressure_mpa: float | None = None,
        temp_min_c: float | None = -60.0,
        temp_max_c: float | None = 200.0,
        mass_kg: float | None = 0.015,
        standards: list[str] | None = None,
        unit_price_usd: float | None = 20.0,
        lead_time_days: int | None = 14,
        anomalies: list[ValidationAnomaly] | None = None,
        validation_status: Literal["VALID", "VALID_WITH_WARNINGS", "QUARANTINED"] = "VALID",
    ) -> NormalizedComponent:
        return NormalizedComponent(
            part_number=part_number,
            supplier_name=supplier_name,
            source_file=source_file,
            source_type=source_type,
            source_location=source_location,
            category=category,
            category_raw=category_raw,
            description_raw=description_raw,
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
            standards=["AS9100D", "AMS 4928"] if standards is None else standards,
            unit_price_usd=unit_price_usd,
            lead_time_days=lead_time_days,
            anomalies=[] if anomalies is None else anomalies,
            validation_status=validation_status,
        )

    return _factory


@pytest.fixture
def make_rfp_requirement() -> Callable[..., RFPRequirement]:
    """Factory helper to build RFPRequirement instances for compliance tests."""

    def _factory(
        *,
        req_id: str = "REQ-TEST-001",
        title: str = "Test Structural Bolt",
        language: Literal["en", "fr", "bilingual"] = "en",
        category: ComponentCategory = ComponentCategory.FASTENER,
        required_materials: list[str] | None = None,
        dim_min_mm: float | None = 8.0,
        dim_max_mm: float | None = 12.0,
        max_allowed_tolerance_mm: float | None = 0.05,
        min_pressure_mpa: float | None = None,
        required_temp_min_c: float | None = -55.0,
        required_temp_max_c: float | None = 180.0,
        required_standard_groups: list[list[str]] | None = None,
        raw_text: str = "### REQ-TEST-001: Test Structural Bolt",
    ) -> RFPRequirement:
        return RFPRequirement(
            req_id=req_id,
            title=title,
            language=language,
            category=category,
            required_materials=(
                ["Ti-6Al-4V"] if required_materials is None else required_materials
            ),
            dim_min_mm=dim_min_mm,
            dim_max_mm=dim_max_mm,
            max_allowed_tolerance_mm=max_allowed_tolerance_mm,
            min_pressure_mpa=min_pressure_mpa,
            required_temp_min_c=required_temp_min_c,
            required_temp_max_c=required_temp_max_c,
            required_standard_groups=(
                [["AS9100D", "EN 9100"], ["AMS 4928"]]
                if required_standard_groups is None
                else required_standard_groups
            ),
            raw_text=raw_text,
        )

    return _factory
