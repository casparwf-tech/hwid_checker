@echo off
chcp 65001 >nul
REM =============================================================
REM build_windows.bat -- Package HWID Checker as Windows EXE
REM Requirements: Python 3.10 / 3.11 / 3.12 installed and on PATH
REM NOTE: Python 3.14 is NOT supported (PyQt6 sip DLL incompatibility)
REM Output: dist\HWID_Checker.exe
REM =============================================================

SET SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Use TEMP dir for build artifacts to avoid Device Guard path restrictions
SET BUILD_WORK=%TEMP%\hwid_checker_build
SET BUILD_DIST=%TEMP%\hwid_checker_dist

echo [1/5] Checking Python...
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.11 from https://python.org
    pause & exit /b 1
)
python --version

REM Warn if Python 3.14 detected (known incompatibility with PyQt6 sip)
python -c "import sys; v=sys.version_info; exit(0 if v.major==3 and v.minor<=12 else 1)" >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: Python 3.13+ detected. PyQt6 may not be compatible.
    echo Recommended: Python 3.11 or 3.12  ^(https://python.org/downloads^)
    echo Press any key to try anyway, or Ctrl+C to cancel...
    pause >nul
)

echo [2/5] Creating virtual environment...
if not exist ".venv_win\Scripts\activate.bat" (
    python -m venv .venv_win
)

SET VENV_PY=.venv_win\Scripts\python.exe

echo [3/5] Installing dependencies...
%VENV_PY% -m pip install --upgrade pip --quiet
%VENV_PY% -m pip install "PyQt6>=6.4.0"     --quiet
%VENV_PY% -m pip install "openpyxl>=3.1.0"  --quiet
%VENV_PY% -m pip install "PyYAML>=6.0"       --quiet
%VENV_PY% -m pip install pyinstaller          --quiet

echo [4/5] Building EXE (workdir: %TEMP%)...
%VENV_PY% -m PyInstaller ^
    --clean ^
    --noconfirm ^
    --workpath "%BUILD_WORK%" ^
    --distpath "%BUILD_DIST%" ^
    hwid_checker.spec

if errorlevel 1 (
    echo.
    echo ERROR: Build failed. See output above.
    pause & exit /b 1
)

echo [5/5] Copying EXE to dist\ ...
if not exist "dist" mkdir dist
copy /Y "%BUILD_DIST%\HWID_Checker.exe" "dist\HWID_Checker.exe"

echo.
echo ============================================================
echo   Build complete!
echo   EXE: %SCRIPT_DIR%dist\HWID_Checker.exe
echo ============================================================
pause
