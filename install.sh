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
HOST_DIR="$SCRIPT_DIR/native-host"
HOST_JS="$HOST_DIR/host.js"
HOST_JSON="$HOST_DIR/host.json"
EXTID_JS="$HOST_DIR/extid.js"
VERIFY_JS="$HOST_DIR/verify.js"

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
# 2. 计算扩展 ID
# ═══════════════════════════════════════════════════════════════════════
echo -e "${YELLOW}[2/4]${NC} 计算扩展 ID..."

EXT_ID=$($NODE "$EXTID_JS")
echo "       ID: $EXT_ID"

# ═══════════════════════════════════════════════════════════════════════
# 3. 安装 Native Host
# ═══════════════════════════════════════════════════════════════════════
echo -e "${YELLOW}[3/4]${NC} 安装 Native Host 清单..."

chmod +x "$HOST_JS" "$EXTID_JS" "$VERIFY_JS"

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

VERIFY_RESULT=$($NODE "$VERIFY_JS" "$HOST_JS" 2>&1) || true

if echo "$VERIFY_RESULT" | grep -q "^SUCCESS:"; then
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
