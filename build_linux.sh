#!/usr/bin/env bash
# =============================================================================
# build_linux.sh — 打包 HWID Checker 为 Linux 可执行文件
# 输出: dist/HWID_Checker  (单文件，无需安装 Python)
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

cd "$SCRIPT_DIR"

# 确保虚拟环境存在
if [ ! -f "$VENV_PYTHON" ]; then
    echo ">>> 未找到虚拟环境，先运行 setup.sh ..."
    bash "$SCRIPT_DIR/setup.sh" || exit 1
fi

# 安装 PyInstaller（如果尚未安装）
if ! "$VENV_PYTHON" -c "import PyInstaller" 2>/dev/null; then
    echo ">>> 安装 PyInstaller ..."
    "$VENV_PIP" install pyinstaller
fi

echo ">>> 开始打包 Linux 可执行文件 ..."
"$VENV_DIR/bin/pyinstaller" \
    --clean \
    --noconfirm \
    hwid_checker.spec

echo ""
echo "============================================================"
echo "  ✅ 打包完成！"
echo "  可执行文件: $(pwd)/dist/HWID_Checker"
echo "============================================================"
