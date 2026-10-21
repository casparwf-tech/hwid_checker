"""
Result table widget.

Renders Region or Device check results in a styled QTableWidget with:
- Colour-coded rows per status
- Filter toolbar (All / OK / issues only / individual statuses)
- Read-only, sortable columns
"""
from __future__ import annotations
from PyQt6.QtCore import Qt, QSortFilterProxyModel, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QColor, QBrush, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableView, QHeaderView, QLabel, QAbstractItemView,
)
from core.models import RegionResult, DeviceResult

# ---------------------------------------------------------------------------
# Status → (row-bg, row-fg, icon)
# ---------------------------------------------------------------------------
_STATUS_COLORS: dict[str, tuple[str, str, str]] = {
    "OK":                  ("#0d2018", "#4ade80", "✅"),
    "MISSING":             ("#2a0f0f", "#f87171", "❌"),
    "UNSUPPORTED":         ("#2a1f0a", "#fbbf24", "⚠️"),
    "NO_AVL_ID":           ("#2a1500", "#f97316", "🔍"),
    "POSSIBLE_MATCH":      ("#251800", "#fb923c", "🔶"),
    "UNKNOWN_MAPPING":     ("#0f1030", "#818cf8", "❓"),
    "UNKNOWN_CATEGORY":    ("#100f30", "#a78bfa", "⚙️"),
    "NOT_IN_AVL":          ("#1a0a2a", "#e879f9", "🚫"),
    "AVL_NOT_QUALIFIED":   ("#1a1500", "#facc15", "📋"),
}

_DEFAULT_BG = "#13162a"
_DEFAULT_FG = "#cbd5e1"


def _status_display(status: str) -> str:
    _, _, icon = _STATUS_COLORS.get(status, ("", "", ""))
    return f"{icon} {status}" if icon else status


# ---------------------------------------------------------------------------
# Region results table model
# ---------------------------------------------------------------------------
_REGION_HEADERS = ["Geo", "Country", "Possible Codes", "Status", "Matched Code", "Note"]

