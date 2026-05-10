#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# Obsidian Word Importer — 一键安装脚本
# 支持 Chrome / Edge / Chromium / Firefox
# 用法:
#   ./install.sh           # 安装到所有已检测到的浏览器
#   ./install.sh chrome    # 仅 Chrome
#   ./install.sh firefox   # 仅 Firefox
#   ./install.sh all       # 所有浏览器
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
HOST_JSON_FX="$SCRIPT_DIR/native-host/host.firefox.json"

declare -A BROWSER_PROCESS
declare -A BROWSER_CONFIG_DIR
declare -A BROWSER_DISPLAY
declare -A BROWSER_HOST_TEMPLATE

# ═══════════════════════════════════════════════════════════════════════
# 1. 检测环境
# ═══════════════════════════════════════════════════════════════════════
echo -e "${YELLOW}[1/4]${NC} 检测环境..."

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

OS="$(uname -s)"

# ── 浏览器配置表 ──
# 格式: 名称:进程名:配置目录:显示名
declare -A BROWSER_PROCESS
declare -A BROWSER_CONFIG_DIR
declare -A BROWSER_DISPLAY

if [ "$OS" = "Linux" ]; then
    BROWSER_PROCESS[chrome]="chrome"
    BROWSER_CONFIG_DIR[chrome]="$HOME/.config/google-chrome"
    BROWSER_DISPLAY[chrome]="Google Chrome"
    BROWSER_HOST_TEMPLATE[chrome]="$HOST_JSON"

    BROWSER_PROCESS[edge]="microsoft-edge"
    BROWSER_CONFIG_DIR[edge]="$HOME/.config/microsoft-edge"
    BROWSER_DISPLAY[edge]="Microsoft Edge"
    BROWSER_HOST_TEMPLATE[edge]="$HOST_JSON"

    BROWSER_PROCESS[chromium]="chromium"
    BROWSER_CONFIG_DIR[chromium]="$HOME/.config/chromium"
    BROWSER_DISPLAY[chromium]="Chromium"
    BROWSER_HOST_TEMPLATE[chromium]="$HOST_JSON"

    BROWSER_PROCESS[firefox]="firefox"
    BROWSER_CONFIG_DIR[firefox]="$HOME/.mozilla"
    BROWSER_DISPLAY[firefox]="Firefox"
    BROWSER_HOST_TEMPLATE[firefox]="$HOST_JSON_FX"
elif [ "$OS" = "Darwin" ]; then
    BROWSER_PROCESS[chrome]="Google Chrome"
    BROWSER_CONFIG_DIR[chrome]="$HOME/Library/Application Support/Google/Chrome"
    BROWSER_DISPLAY[chrome]="Google Chrome"
    BROWSER_HOST_TEMPLATE[chrome]="$HOST_JSON"

    BROWSER_PROCESS[edge]="Microsoft Edge"
    BROWSER_CONFIG_DIR[edge]="$HOME/Library/Application Support/Microsoft Edge"
    BROWSER_DISPLAY[edge]="Microsoft Edge"
    BROWSER_HOST_TEMPLATE[edge]="$HOST_JSON"

    BROWSER_PROCESS[firefox]="firefox"
    BROWSER_CONFIG_DIR[firefox]="$HOME/Library/Application Support/Mozilla"
    BROWSER_DISPLAY[firefox]="Firefox"
    BROWSER_HOST_TEMPLATE[firefox]="$HOST_JSON_FX"
else
    echo -e "${RED}不支持的操作系统: $OS${NC}"
    exit 1
fi

