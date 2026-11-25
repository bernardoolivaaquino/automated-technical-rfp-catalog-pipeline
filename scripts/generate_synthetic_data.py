"""Deterministic synthetic data generator for the technical RFP compliance pipeline.

Generates:
1. data/raw/supplier_catalog_dirty.csv (50 data rows + 1 header row)
2. data/raw/supplier_spec_sheet_dirty.pdf (6 bilingual aerospace spec blocks via PyMuPDF)
3. data/raw/rfp_requirements_sample.md (10 bilingual EN/FR RFP requirements)

Run from repository root:
    python scripts/generate_synthetic_data.py
"""

from __future__ import annotations

import csv
from pathlib import Path

import pymupdf as fitz

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"

CSV_HEADERS = [
    "part_number",
    "supplier_name",
    "category_raw",
    "description",
    "material_spec",
    "nominal_dim_raw",
    "tolerance_raw",
    "max_pressure_raw",
    "operating_temp_raw",
    "mass_raw",
    "standards_raw",
    "unit_price_usd",
    "lead_time_days",
]


def _build_csv_rows() -> list[dict[str, str]]:
    """Return exactly 50 deterministic dirty-yet-realistic supplier catalog rows."""
    rows: list[dict[str, str]] = [
        # --- FASTENERS / FIXATIONS (14 rows: 10 clean, 4 defective) ---
        {
            "part_number": "TI64-BOLT-M8",
            "supplier_name": "AeroFix Precision SA",
            "category_raw": "Fastener",
            "description": "Titanium hex head structural bolt for wing-spar attachment",
            "material_spec": "Ti-6Al-4V",
            "nominal_dim_raw": "8.0 mm",
            "tolerance_raw": "±0.025 mm",
            "max_pressure_raw": "",
            "operating_temp_raw": "-60 °C to 220 °C",
            "mass_raw": "14.5 g",
            "standards_raw": "AS9100D, AMS 4928, NASM21250",
            "unit_price_usd": "18.40",
            "lead_time_days": "14",
        },
        {
            "part_number": "TI64-BOLT-M10",
            "supplier_name": "Safran Fixations Lyon",
            "category_raw": "Fixation",
            "description": "Vis hexagonale structurale en titane pour longeron de voilure",
            "material_spec": "Ti-6Al-4V (Grade 5)",
            "nominal_dim_raw": "10,0 mm",
            "tolerance_raw": "±0,03 mm",
            "max_pressure_raw": "",
            "operating_temp_raw": "-65 °C à 200 °C",
            "mass_raw": "24.2 g",
            "standards_raw": "EN 9100, NASM21250, NADCAP",
            "unit_price_usd": "22.90",
            "lead_time_days": "2 semaines",
        },
        {
            "part_number": "NAS-6204-12",
            "supplier_name": "Pacific Aerospace Fasteners",
            "category_raw": "Aerospace Fasteners",
            "description": "Close-tolerance alloy steel shear bolt 1/4 inch shank",
            "material_spec": "4340 Alloy Steel",
            "nominal_dim_raw": '1/4"',
            "tolerance_raw": "±0.001 in",
            "max_pressure_raw": "",
            "operating_temp_raw": "-65 °F to 350 °F",
            "mass_raw": "0.65 oz",
            "standards_raw": "AS9100D, NAS6204, MIL-S-5000",
            "unit_price_usd": "9.75",
            "lead_time_days": "10",
        },
        {
            "part_number": "A286-NUT-M14",
            "supplier_name": "AéroVisserie Toulouse",
            "category_raw": "Visserie",
            "description": "Écrou autofreiné haute température pour train d'atterrissage",
            "material_spec": "A286 Superalloy",
            "nominal_dim_raw": "14.0 mm",
            "tolerance_raw": "±0.015 mm",
            "max_pressure_raw": "",
            "operating_temp_raw": "-65 °C à 420 °C",
            "mass_raw": "31.0 g",
            "standards_raw": "AS9100D, NASM25027, NADCAP",
            "unit_price_usd": "16.80",
            "lead_time_days": "3 weeks",
        },
        {
            "part_number": "INC718-STUD-38",
            "supplier_name": "Turbine Hardware Corp",
            "category_raw": "Fastener",
            "description": "Double-ended Inconel 718 turbine flange stud",
            "material_spec": "Inconel 718",
            "nominal_dim_raw": "3/8 in",
            "tolerance_raw": "±0.02 mm",
            "max_pressure_raw": "",
            "operating_temp_raw": "-55 °C to 650 °C",
            "mass_raw": "42 g",
            "standards_raw": "AS9100D, AMS 5662, NADCAP",
            "unit_price_usd": "34.50",
            "lead_time_days": "21",
        },
        {
            "part_number": "TI64-PIN-06",
            "supplier_name": "AeroFix Precision SA",
            "category_raw": "Boulonnerie",
            "description": "Goupille de cisaillement en titane / Titanium shear pin",
            "material_spec": "Ti-6Al-4V",
            "nominal_dim_raw": "6.0 mm",
            "tolerance_raw": "±0.012 mm",
            "max_pressure_raw": "",
            "operating_temp_raw": "210 K to 473 K",
            "mass_raw": "8.4 g",
            "standards_raw": "AS9100D, EN 9100, AMS 4928",
            "unit_price_usd": "12.10",
            "lead_time_days": "12",
        },
        {
            "part_number": "MS21042-L4",
            "supplier_name": "Pacific Aerospace Fasteners",
            "category_raw": "Fastener",
            "description": "Self-locking reduced hexagon aerospace nut",
            "material_spec": "A286 Stainless",
            "nominal_dim_raw": "0.25 in",
            "tolerance_raw": "±0.03 mm",
            "max_pressure_raw": "",
            "operating_temp_raw": "-65 °F to 800 °F",
            "mass_raw": "4.8 g",
            "standards_raw": "AS9100D, MS21042, NASM21042",
            "unit_price_usd": "3.45",
            "lead_time_days": "7",
        },
        {
            "part_number": "AL7075-RIV-05",
            "supplier_name": "Safran Fixations Lyon",
            "category_raw": "Fixation",
            "description": "Rivet structural affleurant alliage aluminium 7075",
            "material_spec": "7075-T6",
            "nominal_dim_raw": "4.8 mm",
            "tolerance_raw": "±0.025 mm",
            "max_pressure_raw": "",
            "operating_temp_raw": "-55 °C à 130 °C",
            "mass_raw": "2.1 g",
            "standards_raw": "EN 9100, NAS1097, ISO 9001",
            "unit_price_usd": "1.15",
            "lead_time_days": "10",
        },
        {
            "part_number": "SS316-SCREW-M6",
            "supplier_name": "EuroFasten GmbH",
            "category_raw": "Fastener",
            "description": "Corrosion-resistant socket head cap screw for avionics bay",
            "material_spec": "316L Stainless Steel",
            "nominal_dim_raw": "6,0 mm",
            "tolerance_raw": "±0.04 mm",
            "max_pressure_raw": "",
            "operating_temp_raw": "-60 °C to 260 °C",
            "mass_raw": "9.3 g",
            "standards_raw": "ISO 9001, EN 9100, DIN 912",
            "unit_price_usd": "2.60",
            "lead_time_days": "8",
        },
        {
            "part_number": "TI64-BOLT-10IN",
            "supplier_name": "Pacific Aerospace Fasteners",
            "category_raw": "Fastener",
            "description": "Imperial 1 inch structural titanium clevis bolt",
            "material_spec": "Ti-6Al-4V",
            "nominal_dim_raw": "25,4 mm",
            "tolerance_raw": "±0.03 mm",
            "max_pressure_raw": "",
            "operating_temp_raw": "-55 °C to 250 °C",
            "mass_raw": "0.18 lb",
            "standards_raw": "AS9100D, AMS 4928, NASM",
            "unit_price_usd": "44.00",
            "lead_time_days": "18",
        },
        # Defective Fastener 1: Duplicate part number (whitespace + lowercase)
        {
            "part_number": "ti64-bolt-m8 ",
            "supplier_name": "AeroFix Precision SA",
            "category_raw": "Fastener",
            "description": "Duplicate entry for titanium hex head structural bolt M8",
            "material_spec": "Ti-6Al-4V",
            "nominal_dim_raw": "8.0 mm",
            "tolerance_raw": "±0.025 mm",
            "max_pressure_raw": "",
            "operating_temp_raw": "-60 °C to 220 °C",
            "mass_raw": "14.5 g",
            "standards_raw": "AS9100D, AMS 4928",
            "unit_price_usd": "18.40",
            "lead_time_days": "14",
        },
        # Defective Fastener 2: Loose fastener tolerance (metric)
        {
            "part_number": "BAD-FST-TOL1",
            "supplier_name": "LowCost Fasteners Ltd",
            "category_raw": "Fastener",
            "description": "Unfinished structural bolt with excessive dimensional play",
            "material_spec": "4340 Alloy Steel",
            "nominal_dim_raw": "10.0 mm",
            "tolerance_raw": "±0.65 mm",
            "max_pressure_raw": "",
            "operating_temp_raw": "-40 °C to 150 °C",
            "mass_raw": "28 g",
            "standards_raw": "ISO 9001",
            "unit_price_usd": "3.10",
            "lead_time_days": "5",
        },
        # Defective Fastener 3: Loose fastener tolerance (imperial)
        {
            "part_number": "BAD-FST-TOL2",
            "supplier_name": "LowCost Fasteners Ltd",
            "category_raw": "Fixation",
            "description": "Boulon hors tolérance aéronautique / Out-of-spec imperial bolt",
            "material_spec": "316L Stainless Steel",
            "nominal_dim_raw": '1/2"',
            "tolerance_raw": "±0.08 in",
            "max_pressure_raw": "",
            "operating_temp_raw": "-40 °C to 180 °C",
            "mass_raw": "1.2 oz",
            "standards_raw": "ISO 9001",
            "unit_price_usd": "4.20",
            "lead_time_days": "6",
        },
        # Defective Fastener 4: Negative dimension
        {
            "part_number": "BAD-FST-NEG",
            "supplier_name": "AéroVisserie Toulouse",
            "category_raw": "Fastener",
            "description": "Corrupted CAD import fastener with negative diameter",
            "material_spec": "Ti-6Al-4V",
            "nominal_dim_raw": "-5.0 mm",
            "tolerance_raw": "±0.02 mm",
            "max_pressure_raw": "",
            "operating_temp_raw": "-55 °C to 200 °C",
            "mass_raw": "11.0 g",
            "standards_raw": "AS9100D",
            "unit_price_usd": "15.00",
            "lead_time_days": "14",
        },
        # --- VALVES / VANNES (12 rows: 8 clean, 4 defective) ---
        {
            "part_number": "VLV-174PH-25",
            "supplier_name": "HydraFlow Aerospace",
            "category_raw": "Hydraulic Valve",
            "description": "High-pressure proportional hydraulic control valve 25.4 mm bore",
            "material_spec": "17-4PH Stainless Steel",
            "nominal_dim_raw": "25,4 mm",
            "tolerance_raw": "±0.04 mm",
            "max_pressure_raw": "3500 psi",
            "operating_temp_raw": "-55 °C to 150 °C",
            "mass_raw": "1.12 kg",
            "standards_raw": "AS9100D, ISO 9001, ARP490",
            "unit_price_usd": "890.00",
            "lead_time_days": "28",
        },
        {
            "part_number": "VLV-FR-3000",
            "supplier_name": "MécaFluide Bordeaux",
            "category_raw": "Vanne",
            "description": "Vanne de régulation hydraulique haute pression en acier 17-4PH",
            "material_spec": "17-4PH",
            "nominal_dim_raw": "1.0 in",
            "tolerance_raw": "±0.05 mm",
            "max_pressure_raw": "24,0 MPa",
            "operating_temp_raw": "-65 °F to 300 °F",
            "mass_raw": "2.4 lb",
            "standards_raw": "EN 9100, ISO 9001, NADCAP",
            "unit_price_usd": "945.00",
            "lead_time_days": "4 semaines",
        },
        {
            "part_number": "VLV-CHK-19",
            "supplier_name": "HydraFlow Aerospace",
            "category_raw": "Check Valve",
            "description": "Inline aerospace hydraulic check valve 3/4 inch port",
            "material_spec": "316L Stainless Steel",
            "nominal_dim_raw": "3/4 in",
            "tolerance_raw": "±0.03 mm",
            "max_pressure_raw": "300 bar",
            "operating_temp_raw": "-54 °C to 135 °C",
            "mass_raw": "420 g",
            "standards_raw": "AS9100D, AS4395, NADCAP",
            "unit_price_usd": "315.00",
            "lead_time_days": "16",
        },
        {
            "part_number": "VLV-SOL-12",
            "supplier_name": "MécaFluide Bordeaux",
            "category_raw": "Électrovanne",
            "description": "Électrovanne carburant basse fuite / Low-leakage fuel solenoid valve",
            "material_spec": "Inconel 718",
            "nominal_dim_raw": "12.7 mm",
            "tolerance_raw": "±0.025 mm",
            "max_pressure_raw": "14,5 MPa",
            "operating_temp_raw": "-55 °C à 210 °C",
            "mass_raw": "680 g",
            "standards_raw": "AS9100D, EN 9100, DO-160G",
            "unit_price_usd": "1120.00",
            "lead_time_days": "30",
        },
        {
            "part_number": "VLV-REL-5000",
            "supplier_name": "Valcor Flight Systems",
            "category_raw": "Valve",
            "description": "High-pressure hydraulic relief valve rated to 5000 PSI",
            "material_spec": "17-4PH Stainless Steel",
            "nominal_dim_raw": "19.05 mm",
            "tolerance_raw": "±0.035 mm",
            "max_pressure_raw": "5000 PSI",
            "operating_temp_raw": "-65 °F to 275 °F",
            "mass_raw": "0.85 kg",
            "standards_raw": "AS9100D, MIL-PRF-5523, ISO 9001",
            "unit_price_usd": "760.00",
            "lead_time_days": "21",
        },
        {
            "part_number": "VLV-PNU-32",
            "supplier_name": "Valcor Flight Systems",
            "category_raw": "Valve",
            "description": "Pneumatic bleed-air butterfly shutoff valve",
            "material_spec": "Inconel 625",
            "nominal_dim_raw": "3.2 cm",
            "tolerance_raw": "±0.06 mm",
            "max_pressure_raw": "2200 kPa",
            "operating_temp_raw": "218 K to 573 K",
            "mass_raw": "1.65 kg",
            "standards_raw": "AS9100D, AMS 5599, NADCAP",
            "unit_price_usd": "1480.00",
            "lead_time_days": "35",
        },
        {
            "part_number": "VLV-MAN-08",
            "supplier_name": "HydraFlow Aerospace",
            "category_raw": "Valve",
            "description": "Compact manual bleed valve with imperial pressure rating",
            "material_spec": "316L",
            "nominal_dim_raw": "8.0 mm",
            "tolerance_raw": "±0.03 mm",
            "max_pressure_raw": "4000 lbf/in2",
            "operating_temp_raw": "-50 °C to 180 °C",
            "mass_raw": "195 g",
            "standards_raw": "AS9100D, ISO 9001",
            "unit_price_usd": "210.00",
            "lead_time_days": "14",
        },
        {
            "part_number": "VLV-BLEED-320",
            "supplier_name": "Turbine Hardware Corp",
            "category_raw": "Vanne",
            "description": "Vanne d'isolement air prélevé / Bleed-air isolation valve 32 MPa",
            "material_spec": "Inconel 718",
            "nominal_dim_raw": "30.0 mm",
            "tolerance_raw": "±0.04 mm",
            "max_pressure_raw": "32 MPa",
            "operating_temp_raw": "-55 °C to 320 °C",
            "mass_raw": "2.1 kg",
            "standards_raw": "AS9100D, NADCAP, EN 9100",
            "unit_price_usd": "1950.00",
            "lead_time_days": "42",
        },
        # Defective Valve 1: Unrated valve (missing pressure)
        {
            "part_number": "BAD-VLV-NOPRES",
            "supplier_name": "MécaFluide Bordeaux",
            "category_raw": "Vanne",
            "description": "Vanne hydraulique sans pression nominale spécifiée",
            "material_spec": "316L Stainless Steel",
            "nominal_dim_raw": "20.0 mm",
            "tolerance_raw": "±0.05 mm",
            "max_pressure_raw": "",
            "operating_temp_raw": "-40 °C to 140 °C",
            "mass_raw": "780 g",
            "standards_raw": "AS9100D",
            "unit_price_usd": "490.00",
            "lead_time_days": "20",
        },
        # Defective Valve 2: Negative pressure
        {
            "part_number": "BAD-VLV-NEGPRES",
            "supplier_name": "Valcor Flight Systems",
            "category_raw": "Valve",
            "description": "Hydraulic shuttle valve with corrupted negative pressure rating",
            "material_spec": "17-4PH",
            "nominal_dim_raw": "16.0 mm",
            "tolerance_raw": "±0.04 mm",
            "max_pressure_raw": "-15 bar",
            "operating_temp_raw": "-55 °C to 150 °C",
            "mass_raw": "520 g",
            "standards_raw": "AS9100D, ISO 9001",
            "unit_price_usd": "410.00",
            "lead_time_days": "18",
        },
        # Defective Valve 3: Unparseable pressure string
        {
            "part_number": "BAD-VLV-UNPARSE",
            "supplier_name": "LowCost Fasteners Ltd",
            "category_raw": "Valve",
            "description": "Auxiliary valve with non-numeric pressure specification",
            "material_spec": "316L",
            "nominal_dim_raw": "12.0 mm",
            "tolerance_raw": "±0.05 mm",
            "max_pressure_raw": "high pressure",
            "operating_temp_raw": "-30 °C to 120 °C",
            "mass_raw": "350 g",
            "standards_raw": "ISO 9001",
            "unit_price_usd": "180.00",
            "lead_time_days": "15",
        },
        # Defective Valve 4: Inverted temperature range
        {
            "part_number": "BAD-VLV-INVTEMP",
            "supplier_name": "HydraFlow Aerospace",
            "category_raw": "Hydraulic Valve",
            "description": "Shutoff valve with inverted min/max operating temperatures",
            "material_spec": "17-4PH Stainless Steel",
            "nominal_dim_raw": "22.0 mm",
            "tolerance_raw": "±0.04 mm",
            "max_pressure_raw": "25 MPa",
            "operating_temp_raw": "200 C to 50 C",
            "mass_raw": "910 g",
            "standards_raw": "AS9100D, ISO 9001",
            "unit_price_usd": "640.00",
            "lead_time_days": "25",
        },
        # --- ALLOYS / ALLIAGES (10 rows: 8 clean, 2 defective) ---
        {
            "part_number": "INC718-BAR-25",
            "supplier_name": "Aubert & Duval Alloys",
            "category_raw": "Superalloy",
            "description": "Precipitation-hardened Inconel 718 turbine shaft bar stock",
            "material_spec": "Inconel 718",
            "nominal_dim_raw": "25.4 mm",
            "tolerance_raw": "±0.05 mm",
            "max_pressure_raw": "",
            "operating_temp_raw": "-100 °C to 700 °C",
            "mass_raw": "3.85 kg",
            "standards_raw": "AS9100D, AMS 5662, NADCAP",
            "unit_price_usd": "420.00",
            "lead_time_days": "21",
        },
        {
            "part_number": "INC718-BAR-40",
            "supplier_name": "Special Metals Aerospace",
            "category_raw": "Alliage",
            "description": "Barre forgée en superalliage Inconel 718 pour arbre haute température",
            "material_spec": "Inconel 718 (UNS N07718)",
            "nominal_dim_raw": "4.0 cm",
            "tolerance_raw": "±0.08 mm",
            "max_pressure_raw": "",
            "operating_temp_raw": "-70 °C à 680 °C",
            "mass_raw": "6.2 kg",
            "standards_raw": "EN 9100, AMS 5663, ISO 9001",
            "unit_price_usd": "615.00",
            "lead_time_days": "3 weeks",
        },
        {
            "part_number": "AL7075-PLT-16",
            "supplier_name": "Constellium Aero",
            "category_raw": "Alliage aéronautique",
            "description": "Tôle épaisse en alliage d'aluminium 7075-T6 haute résistance",
            "material_spec": "7075-T6 Aluminum",
            "nominal_dim_raw": "16.0 mm",
            "tolerance_raw": "±0.08 mm",
            "max_pressure_raw": "",
            "operating_temp_raw": "-65 °C à 160 °C",
            "mass_raw": "4.48 kg",
            "standards_raw": "AS9100D, AMS 4045, NADCAP",
            "unit_price_usd": "185.00",
            "lead_time_days": "12",
        },
        {
            "part_number": "TI64-BIL-50",
            "supplier_name": "Aubert & Duval Alloys",
            "category_raw": "Alloy",
            "description": "Forged Ti-6Al-4V aerospace structural billet",
            "material_spec": "Ti-6Al-4V",
            "nominal_dim_raw": "0.05 m",
            "tolerance_raw": "±0.10 mm",
            "max_pressure_raw": "",
            "operating_temp_raw": "-60 °C to 350 °C",
            "mass_raw": "5.5 lb",
            "standards_raw": "AS9100D, AMS 4928, EN 9100",
            "unit_price_usd": "540.00",
            "lead_time_days": "25",
        },
        {
            "part_number": "AL2024-SH-03",
            "supplier_name": "Constellium Aero",
            "category_raw": "Alloy",
            "description": "Alclad 2024-T3 fuselage skin sheet 3.2 mm gauge",
            "material_spec": "2024-T3 Aluminum",
            "nominal_dim_raw": "3.2 mm",
            "tolerance_raw": "±0.05 mm",
            "max_pressure_raw": "",
            "operating_temp_raw": "-65 °F to 250 °F",
            "mass_raw": "1.9 kg",
            "standards_raw": "AS9100D, AMS 4041, NADCAP",
            "unit_price_usd": "98.00",
            "lead_time_days": "10",
        },
        {
            "part_number": "INC625-TUB-19",
            "supplier_name": "Special Metals Aerospace",
            "category_raw": "Superalloy",
            "description": "Seamless Inconel 625 exhaust duct tubing 3/4 inch OD",
            "material_spec": "Inconel 625",
            "nominal_dim_raw": '3/4"',
            "tolerance_raw": "±0.05 mm",
            "max_pressure_raw": "",
            "operating_temp_raw": "-100 °C to 815 °C",
            "mass_raw": "1.35 kg",
            "standards_raw": "AS9100D, AMS 5581, NADCAP",
            "unit_price_usd": "375.00",
            "lead_time_days": "19",
        },
        {
            "part_number": "SS174PH-ROD-22",
            "supplier_name": "Aubert & Duval Alloys",
            "category_raw": "Alliage",
            "description": "Barre ronde en acier inoxydable 17-4PH H900",
            "material_spec": "17-4PH Stainless Steel",
            "nominal_dim_raw": "22,0 mm",
            "tolerance_raw": "±0.04 mm",
            "max_pressure_raw": "",
            "operating_temp_raw": "-55 °C à 315 °C",
            "mass_raw": "2.95 kg",
            "standards_raw": "EN 9100, AMS 5643, ISO 9001",
            "unit_price_usd": "162.00",
            "lead_time_days": "14",
        },
        {
            "part_number": "A286-BAR-30",
            "supplier_name": "Special Metals Aerospace",
            "category_raw": "Alloy",
            "description": "Heat-treated A286 iron-base superalloy round bar",
            "material_spec": "A286",
            "nominal_dim_raw": "30.0 mm",
            "tolerance_raw": "±0.06 mm",
            "max_pressure_raw": "",
            "operating_temp_raw": "200 K to 923 K",
            "mass_raw": "3.4 kg",
            "standards_raw": "AS9100D, AMS 5732, NADCAP",
            "unit_price_usd": "295.00",
            "lead_time_days": "18",
        },
        # Defective Alloy 1: Missing material
        {
            "part_number": "BAD-ALY-NOMAT",
            "supplier_name": "LowCost Fasteners Ltd",
            "category_raw": "Alloy",
            "description": "Extruded aerospace bar stock with missing alloy designation",
            "material_spec": "N/A",
            "nominal_dim_raw": "25.0 mm",
            "tolerance_raw": "±0.05 mm",
            "max_pressure_raw": "",
            "operating_temp_raw": "-50 °C to 300 °C",
            "mass_raw": "2.2 kg",
            "standards_raw": "AS9100D",
            "unit_price_usd": "110.00",
            "lead_time_days": "12",
        },
        # Defective Alloy 2: Uncertified standard
        {
            "part_number": "BAD-ALY-UNCERT",
            "supplier_name": "EuroFasten GmbH",
            "category_raw": "Alliage",
            "description": "Barre d'alliage non certifiée sans traçabilité matière",
            "material_spec": "7075-T6",
            "nominal_dim_raw": "20.0 mm",
            "tolerance_raw": "±0.05 mm",
            "max_pressure_raw": "",
            "operating_temp_raw": "-55 °C to 150 °C",
            "mass_raw": "1.8 kg",
            "standards_raw": "Non certifié",
            "unit_price_usd": "65.00",
            "lead_time_days": "7",
        },
        # --- SEALS / JOINTS (7 rows: 5 clean, 2 defective) ---
        {
            "part_number": "SEAL-FVMQ-028",
            "supplier_name": "Joints Aéronautiques SA",
            "category_raw": "Joint d'étanchéité",
            "description": "Joint torique fluorosilicone résistant au kérosène Jet-A1",
            "material_spec": "Fluorosilicone",
            "nominal_dim_raw": "28,0 mm",
            "tolerance_raw": "±0.05 mm",
            "max_pressure_raw": "14,5 MPa",
            "operating_temp_raw": "-60 °C à 210 °C",
            "mass_raw": "12.0 g",
            "standards_raw": "AS9100D, AMS-R-25988, AS568",
            "unit_price_usd": "14.50",
            "lead_time_days": "10",
        },
        {
            "part_number": "SEAL-FKM-035",
            "supplier_name": "Parker Aerospace Seals",
            "category_raw": "O-Ring Seal",
            "description": "Viton FKM high-temperature hydraulic actuator O-ring",
            "material_spec": "FKM (Viton)",
            "nominal_dim_raw": "35.0 mm",
            "tolerance_raw": "±0.06 mm",
            "max_pressure_raw": "21 MPa",
            "operating_temp_raw": "-40 °C to 220 °C",
            "mass_raw": "0.55 oz",
            "standards_raw": "AS9100D, AMS 7276, AS568",
            "unit_price_usd": "11.80",
            "lead_time_days": "9",
        },
        {
            "part_number": "SEAL-PTFE-020",
            "supplier_name": "Parker Aerospace Seals",
            "category_raw": "Seal",
            "description": "Spring-energized PTFE dynamic rod seal for flight actuators",
            "material_spec": "PTFE",
            "nominal_dim_raw": "20.0 mm",
            "tolerance_raw": "±0.03 mm",
            "max_pressure_raw": "30 MPa",
            "operating_temp_raw": "-65 °F to 450 °F",
            "mass_raw": "18.5 g",
            "standards_raw": "AS9100D, MIL-P-46191, ISO 9001",
            "unit_price_usd": "38.00",
            "lead_time_days": "15",
        },
        {
            "part_number": "SEAL-FFKM-042",
            "supplier_name": "Joints Aéronautiques SA",
            "category_raw": "Joint",
            "description": "Joint perfluoroélastomère haute inertie chimique",
            "material_spec": "FFKM (Kalrez)",
            "nominal_dim_raw": "42.0 mm",
            "tolerance_raw": "±0.05 mm",
            "max_pressure_raw": "180 bar",
            "operating_temp_raw": "-25 °C à 300 °C",
            "mass_raw": "22.0 g",
            "standards_raw": "EN 9100, AMS 7257, NADCAP",
            "unit_price_usd": "82.00",
            "lead_time_days": "2 semaines",
        },
        {
            "part_number": "SEAL-EPDM-025",
            "supplier_name": "Parker Aerospace Seals",
            "category_raw": "Seal",
            "description": "Skydrol-compatible EPDM hydraulic manifold O-ring",
            "material_spec": "EPDM",
            "nominal_dim_raw": "1.0 in",
            "tolerance_raw": "±0.04 mm",
            "max_pressure_raw": "3000 psi",
            "operating_temp_raw": "-55 °C to 150 °C",
            "mass_raw": "9.8 g",
            "standards_raw": "AS9100D, NAS1613, AS568",
            "unit_price_usd": "7.90",
            "lead_time_days": "7",
        },
        # Defective Seal 1: Missing temperature range
        {
            "part_number": "BAD-SL-NOTEMP",
            "supplier_name": "Joints Aéronautiques SA",
            "category_raw": "Joint",
            "description": "Joint statique sans plage de température qualifiée",
            "material_spec": "Fluorosilicone",
            "nominal_dim_raw": "30.0 mm",
            "tolerance_raw": "±0.05 mm",
            "max_pressure_raw": "12 MPa",
            "operating_temp_raw": "",
            "mass_raw": "14 g",
            "standards_raw": "AS9100D, AS568",
            "unit_price_usd": "10.20",
            "lead_time_days": "10",
        },
        # Defective Seal 2: Missing certification
        {
            "part_number": "BAD-SL-NOCERT",
            "supplier_name": "LowCost Fasteners Ltd",
            "category_raw": "Seal",
            "description": "Unverified elastomeric O-ring missing quality standards",
            "material_spec": "FKM (Viton)",
            "nominal_dim_raw": "24.0 mm",
            "tolerance_raw": "±0.05 mm",
            "max_pressure_raw": "15 MPa",
            "operating_temp_raw": "-30 °C to 180 °C",
            "mass_raw": "10 g",
            "standards_raw": "",
            "unit_price_usd": "4.50",
            "lead_time_days": "5",
        },
        # --- FITTINGS / SENSORS / ACTUATORS / OTHER (7 rows: 5 clean, 2 defective) ---
        {
            "part_number": "FIT-AN815-08",
            "supplier_name": "AeroFluid Connectors",
            "category_raw": "Fitting",
            "description": "Flared hydraulic union fitting 1/2 inch aluminum alloy",
            "material_spec": "7075-T6",
            "nominal_dim_raw": '1/2"',
            "tolerance_raw": "±0.03 mm",
            "max_pressure_raw": "3000 psi",
            "operating_temp_raw": "-55 °C to 135 °C",
            "mass_raw": "36 g",
            "standards_raw": "AS9100D, SAE AS4395, MS21902",
            "unit_price_usd": "29.00",
            "lead_time_days": "12",
        },
        {
            "part_number": "FIT-TI-012",
            "supplier_name": "Raccords Aviation Nice",
            "category_raw": "Raccord",
            "description": "Raccord hydraulique coudé 90 degrés en titane haute pression",
            "material_spec": "Ti-6Al-4V",
            "nominal_dim_raw": "12.0 mm",
            "tolerance_raw": "±0.025 mm",
            "max_pressure_raw": "35 MPa",
            "operating_temp_raw": "-55 °C à 205 °C",
            "mass_raw": "48 g",
            "standards_raw": "EN 9100, AS9100D, SAE AS4395",
            "unit_price_usd": "132.00",
            "lead_time_days": "18",
        },
        {
            "part_number": "SNS-TEMP-PT100",
            "supplier_name": "Avionics SenseTech",
            "category_raw": "Capteur",
            "description": "Sonde de température carburant Pt100 / Fuel RTD probe",
            "material_spec": "316L Stainless Steel",
            "nominal_dim_raw": "12.7 mm",
            "tolerance_raw": "±0.02 mm",
            "max_pressure_raw": "18 MPa",
            "operating_temp_raw": "-60 °C to 260 °C",
            "mass_raw": "95 g",
            "standards_raw": "AS9100D, DO-160G, EN 9100",
            "unit_price_usd": "415.00",
            "lead_time_days": "21",
        },
        {
            "part_number": "SNS-PRS-250",
            "supplier_name": "Avionics SenseTech",
            "category_raw": "Sensor",
            "description": "Absolute hydraulic line pressure transducer 25 MPa",
            "material_spec": "Inconel 625",
            "nominal_dim_raw": "15.0 mm",
            "tolerance_raw": "±0.02 mm",
            "max_pressure_raw": "25 MPa",
            "operating_temp_raw": "-55 °C to 175 °C",
            "mass_raw": "140 g",
            "standards_raw": "AS9100D, DO-160G, MIL-STD-810",
            "unit_price_usd": "590.00",
            "lead_time_days": "3 weeks",
        },
        {
            "part_number": "ACT-ROT-400",
            "supplier_name": "Systèmes Vol Toulouse",
            "category_raw": "Actionneur",
            "description": "Actionneur rotatif électromécanique pour volet / Flap EMA actuator",
            "material_spec": "17-4PH Stainless Steel",
            "nominal_dim_raw": "45.0 mm",
            "tolerance_raw": "±0.03 mm",
            "max_pressure_raw": "22 MPa",
            "operating_temp_raw": "-55 °C à 135 °C",
            "mass_raw": "1.85 kg",
            "standards_raw": "AS9100D, MIL-PRF-5440, EN 9100",
            "unit_price_usd": "2180.00",
            "lead_time_days": "35",
        },
        # Defective Fitting 1: Missing dimension
        {
            "part_number": "BAD-FIT-NODIM",
            "supplier_name": "AeroFluid Connectors",
            "category_raw": "Fitting",
            "description": "Bulkhead adapter tee missing nominal port dimension",
            "material_spec": "Ti-6Al-4V",
            "nominal_dim_raw": "",
            "tolerance_raw": "±0.03 mm",
            "max_pressure_raw": "28 MPa",
            "operating_temp_raw": "-55 °C to 200 °C",
            "mass_raw": "54 g",
            "standards_raw": "AS9100D, SAE AS4395",
            "unit_price_usd": "115.00",
            "lead_time_days": "15",
        },
        # Defective Other: Unknown category + unparseable dimension
        {
            "part_number": "BAD-UNK-001",
            "supplier_name": "LowCost Fasteners Ltd",
            "category_raw": "Unclassified Hardware",
            "description": "Ambiguous bracket assembly with informal sizing note",
            "material_spec": "6061-T6",
            "nominal_dim_raw": "approx half inch?",
            "tolerance_raw": "±0.05 mm",
            "max_pressure_raw": "",
            "operating_temp_raw": "-20 °C to 100 °C",
            "mass_raw": "75 g",
            "standards_raw": "ISO 9001",
            "unit_price_usd": "19.00",
            "lead_time_days": "10",
        },
    ]
    assert len(rows) == 50, f"Expected 50 CSV data rows, got {len(rows)}"
    return rows


