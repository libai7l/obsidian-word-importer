#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# Obsidian Word Importer — 一键安装脚本 (Google Chrome)
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

# 确定 Chrome 配置目录
if [ "$OS" = "Linux" ]; then
    CHROME_CONFIG_DIR="$HOME/.config/google-chrome"
elif [ "$OS" = "Darwin" ]; then
    CHROME_CONFIG_DIR="$HOME/Library/Application Support/Google/Chrome"
else
    echo -e "${RED}不支持的操作系统: $OS${NC}"
    exit 1
fi

if [ ! -d "$CHROME_CONFIG_DIR" ]; then
    echo -e "${RED}错误: 未检测到 Google Chrome${NC}"
    echo "请先安装 Chrome: https://www.google.com/chrome/"
    exit 1
fi
echo "       操作系统: $OS"
echo "       Google Chrome: 已检测到"

# ═══════════════════════════════════════════════════════════════════════
# 2. 计算扩展 ID（基于 manifest.json 中的 key）
# ═══════════════════════════════════════════════════════════════════════
echo -e "${YELLOW}[2/4]${NC} 计算扩展 ID..."

EXT_ID=$($PYTHON -c "
import json, hashlib, base64, os

manifest_path = os.path.join('$SCRIPT_DIR', 'manifest.json')
with open(manifest_path, 'r', encoding='utf-8') as f:
    manifest = json.load(f)

key_b64 = manifest.get('key', '')
if not key_b64:
    path = '$SCRIPT_DIR'.lower().encode('utf-8')
    h = hashlib.sha256(path).digest()
else:
    pubkey_der = base64.b64decode(key_b64)
    h = hashlib.sha256(pubkey_der).digest()

chars = []
for b in h[:16]:
    chars.append(chr(ord('a') + (b >> 4)))
    chars.append(chr(ord('a') + (b & 0x0f)))
print(''.join(chars[:32]))
")
echo "       ID: $EXT_ID"

# ═══════════════════════════════════════════════════════════════════════
# 3. 安装 Native Host
# ═══════════════════════════════════════════════════════════════════════
echo -e "${YELLOW}[3/4]${NC} 安装 Native Host 清单..."

chmod +x "$HOST_PY"

host_dir="$CHROME_CONFIG_DIR/NativeMessagingHosts"
mkdir -p "$host_dir"
manifest_file="$host_dir/com.obsidian.wordimporter.json"

sed -e "s|HOST_PYTHON_PATH_PLACEHOLDER|$HOST_PY|g" \
    -e "s|EXTENSION_ID_PLACEHOLDER|$EXT_ID|g" \
    "$HOST_JSON" > "$manifest_file"
echo "       清单: $manifest_file ✓"

# ═══════════════════════════════════════════════════════════════════════
# 4. 验证 Native Host
# ═══════════════════════════════════════════════════════════════════════
echo ""
echo -e "${YELLOW}[4/4]${NC} 验证 Native Host..."

VERIFY_RESULT=$($PYTHON -c "
import subprocess, json, struct, threading, sys

proc = subprocess.Popen(
    ['$HOST_PY'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

msg = json.dumps({'action': 'test'}).encode('utf-8')
proc.stdin.write(struct.pack('@I', len(msg)))
proc.stdin.write(msg)
proc.stdin.flush()

result = []
def read_resp():
    raw_len = proc.stdout.read(4)
    if raw_len and len(raw_len) == 4:
        msg_len = struct.unpack('@I', raw_len)[0]
        raw_msg = proc.stdout.read(msg_len)
        result.append(raw_msg.decode('utf-8'))

t = threading.Thread(target=read_resp)
t.start()
t.join(timeout=10)
proc.kill()

if result:
    resp = json.loads(result[0])
    if resp.get('status') == 'ok':
        print('OK:' + resp.get('message', ''))
        sys.exit(0)
sys.exit(1)
" 2>&1) || true

if echo "$VERIFY_RESULT" | grep -q "^OK:"; then
    echo -e "       ${GREEN}${VERIFY_RESULT}${NC}"
else
    echo -e "       ${RED}警告: Native host 验证失败${NC}"
    echo "       $VERIFY_RESULT"
    echo "       请检查 Python 3 是否已正确安装"
fi

# ═══════════════════════════════════════════════════════════════════════
# 完成
# ═══════════════════════════════════════════════════════════════════════
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║       Native Host 注册完成！按以下步骤加载扩展       ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}  下一步：在 Chrome 中加载扩展${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  1. 打开 chrome://extensions"
echo "  2. 开启右上角「开发者模式」(Developer mode)"
echo "  3. 点击「加载已解压的扩展程序」(Load unpacked)"
echo "  4. 选择: $SCRIPT_DIR"
echo ""
echo "  5. 加载完成后，点击扩展图标配置 Vault 路径"
echo ""
echo "使用: 选中英文单词 → Ctrl+C → 自动收录到 Obsidian"
echo ""
