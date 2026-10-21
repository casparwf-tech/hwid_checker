#!/usr/bin/env bash
# =============================================================================
# setup.sh — HWID Checker 一键安装脚本
# 适用于任何 Ubuntu 22.04+ 机器
#
# 使用方式:
#   bash setup.sh
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}✓${NC} $1"; }
warn()  { echo -e "${YELLOW}⚠${NC}  $1"; }
error() { echo -e "${RED}✗${NC} $1"; exit 1; }

echo ""
echo "  ╔══════════════════════════════════╗"
echo "  ║       HWID Checker Setup         ║"
echo "  ╚══════════════════════════════════╝"
echo ""

# ── 1. 检查 Python 3 ───────────────────────────────────────────────────────
PYTHON=$(command -v python3 || command -v python || true)
[ -z "$PYTHON" ] && error "未找到 python3，请先安装: sudo apt install python3"

PY_VERSION=$("$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$("$PYTHON" -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$("$PYTHON" -c 'import sys; print(sys.version_info.minor)')

info "Python: $PY_VERSION ($PYTHON)"

[ "$PY_MAJOR" -lt 3 ] && error "需要 Python 3.8+，当前为 $PY_VERSION"
[ "$PY_MINOR" -lt 8 ] && error "需要 Python 3.8+，当前为 $PY_VERSION"

# ── 2. 确保 venv 模块可用 ─────────────────────────────────────────────────
if ! "$PYTHON" -m venv --help &>/dev/null 2>&1; then
    warn "python3-venv 未安装，尝试通过 apt 安装..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get install -y "python${PY_MAJOR}.${PY_MINOR}-venv" python3-venv 2>/dev/null \
            || sudo apt-get install -y python3-venv \
            || error "无法安装 python3-venv，请手动执行: sudo apt install python3.${PY_MINOR}-venv"
        info "python3-venv 安装完成"
    else
        error "无法自动安装 python3-venv，请手动执行: sudo apt install python3.${PY_MINOR}-venv"
    fi
fi

# 再次验证（apt 安装后需要重新检测）
"$PYTHON" -c "import venv" 2>/dev/null \
    || error "venv 模块不可用。请手动执行: sudo apt install python${PY_MAJOR}.${PY_MINOR}-venv"


# ── 3. 创建虚拟环境 ───────────────────────────────────────────────────────
# 如果已存在，检查是否完整（有 pip）；残缺则删掉重建
if [ -d "$VENV_DIR" ]; then
    if "$VENV_DIR/bin/python" -m pip --version &>/dev/null 2>&1; then
        warn "已存在虚拟环境，跳过创建: $VENV_DIR"
    else
        warn "检测到残缺的虚拟环境（无 pip），正在删除并重建..."
        rm -rf "$VENV_DIR"
        info "创建虚拟环境: $VENV_DIR"
        "$PYTHON" -m venv "$VENV_DIR"
    fi
else
    info "创建虚拟环境: $VENV_DIR"
    "$PYTHON" -m venv "$VENV_DIR"
fi

VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

# ── 4. 升级 pip ────────────────────────────────────────────────────────────
info "升级 pip..."
"$VENV_PYTHON" -m pip install --upgrade pip --quiet

# ── 5. 安装依赖（从 requirements.txt 读取，保证版本一致）─────────────────
info "安装依赖 (PyQt6, openpyxl, PyYAML)..."
"$VENV_PIP" install -r "$SCRIPT_DIR/requirements.txt" --quiet

# ── 6. 检查系统 Qt 库（PyQt6 wheel 需要 libGL 等动态库）──────────────────
if ! "$VENV_PYTHON" -c "from PyQt6.QtWidgets import QApplication" &>/dev/null 2>&1; then
    warn "PyQt6 无法加载 Qt 库，尝试安装系统 Qt 依赖..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get install -y libgl1 libglib2.0-0 libdbus-1-3 \
            libxcb-cursor0 libxcb-xinerama0 libegl1 2>/dev/null || true
    fi
fi

# ── 7. 验证所有依赖 ───────────────────────────────────────────────────────
"$VENV_PYTHON" -c "
failed = []
try:
    from PyQt6.QtWidgets import QApplication
except Exception as e:
    failed.append(f'PyQt6: {e}')
try:
    import openpyxl
except Exception as e:
    failed.append(f'openpyxl: {e}')
try:
    import yaml
except Exception as e:
    failed.append(f'PyYAML: {e}')
if failed:
    print('FAILED:', '\n  '.join(failed))
    exit(1)
print('  所有依赖验证通过 (PyQt6 / openpyxl / PyYAML)')
" || error "依赖安装验证失败，请查看上方错误信息"

info "安装完成！"
echo ""
echo "  运行方式:"
echo ""
echo "    bash run.sh"
echo ""