def write_dirty_csv(output_path: Path) -> Path:
    """Write the 50-row dirty supplier CSV file in UTF-8."""
    rows = _build_csv_rows()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def _build_pdf_components() -> list[dict[str, str]]:
    """Return 6 structured bilingual aerospace spec blocks for PDF generation."""
    return [
        {
            "Part Number / Référence": "TI-FIT-038",
            "Supplier / Fournisseur": "Raccords Aviation Nice",
            "Category / Catégorie": "Fitting / Raccord hydraulique",
            "Description": "Raccord de cloison haute pression en titane / Titanium hydraulic bulkhead fitting",
            "Material / Matériau": "Ti-6Al-4V",
            "Nominal Dimension": "3/8 in",
            "Tolerance / Tolérance": "±0.025 mm",
            "Max Pressure / Pression max": "35 MPa",
            "Operating Temp / Température": "-55 °C à 205 °C",
            "Mass / Masse": "42 g",
            "Standards / Normes": "AS9100D, SAE AS4395, NADCAP",
            "Unit Price (USD)": "148.50",
            "Lead Time / Délai": "2 semaines",
        },
        {
            "Part Number / Référence": "CRYO-VLV-112",
            "Supplier / Fournisseur": "MécaFluide Bordeaux",
            "Category / Catégorie": "Valve / Vanne cryogénique",
            "Description": "Vanne d'arrêt cryogénique haute pression / Cryogenic shutoff valve",
            "Material / Matériau": "Inconel 718",
            "Nominal Dimension": "25,4 mm",
            "Tolerance / Tolérance": "±0.05 mm",
            "Max Pressure / Pression max": "24 MPa",
            "Operating Temp / Température": "77 K to 423 K",
            "Mass / Masse": "1.45 kg",
            "Standards / Normes": "AS9100D, ISO 9001, EN 9100",
            "Unit Price (USD)": "1240.00",
            "Lead Time / Délai": "4 weeks",
        },
        {
            "Part Number / Référence": "DPS-SNS-404",
            "Supplier / Fournisseur": "Avionics SenseTech",
            "Category / Catégorie": "Sensor / Capteur de pression différentielle",
            "Description": "Capteur de pression différentielle avionique / Differential pressure transducer",
            "Material / Matériau": "316L Stainless Steel",
            "Nominal Dimension": '1/2"',
            "Tolerance / Tolérance": "±0.015 mm",
            "Max Pressure / Pression max": "3500 psi",
            "Operating Temp / Température": "-65 °F to 300 °F",
            "Mass / Masse": "185 g",
            "Standards / Normes": "AS9100D, DO-160G, MIL-STD-810",
            "Unit Price (USD)": "680.00",
            "Lead Time / Délai": "21",
        },
        {
            "Part Number / Référence": "ACT-ELH-710",
            "Supplier / Fournisseur": "Systèmes Vol Toulouse",
            "Category / Catégorie": "Actuator / Actionneur électro-hydraulique",
            "Description": "Actionneur linéaire de commande de vol / Electro-hydraulic linear actuator",
            "Material / Matériau": "17-4PH Stainless Steel",
            "Nominal Dimension": "50.0 mm",
            "Tolerance / Tolérance": "±0.02 mm",
            "Max Pressure / Pression max": "280 bar",
            "Operating Temp / Température": "-54 °C to 135 °C",
            "Mass / Masse": "2.6 lb",
            "Standards / Normes": "AS9100D, MIL-PRF-5440, NADCAP",
            "Unit Price (USD)": "2450.00",
            "Lead Time / Délai": "35",
        },
        {
            "Part Number / Référence": "TI-SEAL-088",
            "Supplier / Fournisseur": "Joints Aéronautiques SA",
            "Category / Catégorie": "Seal / Joint métallique",
            "Description": "Joint métallique en C haute température / High-temp metallic C-seal",
            "Material / Matériau": "Inconel X-750",
            "Nominal Dimension": "38.1 mm",
            "Tolerance / Tolérance": "±0.03 mm",
            "Max Pressure / Pression max": "42 MPa",
            "Operating Temp / Température": "-100 °C à 480 °C",
            "Mass / Masse": "0.95 oz",
            "Standards / Normes": "AS9100D, AMS 5542, ISO 9001",
            "Unit Price (USD)": "94.00",
            "Lead Time / Délai": "10",
        },
        # Defective PDF component: temperature below absolute zero (-300 °C)
        {
            "Part Number / Référence": "CRYO-SNS-999",
            "Supplier / Fournisseur": "Avionics SenseTech",
            "Category / Catégorie": "Sensor / Capteur cryogénique",
            "Description": "Capteur thermique défectueux (température impossible) / Corrupted cryo sensor",
            "Material / Matériau": "316L Stainless Steel",
            "Nominal Dimension": "12.7 mm",
            "Tolerance / Tolérance": "±0.02 mm",
            "Max Pressure / Pression max": "20 MPa",
            "Operating Temp / Température": "-300 °C to 120 °C",
            "Mass / Masse": "110 g",
            "Standards / Normes": "AS9100D",
            "Unit Price (USD)": "510.00",
            "Lead Time / Délai": "18",
        },
    ]


