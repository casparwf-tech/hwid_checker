"""
OD (Option Document) parser.

Reads the 'Country List' sheet and returns every shipping country.

Supported layouts
-----------------
Layout A (e.g. pujjoquince):
    Contains a header row with the word "Regions".
    col_geo     = column with "Geo" (or col_country - 1)
    col_country = column with "Regions"

Layout B (e.g. pujjolo):
    No "Regions" header row.
    Columns are detected dynamically by locating the column containing
    Geo group labels (e.g. "NA", "EMEA", "AP", "LAS").
    col_country_or_geo = detected column index
    col_marker         = column immediately to the right containing presence markers

The parser auto-detects the layout and auto-aligns column positions.
"""
from __future__ import annotations
import openpyxl
from ..models import ODCountry

_GEO_KEYWORDS = {
    "na", "emea", "ap", "las", "latam", "prc", "japan", "ww",
    "na & latam", "anz", "brazil", "caribbean",
}


def _find_country_sheet(wb: openpyxl.Workbook) -> openpyxl.worksheet.worksheet.Worksheet:
    for name in wb.sheetnames:
        if "country" in name.lower() and "list" in name.lower():
            return wb[name]
    for name in wb.sheetnames:
        if "country" in name.lower():
            return wb[name]
    raise ValueError(
        f"Cannot find a 'Country List' sheet.\n"
        f"Available sheets: {wb.sheetnames}"
    )


def _cell(row: tuple, idx: int) -> str:
    if 0 <= idx < len(row) and row[idx] is not None:
        return str(row[idx]).strip()
    return ""


def _parse_layout_a(rows: list[tuple], header_row_idx: int) -> list[ODCountry]:
    """
    Layout A: header row contains both "Geo" and "Regions" / "Country".
    Dynamically derives col_country and col_geo from the header row.
    """
    header_row = [str(v).strip().lower() if v is not None else "" for v in rows[header_row_idx]]
    col_geo = header_row.index("geo")
    if "regions" in header_row:
        col_country = header_row.index("regions")
    elif "region" in header_row:
        col_country = header_row.index("region")
    elif "country" in header_row:
        col_country = header_row.index("country")
    else:
        col_country = col_geo + 1

    countries: list[ODCountry] = []
    current_geo = ""

    for row in rows[header_row_idx + 1:]:
        if not any(row):
            continue
        geo_val = _cell(row, col_geo)
        region_val = _cell(row, col_country)

        if geo_val:
            current_geo = geo_val

        region_val = region_val.strip()
        if region_val and region_val.lower() not in ("none", "", "regions", "region"):
            countries.append(ODCountry(name=region_val, geo=current_geo))

    return countries


def _detect_layout_b_columns(rows: list[tuple]) -> tuple[int, int]:
    """
    Detect the data column and presence marker column for Layout B.
    Looks for the column containing Geo keywords (NA, EMEA, AP, etc.).
    """
    col_counts: dict[int, int] = {}
    for row in rows[:50]:
        for ci, v in enumerate(row):
            if v and str(v).strip().lower() in _GEO_KEYWORDS:
                col_counts[ci] = col_counts.get(ci, 0) + 1

    if col_counts:
        col_country = max(col_counts, key=col_counts.get)
    else:
        # Fallback: scan for first column with non-empty strings
        col_country = 1
        for row in rows[:20]:
            for ci, v in enumerate(row):
                if v and str(v).strip():
                    col_country = ci
                    break
            else:
                continue
            break

    col_marker = col_country + 1
    return col_country, col_marker


def _parse_layout_b(rows: list[tuple]) -> list[ODCountry]:
    """
    Layout B: col_country = Geo label or Country name; col_marker = presence marker.
    A row is a country if col_marker is non-empty.
    A row is a Geo section header if col_country is non-empty but col_marker is empty.
    """
    col_country, col_marker = _detect_layout_b_columns(rows)

    countries: list[ODCountry] = []
    current_geo = ""

    for row in rows:
        if not any(row):
            continue

        c1 = _cell(row, col_country)
        c2 = _cell(row, col_marker)

        if not c1 or c1.lower() in ("regions", "region", "none"):
            continue

        if c2 and c2.lower() not in ("none", "-"):
            # Country row
            countries.append(ODCountry(name=c1, geo=current_geo))
        else:
            # Geo section header (e.g. "NA", "EMEA", "AP", "LAS")
            current_geo = c1

    return countries


def parse_od(filepath: str) -> list[ODCountry]:
    """
    Parse an OD xlsx file and return all shipping countries.
    """
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    sheet = _find_country_sheet(wb)

    rows = list(sheet.iter_rows(values_only=True))
    wb.close()

    # Detect Layout A: a header row that has BOTH "geo" and "regions" (or "country")
    for i, row in enumerate(rows):
        row_strs = [str(v).strip().lower() if v is not None else "" for v in row]
        if "geo" in row_strs and ("regions" in row_strs or "region" in row_strs or "country" in row_strs):
            return _parse_layout_a(rows, header_row_idx=i)

    # Otherwise Layout B (matrix/marker style, e.g. pujjolo)
    return _parse_layout_b(rows)
