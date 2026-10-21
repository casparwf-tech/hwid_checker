"""
Summary bar widget.

Shows coloured counters for each check status category,
plus an optional contact note (e.g. "请联系 SWPM").
"""
from __future__ import annotations
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame


# Status display config: (label text, background, text-colour)
_STATUS_STYLES: dict[str, tuple[str, str, str]] = {
    "OK":                  ("✅  OK",                "#0f2e1a", "#22c55e"),
    "MISSING":             ("❌  MISSING",            "#2e1010", "#f87171"),
    "UNSUPPORTED":         ("⚠️  UNSUPPORTED",        "#2e2010", "#fbbf24"),
    "NO_AVL_ID":           ("🔍  NO AVL ID",          "#2e1e0a", "#f97316"),
    "POSSIBLE_MATCH":      ("🔶  POSSIBLE MATCH",     "#261a0a", "#fb923c"),
    "UNKNOWN_MAPPING":     ("❓  UNKNOWN MAPPING",    "#1a1a2e", "#818cf8"),
    "UNKNOWN_CATEGORY":    ("⚙️  UNKNOWN CAT",        "#1a1a2e", "#a78bfa"),
    "NOT_IN_AVL":          ("🚫  NOT IN AVL",         "#1a0a2a", "#e879f9"),
    "AVL_NOT_QUALIFIED":   ("📋  NOT QUALIFIED",      "#1a1500", "#facc15"),
}


class _Chip(QWidget):
    def __init__(self, status: str, count: int, parent=None):
        super().__init__(parent)
        label_text, bg, fg = _STATUS_STYLES.get(
            status, (status, "#1e293b", "#94a3b8")
        )
        self.setStyleSheet(
            f"background-color: {bg}; border-radius: 6px; padding: 0px;"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(6)

        lbl = QLabel(f"{label_text}  <b>{count}</b>")
        lbl.setStyleSheet(
            f"color: {fg}; font-size: 11px; background: transparent;"
        )
        lbl.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(lbl)


class SummaryBar(QWidget):
    """
    Horizontal bar of coloured chips showing counts per status.
    Call `update_counts(counts, contact_note)` to refresh.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(8)
        self._layout.addStretch()

        self._placeholder = QLabel("Run a check to see results.")
        self._placeholder.setStyleSheet("color: #475569; font-size: 11px;")
        self._layout.insertWidget(0, self._placeholder)

    # ------------------------------------------------------------------
    def update_counts(self, counts: dict[str, int], contact_note: str = ""):
        """Replace all chips with new data. Optionally show a contact note."""
        # Remove old chips (all but stretch)
        while self._layout.count() > 1:
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not counts:
            self._layout.insertWidget(0, self._placeholder)
            return

        for status in [
            "OK", "MISSING", "UNSUPPORTED",
            "NO_AVL_ID", "POSSIBLE_MATCH",
            "UNKNOWN_MAPPING", "UNKNOWN_CATEGORY",
            "NOT_IN_AVL", "AVL_NOT_QUALIFIED",
        ]:
            n = counts.get(status, 0)
            if n > 0:
                chip = _Chip(status, n)
                self._layout.insertWidget(self._layout.count() - 1, chip)

        # Contact note (shown after chips if non-empty)
        if contact_note:
            note_lbl = QLabel(contact_note)
            note_lbl.setStyleSheet(
                "color: #fbbf24; font-size: 10px; font-weight: 600;"
                "background: transparent; padding-left: 8px;"
            )
            self._layout.insertWidget(self._layout.count() - 1, note_lbl)

    def clear(self):
        self.update_counts({})
