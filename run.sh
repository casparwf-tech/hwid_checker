#!/usr/bin/env bash
# =============================================================================
# run.sh — HWID Checker 启动脚本
# 如果虚拟环境不存在，自动执行 setup.sh 安装依赖
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"

# 如果 .venv 不存在或 PyQt6 未安装，先运行 setup
if [ ! -f "$VENV_PYTHON" ] || ! "$VENV_PYTHON" -c "import PyQt6" &>/dev/null 2>&1; then
    echo "未检测到虚拟环境，正在安装依赖..."
    bash "$SCRIPT_DIR/setup.sh" || exit 1
fi

# 启动应用
cd "$SCRIPT_DIR"
exec "$VENV_PYTHON" main.py "$@"
