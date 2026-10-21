"""
Background check worker.

Runs all parsers and checkers in a QThread so the UI stays responsive.
Emits progress signals and a final CheckReport (or an error string).
"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from core.parsers.od_parser import parse_od
from core.parsers.hwid_parser import parse_hwid
from core.parsers.ec_parser import parse_ec_level
from core.parsers.avl_parser import parse_avl
from core.checker.region_checker import check_regions
from core.checker.device_checker import check_devices
from core.models import CheckReport


class CheckWorker(QThread):
    """
    Signals
    -------
    progress(message, percent)
        Emitted at each processing stage.
    completed(report)
        Emitted when all checks finish successfully.
    error(message)
        Emitted if any exception is raised.
    """

    progress  = pyqtSignal(str, int)   # (message, 0–100)
    completed = pyqtSignal(object)     # CheckReport
    error     = pyqtSignal(str)

    def __init__(
        self,
        od_path: str,
        hwid_path: str,
        ec_path: str,
        avl_path: str,
        parent=None,
    ):
        super().__init__(parent)
        self.od_path   = od_path
        self.hwid_path = hwid_path
        self.ec_path   = ec_path
        self.avl_path  = avl_path

    # ------------------------------------------------------------------
    def run(self) -> None:
        try:
            self.progress.emit("Parsing OD file…", 10)
            countries = parse_od(self.od_path)

            self.progress.emit("Parsing HWID database…", 25)
            hwid_data = parse_hwid(self.hwid_path)

            self.progress.emit("Parsing EC Level…", 45)
            ec_components = parse_ec_level(self.ec_path)

            self.progress.emit("Parsing AVL List…", 60)
            avl_components = parse_avl(self.avl_path)

            self.progress.emit("Checking regions…", 75)
            region_results = check_regions(
                countries, hwid_data["region_codes"]
            )

            self.progress.emit("Checking devices…", 90)
            device_results = check_devices(
                ec_components, avl_components, hwid_data["components"]
            )

            self.progress.emit("Finalising report…", 98)

            # Project name: first segment of EC Level filename + HWID database stem
            # e.g. "MCB50_S3A0_EC Level 20260121.xlsx" → "MCB50"
            #      "pujjoquince.yaml"                  → "pujjoquince"
            ec_stem   = Path(self.ec_path).stem
            ec_name   = ec_stem.split("_")[0].strip()   # take first "_"-delimited token
            hwid_name = Path(self.hwid_path).stem
            project_name = f"{ec_name}_{hwid_name}"

            report = CheckReport(
                project_name=project_name,
                run_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                region_results=region_results,
                device_results=device_results,
            )

            self.progress.emit("Done", 100)
            self.completed.emit(report)

        except Exception as exc:  # noqa: BLE001
            import traceback
            self.error.emit(
                f"{type(exc).__name__}: {exc}\n\n{traceback.format_exc()}"
            )