def write_dirty_pdf(output_path: Path) -> Path:
    """Generate the supplemental bilingual aerospace supplier PDF using PyMuPDF."""
    components = _build_pdf_components()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = fitz.open()
    blocks_per_page = 2
    margin_x = 42
    page_width = 595
    page_height = 842

    for page_idx in range(0, len(components), blocks_per_page):
        page = doc.new_page(width=page_width, height=page_height)
        page.insert_text(
            (margin_x, 42),
            "AEROSPACE SUPPLEMENTAL SUPPLIER DATASHEET / FICHE TECHNIQUE FOURNISSEUR",
            fontname="helv",
            fontsize=11,
            color=(0.1, 0.22, 0.42),
        )
        page.insert_text(
            (margin_x, 58),
            f"Document Ref: SUP-AERO-2026-PDF | Page {page_idx // blocks_per_page + 1}",
            fontname="helv",
            fontsize=8.5,
            color=(0.35, 0.35, 0.35),
        )
        page.draw_line(
            fitz.Point(margin_x, 66),
            fitz.Point(page_width - margin_x, 66),
            color=(0.6, 0.65, 0.72),
            width=0.8,
        )

        y = 92
        page_blocks = components[page_idx : page_idx + blocks_per_page]
        for local_idx, spec in enumerate(page_blocks):
            global_num = page_idx + local_idx + 1
            page.insert_text(
                (margin_x, y),
                f"--- Component Spec Block #{global_num} ---",
                fontname="helv",
                fontsize=10,
                color=(0.12, 0.3, 0.55),
            )
            y += 20
            for label, value in spec.items():
                line = f"{label}: {value}"
                page.insert_text(
                    (margin_x, y),
                    line,
                    fontname="helv",
                    fontsize=9,
                    color=(0.08, 0.08, 0.08),
                )
                y += 17

            y += 14
            page.draw_line(
                fitz.Point(margin_x, y),
                fitz.Point(page_width - margin_x, y),
                color=(0.8, 0.82, 0.85),
                width=0.5,
            )
            y += 28

    doc.save(str(output_path))
    doc.close()
    return output_path