class RegionTableModel(QAbstractTableModel):
    def __init__(self, results: list[RegionResult], parent=None):
        super().__init__(parent)
        self._data = results

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(_REGION_HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return _REGION_HEADERS[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row = self._data[index.row()]
        col = index.column()
        status = row.status

        if role == Qt.ItemDataRole.DisplayRole:
            vals = [
                row.geo,
                row.country_name,
                ", ".join(row.possible_codes),
                _status_display(status),
                row.matched_code,
                row.note,
            ]
            return vals[col]

        if role == Qt.ItemDataRole.BackgroundRole:
            bg, _, _ = _STATUS_COLORS.get(status, (_DEFAULT_BG, "", ""))
            return QBrush(QColor(bg))

        if role == Qt.ItemDataRole.ForegroundRole:
            _, fg, _ = _STATUS_COLORS.get(status, ("", _DEFAULT_FG, ""))
            return QBrush(QColor(fg if col == 3 else _DEFAULT_FG))

        if role == Qt.ItemDataRole.FontRole and col == 3:
            f = QFont()
            f.setBold(True)
            return f

        if role == Qt.ItemDataRole.UserRole:
            return status   # used by filter proxy

        return None


# ---------------------------------------------------------------------------
# Device results table model
# ---------------------------------------------------------------------------
_DEVICE_HEADERS = [
    "Category", "LCFC PN", "Vendor", "Description",
    "AVL Status", "HWID Key", "Check Status", "DB Status", "Note",
]

class DeviceTableModel(QAbstractTableModel):
    def __init__(self, results: list[DeviceResult], parent=None):
        super().__init__(parent)
        self._data = results

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(_DEVICE_HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return _DEVICE_HEADERS[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row = self._data[index.row()]
        col = index.column()
        status = row.check_status

        if role == Qt.ItemDataRole.DisplayRole:
            vals = [
                row.category,
                row.lcfc_pn,
                row.vendor,
                row.description,
                row.avl_status,
                row.hwid_key,
                _status_display(status),
                row.hwid_db_status,
                row.note,
            ]
            return vals[col]

        if role == Qt.ItemDataRole.BackgroundRole:
            bg, _, _ = _STATUS_COLORS.get(status, (_DEFAULT_BG, "", ""))
            return QBrush(QColor(bg))

        if role == Qt.ItemDataRole.ForegroundRole:
            _, fg, _ = _STATUS_COLORS.get(status, ("", _DEFAULT_FG, ""))
            return QBrush(QColor(fg if col == 6 else _DEFAULT_FG))

        if role == Qt.ItemDataRole.FontRole and col == 6:
            f = QFont()
            f.setBold(True)
            return f

        if role == Qt.ItemDataRole.UserRole:
            return status

        return None


# ---------------------------------------------------------------------------
# Filter proxy model
# ---------------------------------------------------------------------------
class _StatusFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._allowed: set[str] | None = None   # None = show all

    def set_filter(self, statuses: set[str] | None):
        self._allowed = statuses
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if self._allowed is None:
            return True
        idx = self.sourceModel().index(source_row, 0, source_parent)
        status = self.sourceModel().data(idx, Qt.ItemDataRole.UserRole)
        return status in self._allowed


# ---------------------------------------------------------------------------
# Filter button bar
# ---------------------------------------------------------------------------
_REGION_ISSUE_STATUSES = {"MISSING", "UNKNOWN_MAPPING"}

_DEVICE_ISSUE_STATUSES = {
    "MISSING", "UNSUPPORTED", "NO_AVL_ID",
    "POSSIBLE_MATCH", "UNKNOWN_CATEGORY",
    "NOT_IN_AVL", "AVL_NOT_QUALIFIED",
}

class _BaseFilterBar(QWidget):
    def __init__(self, proxy: _StatusFilterProxy, parent=None):
        super().__init__(parent)
        self._proxy = proxy
        self._btns: list[QPushButton] = []
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)

    def _add_btn(self, text: str, callback, active: bool = False) -> QPushButton:
        b = QPushButton(text)
        b.setCheckable(True)
        b.setChecked(active)
        b.setFixedHeight(28)
        b.clicked.connect(callback)
        b.setStyleSheet(self._btn_style(active))
        self._btns.append(b)
        self._layout.addWidget(b)
        return b

    @staticmethod
    def _btn_style(active: bool) -> str:
        if active:
            return (
                "QPushButton { background: #6366f1; color: #fff; "
                "border-radius: 6px; padding: 2px 12px; font-size: 11px; }"
            )
        return (
            "QPushButton { background: #1e2235; color: #94a3b8; "
            "border: 1px solid #2d3348; border-radius: 6px; "
            "padding: 2px 12px; font-size: 11px; } "
            "QPushButton:hover { background: #252a40; color: #e2e8f0; }"
        )

    def _activate(self, btn: QPushButton):
        for b in self._btns:
            b.setChecked(b is btn)
            b.setStyleSheet(self._btn_style(b is btn))


class _RegionFilterBar(_BaseFilterBar):
    def __init__(self, proxy: _StatusFilterProxy, parent=None):
        super().__init__(proxy, parent)
        self._btn_all    = self._add_btn("All",               self._show_all, True)
        self._btn_issues = self._add_btn("Issues Only",        self._show_issues)
        self._btn_ok     = self._add_btn("✅ OK",              self._show_ok)
        self._btn_miss   = self._add_btn("❌ Missing",         self._show_missing)
        self._btn_unk    = self._add_btn("❓ Unknown Mapping", self._show_unknown)
        self._layout.addStretch()

    def _show_all(self):
        self._activate(self._btn_all)
        self._proxy.set_filter(None)

    def _show_issues(self):
        self._activate(self._btn_issues)
        self._proxy.set_filter(_REGION_ISSUE_STATUSES)

    def _show_ok(self):
        self._activate(self._btn_ok)
        self._proxy.set_filter({"OK"})

    def _show_missing(self):
        self._activate(self._btn_miss)
        self._proxy.set_filter({"MISSING"})

    def _show_unknown(self):
        self._activate(self._btn_unk)
        self._proxy.set_filter({"UNKNOWN_MAPPING"})


class _DeviceFilterBar(_BaseFilterBar):
    def __init__(self, proxy: _StatusFilterProxy, parent=None):
        super().__init__(proxy, parent)
        self._btn_all      = self._add_btn("All",              self._show_all, True)
        self._btn_issues   = self._add_btn("Issues Only",       self._show_issues)
        self._btn_ok       = self._add_btn("✅ OK",             self._show_ok)
        self._btn_miss     = self._add_btn("❌ Missing",        self._show_missing)
        self._btn_unsup    = self._add_btn("⚠️ Unsupported",    self._show_unsupported)
        self._btn_noavl    = self._add_btn("🔍 No AVL ID",      self._show_noavl)
        self._btn_notinavl = self._add_btn("🚫 Not in AVL",     self._show_not_in_avl)
        self._btn_notqual  = self._add_btn("📋 Not Qualified",  self._show_not_qual)
        self._layout.addStretch()

    def _show_all(self):
        self._activate(self._btn_all)
        self._proxy.set_filter(None)

    def _show_issues(self):
        self._activate(self._btn_issues)
        self._proxy.set_filter(_DEVICE_ISSUE_STATUSES)

    def _show_ok(self):
        self._activate(self._btn_ok)
        self._proxy.set_filter({"OK"})

    def _show_missing(self):
        self._activate(self._btn_miss)
        self._proxy.set_filter({"MISSING"})

    def _show_unsupported(self):
        self._activate(self._btn_unsup)
        self._proxy.set_filter({"UNSUPPORTED"})

    def _show_noavl(self):
        self._activate(self._btn_noavl)
        self._proxy.set_filter({"NO_AVL_ID", "POSSIBLE_MATCH"})

    def _show_not_in_avl(self):
        self._activate(self._btn_notinavl)
        self._proxy.set_filter({"NOT_IN_AVL"})

    def _show_not_qual(self):
        self._activate(self._btn_notqual)
        self._proxy.set_filter({"AVL_NOT_QUALIFIED"})


# Backward compatibility alias
_FilterBar = _DeviceFilterBar


# ---------------------------------------------------------------------------
# Public result table widget
# ---------------------------------------------------------------------------

def _make_table_view() -> QTableView:
    tv = QTableView()
    tv.setAlternatingRowColors(False)
    tv.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    tv.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    tv.setSortingEnabled(True)
    tv.horizontalHeader().setStretchLastSection(True)
    tv.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
    tv.verticalHeader().setVisible(False)
    tv.setShowGrid(False)
    tv.setStyleSheet("""
        QTableView {
            background-color: #0d1117;
            color: #cbd5e1;
            font-size: 11px;
            border: none;
            gridline-color: #1e2235;
        }
        QTableView::item { padding: 4px 8px; border-bottom: 1px solid #1a1d30; }
        QTableView::item:selected { background-color: #2d3a6e; }
        QHeaderView::section {
            background-color: #161b2e;
            color: #94a3b8;
            font-size: 11px;
            font-weight: bold;
            padding: 6px 8px;
            border: none;
            border-bottom: 2px solid #2d3348;
        }
        QScrollBar:vertical { background: #0d1117; width: 8px; }
        QScrollBar::handle:vertical { background: #2d3348; border-radius: 4px; }
    """)
    return tv


class RegionResultTable(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._proxy = _StatusFilterProxy()
        self._filter_bar = _RegionFilterBar(self._proxy)
        self._view = _make_table_view()
        self._view.setModel(self._proxy)

        layout.addWidget(self._filter_bar)
        layout.addWidget(self._view)

    def load(self, results: list[RegionResult]):
        model = RegionTableModel(results)
        self._proxy.setSourceModel(model)
        self._view.resizeColumnsToContents()
        self._view.horizontalHeader().setStretchLastSection(True)


class DeviceResultTable(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._proxy = _StatusFilterProxy()
        self._filter_bar = _DeviceFilterBar(self._proxy)
        self._view = _make_table_view()
        self._view.setModel(self._proxy)

        layout.addWidget(self._filter_bar)
        layout.addWidget(self._view)

    def load(self, results: list[DeviceResult]):
        model = DeviceTableModel(results)
        self._proxy.setSourceModel(model)
        self._view.resizeColumnsToContents()
        self._view.horizontalHeader().setStretchLastSection(True)
