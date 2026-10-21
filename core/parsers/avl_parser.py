"""
AVL List parser.

Reads the 'AVL list' sheet from an AVL xlsx file.

Supported layouts
-----------------
Layout A (e.g. pujjoquince):
    Row 0:  header  [<ProjectPN>, Vendor, MPN, LCFC PN, LNV PN, AVL Status, ..., Google AVL Link, ...]
    Row 1+: data
    col_category = 0 (merged cells, forward-fill)

Layout B (e.g. pujjolo):
    Row 0:  metadata row (numbers, arrows – not the header)
    Row 1:  header  [None, Party, Owner, Category, None, LCFC PN, Vendor, MPN, ..., Google AVL Link, ..., AVL Status, ...]
    Row 2+: data
    col_category = index of 'Category' in header

The parser auto-detects the header row by scanning for the row containing
'LCFC PN' (case-insensitive).
"""
from __future__ import annotations
import re
import openpyxl
from ..models import AVLComponent

_AVL_URL_RE = re.compile(r"/component/(\d+)(?:/qualification/(\d+))?")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_ids(url: str) -> tuple[str, str]:
    """Return (component_id, qual_id) from a Google AVL URL, or ('', '')."""
    if not url:
        return "", ""
    m = _AVL_URL_RE.search(url)
    if m:
        return m.group(1), m.group(2) or ""
    return "", ""


def _cell(row: tuple, idx: int) -> str:
    if idx >= 0 and idx < len(row) and row[idx] is not None:
        return str(row[idx]).strip()
    return ""


def _find_avl_sheet(wb: openpyxl.Workbook) -> openpyxl.worksheet.worksheet.Worksheet:
    for name in wb.sheetnames:
        if name.strip().lower() == "avl list":
            return wb[name]
    for name in wb.sheetnames:
        if "avl" in name.lower() and "list" in name.lower():
            return wb[name]
    for name in wb.sheetnames:
        if "avl" in name.lower():
            return wb[name]
    raise ValueError(
        f"Cannot find an AVL list sheet.\n"
        f"Available sheets: {wb.sheetnames}"
    )


def _find_header_row(rows: list[tuple]) -> int:
    """
    Return the index of the first row that contains 'LCFC PN' (case-insensitive).
    Falls back to 0 if not found.
    """
    for i, row in enumerate(rows):
        for cell in row:
            if cell is not None and str(cell).strip().lower() == "lcfc pn":
                return i
    return 0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_avl(filepath: str) -> list[AVLComponent]:
    """
    Parse an AVL List xlsx file and return all component rows.

    All rows are returned regardless of AVL status; filtering for QUALIFIED
    is done in the checker layer.
    """
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    sheet = _find_avl_sheet(wb)

    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        wb.close()
        return []

    # ------------------------------------------------------------------
    # Auto-detect header row
    # ------------------------------------------------------------------
    header_idx = _find_header_row(rows)
    header = [str(v).strip() if v is not None else "" for v in rows[header_idx]]

    def find_col(keyword: str, default: int) -> int:
        kw = keyword.lower()
        for i, h in enumerate(header):
            if kw in h.lower():
                return i
        return default

    # col_category: dynamic – could be 0 (layout A) or 3 (layout B)
    col_category   = find_col("category", 0)
    col_vendor     = find_col("vendor", 1)
    col_mpn        = find_col("mpn", 2)
    col_lcfc_pn    = find_col("lcfc pn", 3)
    col_lnv_pn     = find_col("lnv pn", 4)
    col_avl_status = find_col("avl status", 5)
    col_url        = find_col("google avl link", 10)

    # ------------------------------------------------------------------
    # Parse data rows (everything after the header row)
    # ------------------------------------------------------------------
    components: list[AVLComponent] = []
    current_category = ""

    for row in rows[header_idx + 1:]:
        if not any(row):
            continue

        cat = _cell(row, col_category)
        # Only update category when cell is non-empty AND not a junk value
        # (avoids col_category picking up description text in data rows for
        #  layouts where that column is shared with description).
        if cat and cat.lower() not in ("none", "", "category"):
            current_category = cat

        lcfc_pn = _cell(row, col_lcfc_pn)
        avl_status = _cell(row, col_avl_status)
        url = _cell(row, col_url)
        comp_id, qual_id = _extract_ids(url)

        components.append(AVLComponent(
            category=current_category,
            vendor=_cell(row, col_vendor),
            mpn=_cell(row, col_mpn),
            lcfc_pn=lcfc_pn,
            lnv_pn=_cell(row, col_lnv_pn),
            avl_status=avl_status,
            google_avl_url=url,
            component_id=comp_id,
            qual_id=qual_id,
        ))

    wb.close()
    return components
