#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# Obsidian Word Importer — 一键安装脚本
# 用法: chmod +x install.sh && ./install.sh
# ═══════════════════════════════════════════════════════════════════════
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║   Obsidian Word Importer v2.1 — 一键安装            ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOST_PY="$SCRIPT_DIR/native-host/host.py"
HOST_JSON="$SCRIPT_DIR/native-host/host.json"

# ═══════════════════════════════════════════════════════════════════════
# 1. 检测环境
# ═══════════════════════════════════════════════════════════════════════
echo -e "${YELLOW}[1/5]${NC} 检测环境..."

PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done
if [ -z "$PYTHON" ]; then
    echo -e "${RED}错误: 未找到 Python 3，请先安装${NC}"
    exit 1
fi
echo "       Python: $($PYTHON --version)"

case "$(uname -s)" in
    Linux)
        CHROME_PREFS="$HOME/.config/google-chrome/Default/Preferences"
        CHROME_PREFS_SECURE="$HOME/.config/google-chrome/Default/Secure Preferences"
        HOST_DIR="$HOME/.config/google-chrome/NativeMessagingHosts"
        ;;
    Darwin)
        CHROME_PREFS="$HOME/Library/Application Support/Google/Chrome/Default/Preferences"
        CHROME_PREFS_SECURE="$HOME/Library/Application Support/Google/Chrome/Default/Secure Preferences"
        HOST_DIR="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts"
        ;;
    *)
        echo -e "${RED}不支持的操作系统${NC}"
        exit 1
        ;;
esac

# ═══════════════════════════════════════════════════════════════════════
# 2. 计算扩展 ID（基于路径的 SHA256）
# ═══════════════════════════════════════════════════════════════════════
echo -e "${YELLOW}[2/5]${NC} 计算扩展 ID..."

EXT_ID=$($PYTHON -c "
import hashlib
path = '$SCRIPT_DIR'.lower().encode('utf-8')
h = hashlib.sha256(path).digest()
chars = []
for b in h[:16]:
    chars.append(chr(ord('a') + (b >> 4)))
    chars.append(chr(ord('a') + (b & 0x0f)))
print(''.join(chars[:32]))
")
echo "       扩展 ID: $EXT_ID"

# ═══════════════════════════════════════════════════════════════════════
# 3. 安装 Native Host
# ═══════════════════════════════════════════════════════════════════════
echo -e "${YELLOW}[3/5]${NC} 安装 Native Host..."

mkdir -p "$HOST_DIR"
chmod +x "$HOST_PY"

MANIFEST_FILE="$HOST_DIR/com.obsidian.wordimporter.json"
sed -e "s|HOST_PYTHON_PATH_PLACEHOLDER|$HOST_PY|g" \
    -e "s|EXTENSION_ID_PLACEHOLDER|$EXT_ID|g" \
    "$HOST_JSON" > "$MANIFEST_FILE"

echo "       清单已写入: $MANIFEST_FILE"

# ═══════════════════════════════════════════════════════════════════════
# 4. 注册扩展到 Chrome
# ═══════════════════════════════════════════════════════════════════════
echo -e "${YELLOW}[4/5]${NC} 注册扩展到 Chrome..."

# Kill Chrome to safely modify Preferences
if pgrep -x "chrome" > /dev/null 2>&1; then
    echo "       正在关闭 Chrome..."
    pkill -x chrome 2>/dev/null || true
    sleep 2
fi

for PREFS_FILE in "$CHROME_PREFS" "$CHROME_PREFS_SECURE"; do
    if [ ! -f "$PREFS_FILE" ]; then
        continue
    fi

    $PYTHON -c "
import json, sys

prefs_path = '$PREFS_FILE'
with open(prefs_path, 'r') as f:
    prefs = json.load(f)

# Add extension registration
ext_id = '$EXT_ID'
ext_path = '$SCRIPT_DIR'

# Read our manifest
with open('$SCRIPT_DIR/manifest.json') as f:
    manifest = json.load(f)

prefs.setdefault('extensions', {}).setdefault('settings', {})
prefs['extensions']['settings'][ext_id] = {
    'active_permissions': {
        'api': manifest.get('permissions', []),
        'explicit_host': manifest.get('host_permissions', []),
        'manifest_permissions': [],
        'scriptable_host': manifest.get('host_permissions', []),
    },
    'creation_flags': 38,
    'first_install_time': '13422803526400914',
    'from_webstore': False,
    'granted_permissions': {
        'api': manifest.get('permissions', []),
        'explicit_host': manifest.get('host_permissions', []),
        'manifest_permissions': [],
        'scriptable_host': manifest.get('host_permissions', []),
    },
    'has_started_service_worker': True,
    'location': 4,
    'manifest': manifest,
    'newAllowFileAccess': True,
    'path': ext_path,
    'preferences': {},
    'was_installed_by_default': False,
    'was_installed_by_oem': False,
    'withholding_permissions': False,
}

# Clear protection MAC
if 'protection' in prefs:
    macs = prefs['protection'].get('macs', {})
    if 'extensions' in macs:
        macs['extensions'].pop('settings', None)
    if not macs.get('extensions'):
        macs.pop('extensions', None)
    if not macs:
        prefs['protection'].pop('macs', None)
    if not prefs['protection']:
        prefs.pop('protection', None)

# Also clear super_mac if present
prefs.pop('super_mac', None)

with open(prefs_path, 'w') as f:
    json.dump(prefs, f, indent=2, ensure_ascii=False)
"
    echo "       $PREFS_FILE ✓"
done

# ═══════════════════════════════════════════════════════════════════════
# 5. 完成
# ═══════════════════════════════════════════════════════════════════════
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           安装完成！请重启 Chrome                     ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo "首次使用:"
echo "  1. 重启 Chrome"
echo "  2. 在 chrome://extensions 确认扩展已加载"
echo "  3. 打开任意英文网页，选中单词 Ctrl+C 即可收录"
echo ""
echo "配置 Obsidian Vault 路径（可选，插件会自动检测）:"
echo "  点击扩展图标 → 设置 Vault 路径 → 保存"
echo ""
