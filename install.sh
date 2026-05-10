#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# Obsidian Word Importer v3.0 — 一键安装脚本 (Google Chrome)
# ═══════════════════════════════════════════════════════════════════════
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║   Obsidian Word Importer v3.0 — 一键安装            ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOST_JS="$SCRIPT_DIR/native-host/host.js"
HOST_JSON="$SCRIPT_DIR/native-host/host.json"

# ═══════════════════════════════════════════════════════════════════════
# 1. 检测环境
# ═══════════════════════════════════════════════════════════════════════
echo -e "${YELLOW}[1/4]${NC} 检测环境..."

NODE=""
for cmd in node; do
    if command -v "$cmd" &>/dev/null; then
        NODE="$cmd"
        break
    fi
done
if [ -z "$NODE" ]; then
    echo -e "${RED}错误: 未找到 Node.js，请先安装${NC}"
    echo "下载: https://nodejs.org/"
    exit 1
fi
echo "       Node.js: $($NODE --version)"

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

EXT_ID=$($NODE -e "
const crypto = require('crypto');
const fs = require('fs');
const manifest = JSON.parse(fs.readFileSync('$SCRIPT_DIR/manifest.json', 'utf-8'));
const keyB64 = manifest.key || '';
let h;
if (keyB64) {
    h = crypto.createHash('sha256').update(Buffer.from(keyB64, 'base64')).digest();
} else {
    h = crypto.createHash('sha256').update('$SCRIPT_DIR'.toLowerCase()).digest();
}
const chars = [];
for (let i = 0; i < 16; i++) {
    chars.push(String.fromCharCode(97 + (h[i] >> 4)));
    chars.push(String.fromCharCode(97 + (h[i] & 0x0f)));
}
process.stdout.write(chars.slice(0, 32).join(''));
")
echo "       ID: $EXT_ID"

# ═══════════════════════════════════════════════════════════════════════
# 3. 安装 Native Host
# ═══════════════════════════════════════════════════════════════════════
echo -e "${YELLOW}[3/4]${NC} 安装 Native Host 清单..."

chmod +x "$HOST_JS"

host_dir="$CHROME_CONFIG_DIR/NativeMessagingHosts"
mkdir -p "$host_dir"
manifest_file="$host_dir/com.obsidian.wordimporter.json"

sed -e "s|HOST_NODE_PATH_PLACEHOLDER|$HOST_JS|g" \
    -e "s|EXTENSION_ID_PLACEHOLDER|$EXT_ID|g" \
    "$HOST_JSON" > "$manifest_file"
echo "       清单: $manifest_file ✓"

# ═══════════════════════════════════════════════════════════════════════
# 4. 验证 Native Host
# ═══════════════════════════════════════════════════════════════════════
echo ""
echo -e "${YELLOW}[4/4]${NC} 验证 Native Host..."

VERIFY_RESULT=$($NODE -e "
const childProcess = require('child_process');

const proc = childProcess.spawn('$HOST_JS', [], {
    stdio: ['pipe', 'pipe', 'pipe']
});

const msg = JSON.stringify({action: 'test'});
const lenBuf = Buffer.alloc(4);
lenBuf.writeUInt32LE(Buffer.byteLength(msg, 'utf-8'), 0);

proc.stdin.write(lenBuf);
proc.stdin.write(msg);
proc.stdin.end();

const chunks = [];
const errChunks = [];
proc.stdout.on('data', (c) => chunks.push(c));
proc.stderr.on('data', (c) => errChunks.push(c));

proc.on('close', () => {
    const stdout = Buffer.concat(chunks);
    const stderr = Buffer.concat(errChunks).toString();
    if (stdout.length >= 4) {
        const respLen = stdout.slice(0, 4).readUInt32LE(0);
        const resp = JSON.parse(stdout.slice(4, 4 + respLen).toString());
        if (resp.status === 'ok') {
            process.stdout.write('OK:' + resp.message);
            process.exit(0);
        }
    }
    process.stderr.write(stderr);
    process.exit(1);
});
" 2>&1) || true

if echo "$VERIFY_RESULT" | grep -q "^OK:"; then
    echo -e "       ${GREEN}${VERIFY_RESULT}${NC}"
else
    echo -e "       ${RED}警告: Native host 验证失败${NC}"
    echo "       $VERIFY_RESULT"
    echo "       请检查 Node.js 是否已正确安装"
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
