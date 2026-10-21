"""
EC Level parser.

Reads the KPL sheet from an EC Level xlsx file.

Supported layouts
-----------------
Layout A (e.g. pujjoquince):
    Row 3:  header  [Key Parts, Character, Supplier, Description, ..., LCFC PN, ...]
    Row 4:  sub-header (EVT/DVT/PVT column names – skipped)
    Row 5+: data

Layout B (e.g. pujjolo):
    Row 0:  header  [None, Key Parts, Description, supplier, ..., LCFC PN, ...]
    Row 1+: data (no sub-header row)

The parser auto-detects both layouts:
- col_category  = column index of 'Key Parts' in header (not always 0)
- data_start    = first row after header that has an LCFC PN value; any
                  all-empty or sub-header rows in between are silently skipped.
"""
from __future__ import annotations
import openpyxl
from ..models import ECComponent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cell(row: tuple, idx: int) -> str:
    if idx < len(row) and row[idx] is not None:
        return str(row[idx]).strip()
    return ""


def _find_kpl_sheet(wb: openpyxl.Workbook) -> openpyxl.worksheet.worksheet.Worksheet:
    """Return the KPL worksheet, with fallback strategies."""
    for name in wb.sheetnames:
        if "kpl" in name.lower():
            return wb[name]
    for name in wb.sheetnames:
        if "ec level" in name.lower():
            return wb[name]
    raise ValueError(
        f"Cannot find a KPL sheet in the EC Level file.\n"
        f"Available sheets: {wb.sheetnames}"
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_ec_level(filepath: str) -> list[ECComponent]:
    """
    Parse an EC Level xlsx file and return all KPL components.

    Components without an LCFC PN are silently skipped.
    """
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    sheet = _find_kpl_sheet(wb)

    rows = list(sheet.iter_rows(values_only=True))

    # ------------------------------------------------------------------
    # 1. Find the header row: must contain BOTH 'Key Parts' and 'LCFC PN'
    # ------------------------------------------------------------------
    header_idx: int | None = None
    for i, row in enumerate(rows):
        row_strs = [str(v).strip() if v is not None else "" for v in row]
        if "Key Parts" in row_strs and "LCFC PN" in row_strs:
            header_idx = i
            break

    if header_idx is None:
        wb.close()
        raise ValueError(
            "Cannot find header row containing 'Key Parts' and 'LCFC PN' "
            f"in sheet. Checked {len(rows)} rows."
        )

    header = [str(v).strip() if v is not None else "" for v in rows[header_idx]]

    # ------------------------------------------------------------------
    # 2. Map column names → indices
    #    col_category is derived from where 'Key Parts' lives in the header
    #    (NOT always col 0 – differs by project template).
    # ------------------------------------------------------------------
    def col(name: str, default: int) -> int:
        try:
            return header.index(name)
        except ValueError:
            return default

    def col_ci(name: str, default: int) -> int:
        """Case-insensitive column finder."""
        name_l = name.lower()
        for i, h in enumerate(header):
            if h.lower() == name_l:
                return i
        return default

    col_category    = header.index("Key Parts")          # dynamic!
    col_vendor      = col_ci("supplier", col_ci("vendor", 2))
    col_description = col("Description", 3)
    col_lbg_pn      = col("LBG PN", 6)
    col_lcfc_pn     = col("LCFC PN", 7)

    # ------------------------------------------------------------------
    # 3. Data rows: start immediately after the header row.
    #    Sub-header rows (if any) are handled by the LCFC-PN-empty skip.
    # ------------------------------------------------------------------
    data_start = header_idx + 1

    components: list[ECComponent] = []
    current_category = ""

    # Format detection:
    #   col_category == 0  → "old" format (pujjoquince style):
    #     The category name and LCFC PN appear in the SAME row (first row of a
    #     merged-cell range). Subsequent rows in that section have None in col 0.
    #     → always update current_category when col_category is non-empty.
    #
    #   col_category > 0  → "new" format (pujjolo style):
    #     Category header rows have a value in col_category but NO LCFC PN.
    #     Data rows have LCFC PN and a description in col_category (not the section
    #     name). → only update current_category when LCFC PN is empty.
    old_format = (col_category == 0)

    for row in rows[data_start:]:
        if not any(row):
            continue

        lcfc_pn = _cell(row, col_lcfc_pn)
        is_data_row = bool(lcfc_pn) and lcfc_pn.lower() not in ("none", "-", "n/a", "lcfc pn")

        if old_format:
            # Category and data can coexist in the same row.
            cat = _cell(row, col_category)
            if cat:
                current_category = cat
            if not is_data_row:
                continue
        else:
            # Category rows are separate from data rows.
            if not is_data_row:
                cat = _cell(row, col_category)
                if cat:
                    current_category = cat
                continue
            # Data row: do NOT update category (col_category contains a description)

        components.append(ECComponent(
            category=current_category,
            vendor=_cell(row, col_vendor),
            description=_cell(row, col_description),
            lbg_pn=_cell(row, col_lbg_pn),
            lcfc_pn=lcfc_pn,
        ))


    wb.close()
    return components
