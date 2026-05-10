#!/bin/bash
# ──────────────────────────────────────────────────
# Obsidian Word Importer - Native Host 安装脚本
# ──────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOST_PY="$SCRIPT_DIR/host.py"
HOST_JSON="$SCRIPT_DIR/host.json"

echo "============================================"
echo " Obsidian Word Importer - Native Host 安装"
echo "============================================"

# ── 1. Detect platform ──
case "$(uname -s)" in
    Linux)
        HOST_DIR="$HOME/.config/google-chrome/NativeMessagingHosts"
        # Also support Chromium / Edge
        if [ ! -d "$HOST_DIR" ] && [ -d "$HOME/.config/chromium/NativeMessagingHosts" ]; then
            HOST_DIR="$HOME/.config/chromium/NativeMessagingHosts"
        fi
        if [ ! -d "$HOST_DIR" ] && [ -d "$HOME/.config/microsoft-edge/NativeMessagingHosts" ]; then
            HOST_DIR="$HOME/.config/microsoft-edge/NativeMessagingHosts"
        fi
        ;;
    Darwin)
        HOST_DIR="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts"
        ;;
    *)
        echo "不支持的操作系统: $(uname -s)"
        exit 1
        ;;
esac

echo ""
echo "[1/4] 平台检测: $(uname -s)"
echo "        目标目录: $HOST_DIR"
mkdir -p "$HOST_DIR"

# ── 2. Check Python (stdlib only, no external deps) ──
echo "[2/4] 检查 Python..."
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "错误: 未找到 Python，请先安装 Python 3"
    exit 1
fi
echo "        Python: $PYTHON ($($PYTHON --version 2>&1))"
echo "        使用标准库，无需额外依赖"

# ── 3. Generate manifest ──
echo "[3/4] 生成 Native Host 清单..."

MANIFEST_FILE="$HOST_DIR/com.obsidian.wordimporter.json"

if [ -f "$MANIFEST_FILE" ]; then
    read -p "        已存在旧清单，是否覆盖? [y/N] " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "        跳过"
    fi
fi

sed -e "s|HOST_PYTHON_PATH_PLACEHOLDER|$HOST_PY|g" \
    -e "s|EXTENSION_ID_PLACEHOLDER|*|g" \
    "$HOST_JSON" > "$MANIFEST_FILE"

echo "        清单已写入: $MANIFEST_FILE"

# ── 4. Make host.py executable ──
chmod +x "$HOST_PY"
echo "[4/4] host.py 已设为可执行"

# ── Verify ──
echo ""
echo "============================================"
echo " 安装完成!"
echo "============================================"
echo ""
echo "下一步:"
echo "  1. 在 Chrome 打开 chrome://extensions"
echo "  2. 开启「开发者模式」"
echo "  3. 点击「加载已解压的扩展程序」"
echo "  4. 选择目录: $(dirname "$SCRIPT_DIR")"
echo "  5. 在扩展弹出窗口中设置 Obsidian Vault 路径"
echo "  6. 在任意英文网页选中单词并按 Ctrl+C 测试"
echo ""
echo "注意: 扩展 ID 生成后，请更新清单中的 ID 并重新运行本脚本"
echo "      当前使用通配符 * 以允许开发模式使用"
echo ""