# ── 确定要安装的目标浏览器 ──
TARGET_BROWSERS=()
if [ $# -gt 0 ]; then
    for arg in "$@"; do
        if [ -n "${BROWSER_PROCESS[$arg]:-}" ]; then
            TARGET_BROWSERS+=("$arg")
        elif [ "$arg" = "all" ]; then
            TARGET_BROWSERS=("${!BROWSER_PROCESS[@]}")
            break
        else
            echo -e "${RED}未知浏览器: $arg (支持: chrome, edge, chromium, all)${NC}"
            exit 1
        fi
    done
fi

# 如果没指定，自动检测已安装的浏览器
if [ ${#TARGET_BROWSERS[@]} -eq 0 ]; then
    for browser in "${!BROWSER_PROCESS[@]}"; do
        config_dir="${BROWSER_CONFIG_DIR[$browser]}"
        if [ -d "$config_dir" ]; then
            TARGET_BROWSERS+=("$browser")
        fi
    done
fi

if [ ${#TARGET_BROWSERS[@]} -eq 0 ]; then
    echo -e "${RED}未检测到已安装的浏览器${NC}"
    echo "手动指定: ./install.sh [chrome|edge|chromium|all]"
    exit 1
fi

echo "       操作系统: $OS"
echo "       目标浏览器:"
for browser in "${TARGET_BROWSERS[@]}"; do
    echo "         - ${BROWSER_DISPLAY[$browser]}"
done

# ═══════════════════════════════════════════════════════════════════════
# 2. 计算扩展 ID（基于路径的 SHA256，各浏览器通用）
# ═══════════════════════════════════════════════════════════════════════
echo -e "${YELLOW}[2/4]${NC} 计算扩展 ID..."

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
echo "       ID: $EXT_ID"

# ═══════════════════════════════════════════════════════════════════════
# 3. 对每个浏览器安装 Native Host + 注册扩展
# ═══════════════════════════════════════════════════════════════════════
echo -e "${YELLOW}[3/4]${NC} 安装 Native Host 并注册扩展..."

chmod +x "$HOST_PY"

for browser in "${TARGET_BROWSERS[@]}"; do
    config_dir="${BROWSER_CONFIG_DIR[$browser]}"
    process_name="${BROWSER_PROCESS[$browser]}"
    display_name="${BROWSER_DISPLAY[$browser]}"
    host_template="${BROWSER_HOST_TEMPLATE[$browser]}"
    is_firefox="$([ "$browser" = "firefox" ] && echo 1 || echo 0)"

    echo ""
    echo "       ── ${display_name} ──"

    # 3a. Native Host 清单
    if [ "$is_firefox" = "1" ]; then
        host_dir="$config_dir/native-messaging-hosts"
        ext_id_fx="obsidian-word-importer@libai7l.github.io"
    else
        host_dir="$config_dir/NativeMessagingHosts"
        ext_id_fx="$EXT_ID"
    fi

    mkdir -p "$host_dir"
    manifest_file="$host_dir/com.obsidian.wordimporter.json"

    if [ "$is_firefox" = "1" ]; then
        sed -e "s|HOST_PYTHON_PATH_PLACEHOLDER|$HOST_PY|g" \
            "$host_template" > "$manifest_file"
    else
        sed -e "s|HOST_PYTHON_PATH_PLACEHOLDER|$HOST_PY|g" \
            -e "s|EXTENSION_ID_PLACEHOLDER|$EXT_ID|g" \
            "$host_template" > "$manifest_file"
    fi
    echo "       清单: $manifest_file ✓"

    # 3b. 关闭浏览器
    if [ "$is_firefox" = "1" ]; then
        if pgrep -x "firefox" > /dev/null 2>&1 || pgrep -x "firefox-esr" > /dev/null 2>&1; then
            echo "       正在关闭 Firefox..."
            pkill -x firefox 2>/dev/null || pkill -x firefox-esr 2>/dev/null || true
            sleep 2
        fi
    else
        if pgrep -x "$process_name" > /dev/null 2>&1; then
            echo "       正在关闭 ${display_name}..."
            pkill -x "$process_name" 2>/dev/null || true
            sleep 2
        elif pgrep -f "$process_name" > /dev/null 2>&1; then
            echo "       正在关闭 ${display_name}..."
            pkill -f "$process_name" 2>/dev/null || true
            sleep 2
        fi
    fi

    # 3c. 注册扩展（Chrome 系注入 Preferences，Firefox 调用 register_firefox.py）
    if [ "$is_firefox" = "1" ]; then
        REG_SCRIPT="$SCRIPT_DIR/native-host/register_firefox.py"
        chmod +x "$REG_SCRIPT"
        if $PYTHON "$REG_SCRIPT" 2>/dev/null; then
            echo "       注册: extensions.json ✓"
        else
            echo -e "       ${RED}Firefox 注册失败，请手动加载:${NC}"
            echo "         about:debugging → 此 Firefox → 加载临时附加组件"
            echo "         选择文件: $SCRIPT_DIR/manifest.json"
        fi
    else
        prefs_file="$config_dir/Default/Preferences"
        secure_prefs="$config_dir/Default/Secure Preferences"
        for prefs_path in "$prefs_file" "$secure_prefs"; do
            if [ ! -f "$prefs_path" ]; then
                continue
            fi

            $PYTHON -c "
import json

prefs_path = '''$prefs_path'''
ext_id = '$EXT_ID'
ext_path = '$SCRIPT_DIR'

with open(prefs_path, 'r') as f:
    prefs = json.load(f)

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

prefs.pop('super_mac', None)

with open(prefs_path, 'w') as f:
    json.dump(prefs, f, indent=2, ensure_ascii=False)
"
            echo "       注册: $(basename "$prefs_path") ✓"
        done
    fi
done

# ═══════════════════════════════════════════════════════════════════════
# 4. 完成
# ═══════════════════════════════════════════════════════════════════════
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              安装完成！请重启浏览器                    ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo "已安装到:"
for browser in "${TARGET_BROWSERS[@]}"; do
    echo "  ${BROWSER_DISPLAY[$browser]}"
done
echo ""
echo "验证安装:"
echo "  打开浏览器 → 访问 chrome://extensions（Edge: edge://extensions）"
echo "  确认「Obsidian Word Importer」已启用"
echo ""
echo "使用: 选中英文单词 → Ctrl+C → 自动收录到 Obsidian"
echo "配置: 点击扩展图标 → 设置 Vault 路径（可选，插件会自动检测）"
echo ""
