"""
File upload panel widget.

Renders four drop-zone cards side by side.  Each card accepts drag-and-drop
or a click-to-browse interaction.  The panel emits `all_files_ready` when
all four files have been selected.
"""
from __future__ import annotations
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal, QMimeData
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent, QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QFileDialog, QSizePolicy,
)


# ---------------------------------------------------------------------------
# Single drop-zone card
# ---------------------------------------------------------------------------

class _DropCard(QWidget):
    """A single file drop/browse card."""

    file_selected = pyqtSignal(str)   # absolute path

    _BORDER_NORMAL   = "#2d3348"
    _BORDER_HOVER    = "#6366f1"
    _BORDER_READY    = "#22c55e"
    _BG_NORMAL       = "#13162a"
    _BG_HOVER        = "#1a1d3a"
    _BG_READY        = "#0f2420"

    def __init__(self, label: str, file_filter: str, icon: str, parent=None):
        super().__init__(parent)
        self._label       = label
        self._file_filter = file_filter
        self._icon        = icon
        self._filepath: str = ""
        self._hovered     = False

        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumSize(160, 140)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 16, 12, 16)

        self._icon_lbl = QLabel(self._icon)
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_lbl.setStyleSheet("font-size: 28px; background: transparent;")

        self._title_lbl = QLabel(self._label)
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_lbl.setStyleSheet(
            "font-size: 12px; font-weight: 700; color: #a5b4fc; background: transparent;"
        )

        self._hint_lbl = QLabel("Drop file here\nor click to browse")
        self._hint_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hint_lbl.setStyleSheet(
            "font-size: 10px; color: #64748b; background: transparent;"
        )

        self._file_lbl = QLabel("")
        self._file_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._file_lbl.setWordWrap(True)
        self._file_lbl.setStyleSheet(
            "font-size: 9px; color: #22c55e; background: transparent;"
        )

        layout.addWidget(self._icon_lbl)
        layout.addWidget(self._title_lbl)
        layout.addWidget(self._hint_lbl)
        layout.addWidget(self._file_lbl)

    # ------------------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._filepath:
            bg    = QColor(self._BG_READY)
            border = QColor(self._BORDER_READY)
        elif self._hovered:
            bg    = QColor(self._BG_HOVER)
            border = QColor(self._BORDER_HOVER)
        else:
            bg    = QColor(self._BG_NORMAL)
            border = QColor(self._BORDER_NORMAL)

        rect = self.rect().adjusted(2, 2, -2, -2)
        painter.setBrush(bg)
        pen = QPen(border, 2, Qt.PenStyle.DashLine if not self._filepath else Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.drawRoundedRect(rect, 10, 10)

    # ------------------------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._browse()

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    # ------------------------------------------------------------------
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._hovered = True
            self.update()

    def dragLeaveEvent(self, event):
        self._hovered = False
        self.update()

    def dropEvent(self, event: QDropEvent):
        self._hovered = False
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            self._set_file(path)

    # ------------------------------------------------------------------
    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, f"Select {self._label}", "", self._file_filter
        )
        if path:
            self._set_file(path)

    def _set_file(self, path: str):
        self._filepath = path
        name = Path(path).name
        size = Path(path).stat().st_size
        size_str = f"{size / 1024:.1f} KB" if size < 1_048_576 else f"{size / 1_048_576:.1f} MB"
        self._hint_lbl.setText("✓ File loaded")
        self._hint_lbl.setStyleSheet(
            "font-size: 10px; color: #22c55e; background: transparent;"
        )
        self._file_lbl.setText(f"{name}\n({size_str})")
        self.update()
        self.file_selected.emit(path)

    def get_path(self) -> str:
        return self._filepath

    def reset(self):
        self._filepath = ""
        self._hint_lbl.setText("Drop file here\nor click to browse")
        self._hint_lbl.setStyleSheet(
            "font-size: 10px; color: #64748b; background: transparent;"
        )
        self._file_lbl.setText("")
        self.update()


# ---------------------------------------------------------------------------
# Panel that hosts the four cards
# ---------------------------------------------------------------------------

class FileUploadPanel(QWidget):
    """
    Horizontal panel with four file drop-zone cards.

    Signals
    -------
    all_files_ready(od, hwid, ec, avl)   – emitted when all four paths are set.
    file_changed()                        – emitted on any change.
    """

    all_files_ready = pyqtSignal(str, str, str, str)
    file_changed    = pyqtSignal()

    _XLSX = "Excel Files (*.xlsx *.xls);;All Files (*)"
    _ANY  = "All Files (*)"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        self._od_card   = _DropCard("OD",            self._XLSX, "📋")
        self._hwid_card = _DropCard("HWID Database", self._ANY,  "🔑")
        self._ec_card   = _DropCard("EC Level",      self._XLSX, "⚡")
        self._avl_card  = _DropCard("AVL List",      self._XLSX, "📦")

        for card in (self._od_card, self._hwid_card, self._ec_card, self._avl_card):
            card.file_selected.connect(self._on_file_changed)
            layout.addWidget(card)

    def _on_file_changed(self, _path: str):
        self.file_changed.emit()
        paths = self.get_paths()
        if all(paths):
            self.all_files_ready.emit(*paths)

    def get_paths(self) -> tuple[str, str, str, str]:
        return (
            self._od_card.get_path(),
            self._hwid_card.get_path(),
            self._ec_card.get_path(),
            self._avl_card.get_path(),
        )

    def is_ready(self) -> bool:
        return all(self.get_paths())

    def reset(self):
        for card in (self._od_card, self._hwid_card, self._ec_card, self._avl_card):
            card.reset()