RFP_MARKDOWN_CONTENT = """# RFP-AERO-2026-042: Next-Generation Wing & Hydraulic Subassembly Procurement
# Appel d'offres RFP-AERO-2026-042 : Sous-ensembles voilure et hydraulique nouvelle génération

- **RFP ID:** RFP-AERO-2026-042
- **Title:** Next-Generation Wing & Hydraulic Subassembly Procurement / Approvisionnement sous-ensembles voilure et hydraulique
- **Issuing Authority:** EuroAero Propulsion & Airframe Systems
- **Languages:** Bilingual EN / FR

---

### REQ-001: Primary Wing-Spar Titanium Hex Bolts
Engineering requires corrosion-resistant Grade 5 titanium structural bolts for primary wing-spar shear and tension joints.
- Category: Fastener
- Material: Ti-6Al-4V
- Nominal Dimension: 8.0 mm to 12.0 mm
- Max Tolerance: ±0.05 mm
- Min Pressure: N/A
- Operating Temperature: -55°C to 180°C
- Required Standards: AS9100D OR EN 9100; AMS 4928 OR NASM21250

### REQ-002: Vanne de régulation hydraulique haute pression
Le circuit hydraulique principal exige une vanne de régulation qualifiée pour service sévère en pression impériale et plage thermique étendue.
- Category: Valve
- Material: 17-4PH OR Inconel 718 OR 316L
- Nominal Dimension: 0.5 in to 1.5 in
- Max Tolerance: ±0.08 mm
- Min Pressure: 3000 psi
- Operating Temperature: -65°F to 275°F
- Required Standards: AS9100D OR EN 9100; ISO 9001

### REQ-003: High-Strength Nickel Superalloy Turbine Bar Stock
Turbine shaft machining requires precipitation-hardened nickel-chromium superalloy bar stock certified to aerospace AMS specifications.
- Category: Alloy
- Material: Inconel 718
- Nominal Dimension: 20 mm to 55 mm
- Max Tolerance: ±0.10 mm
- Min Pressure: N/A
- Operating Temperature: -50°C to 650°C
- Required Standards: AS9100D OR EN 9100; AMS 5662 OR AMS 5663

### REQ-004: Joint torique fluorosilicone pour circuit carburant
L'étanchéité des collecteurs carburant Jet-A1 requiert un joint torique élastomère résistant aux hydrocarbures à haute pression.
- Category: Seal
- Material: Fluorosilicone OR FKM
- Nominal Dimension: 15 mm to 45 mm
- Max Tolerance: ±0.10 mm
- Min Pressure: 1500 psi
- Operating Temperature: -55°C to 200°C
- Required Standards: AS9100D OR EN 9100; AS568

### REQ-005: Titanium Hydraulic Bulkhead Fitting
High-pressure hydraulic bulkhead pass-throughs require precision-machined titanium fittings compatible with 5000 psi peak impulse lines.
- Category: Fitting
- Material: Ti-6Al-4V
- Nominal Dimension: 8 mm to 15 mm
- Max Tolerance: ±0.05 mm
- Min Pressure: 5000 psi
- Operating Temperature: -50°C to 180°C
- Required Standards: AS9100D; SAE AS4395

### REQ-006: Capteur de pression différentielle avionique
La surveillance des lignes hydrauliques exige un capteur différentiel qualifié DO-160G avec connectique 1/2 pouce et haute tenue en pression.
- Category: Sensor
- Material: 316L Stainless Steel OR Inconel 625
- Nominal Dimension: 10 mm to 20 mm
- Max Tolerance: ±0.05 mm
- Min Pressure: 3000 psi
- Operating Temperature: -50°C to 140°C
- Required Standards: AS9100D; DO-160G

### REQ-007: Electro-Hydraulic Flight Control Actuator
Primary flight-surface actuation requires a qualified 17-4PH electro-hydraulic linear actuator rated above 25 MPa.
- Category: Actuator
- Material: 17-4PH Stainless Steel
- Nominal Dimension: 40 mm to 60 mm
- Max Tolerance: ±0.05 mm
- Min Pressure: 25 MPa
- Operating Temperature: -50°C to 130°C
- Required Standards: AS9100D; MIL-PRF-5440

### REQ-008: Écrou autofreiné haute température pour train d'atterrissage
La boulonnerie du train d'atterrissage nécessite un écrou autofreiné superalliage résistant jusqu'à 450°C en service continu.
- Category: Fastener
- Material: A286 OR Inconel 718
- Nominal Dimension: 12 mm to 16 mm
- Max Tolerance: ±0.02 mm
- Min Pressure: N/A
- Operating Temperature: -65°C to 450°C
- Required Standards: AS9100D; NASM25027; NADCAP

### REQ-009: Ultra-High-Pressure Bleed-Air Isolation Valve
APU bleed-air manifold isolation requires an extreme-duty superalloy valve operating continuously at 65 MPa and 550°C.
- Category: Valve
- Material: Inconel 718 OR Haynes 230
- Nominal Dimension: 20 mm to 40 mm
- Max Tolerance: ±0.03 mm
- Min Pressure: 65 MPa
- Operating Temperature: -55°C to 550°C
- Required Standards: AS9100D; ARP9013; NADCAP

### REQ-010: Tôle épaisse en alliage d'aluminium haute résistance
Les nervures structurales de voilure demandent une tôle 7075-T6 usinée avec tolérance serrée de ±0.05 mm.
- Category: Alloy
- Material: 7075-T6
- Nominal Dimension: 10 mm to 30 mm
- Max Tolerance: ±0.05 mm
- Min Pressure: N/A
- Operating Temperature: -60°C to 150°C
- Required Standards: AS9100D; AMS 4045; NADCAP
"""


def write_rfp_markdown(output_path: Path) -> Path:
    """Write the bilingual EN/FR RFP requirements Markdown specification."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(RFP_MARKDOWN_CONTENT, encoding="utf-8")
    return output_path


def main() -> None:
    """Generate all synthetic raw datasets for the pipeline."""
    csv_path = write_dirty_csv(RAW_DIR / "supplier_catalog_dirty.csv")
    pdf_path = write_dirty_pdf(RAW_DIR / "supplier_spec_sheet_dirty.pdf")
    rfp_path = write_rfp_markdown(RAW_DIR / "rfp_requirements_sample.md")
    print(f"Generated CSV: {csv_path}")
    print(f"Generated PDF: {pdf_path}")
    print(f"Generated RFP: {rfp_path}")


if __name__ == "__main__":
    main()
