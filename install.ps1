# ═══════════════════════════════════════════════════════════════════════
# Obsidian Word Importer - Windows 一键安装脚本 (Google Chrome)
# 用法:
#   powershell -ExecutionPolicy Bypass -File install.ps1
# ═══════════════════════════════════════════════════════════════════════

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$HostBat  = Join-Path $ScriptDir "native-host\host.bat"
$HostJson = Join-Path $ScriptDir "native-host\host.json"

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   Obsidian Word Importer v2.1 - Windows 一键安装" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# ═══════════════════════════════════════════════════════════════════════
# 1. 检测环境
# ═══════════════════════════════════════════════════════════════════════
Write-Host "[1/5] 检测环境..." -ForegroundColor Yellow

# 检测 Python
$Python     = $null
$PythonPath = $null
foreach ($cmd in @("python", "python3", "py")) {
    $result = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($result) {
        try {
            $ver = & $cmd --version 2>&1
            Write-Host "       Python: $ver"
            $Python     = $cmd
            $PythonPath = $result.Source
            break
        } catch {}
    }
}

if (-not $Python) {
    Write-Host "错误: 未找到 Python 3，请先安装 Python" -ForegroundColor Red
    Write-Host "下载: https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $HostBat)) {
    Write-Host "错误: 未找到 native-host\host.bat" -ForegroundColor Red
    exit 1
}

# 使用绝对路径重写 host.bat，Chrome 进程环境可能没有完整 PATH
$HostBatContent = @"
@echo off
"$PythonPath" "%~dp0host.py" %*
"@
Set-Content -Path $HostBat -Value $HostBatContent -Encoding ASCII
Write-Host "       host.bat -> $PythonPath" -ForegroundColor Gray

# 确认 Chrome 已安装
$ChromeConfigDir = "$env:LOCALAPPDATA\Google\Chrome"
if (-not (Test-Path $ChromeConfigDir)) {
    Write-Host "错误: 未检测到 Google Chrome" -ForegroundColor Red
    Write-Host "下载: https://www.google.com/chrome/" -ForegroundColor Red
    exit 1
}
Write-Host "       Google Chrome: 已检测到" -ForegroundColor Green

# ═══════════════════════════════════════════════════════════════════════
# 2. 计算扩展 ID（基于 manifest.json 中的 key）
# ═══════════════════════════════════════════════════════════════════════
Write-Host "[2/5] 计算扩展 ID..." -ForegroundColor Yellow

$ExtIdScript = @"
import json, hashlib, base64, os

manifest_path = os.path.join(r'$ScriptDir', 'manifest.json')
with open(manifest_path, 'r', encoding='utf-8') as f:
    manifest = json.load(f)

key_b64 = manifest.get('key', '')
if not key_b64:
    path = r'$ScriptDir'.lower().encode('utf-8')
    h = hashlib.sha256(path).digest()
else:
    pubkey_der = base64.b64decode(key_b64)
    h = hashlib.sha256(pubkey_der).digest()

chars = []
for b in h[:16]:
    chars.append(chr(ord('a') + (b >> 4)))
    chars.append(chr(ord('a') + (b & 0x0f)))
print(''.join(chars[:32]))
"@

$ExtId = & $Python -c $ExtIdScript
Write-Host "       ID: $ExtId"

# ═══════════════════════════════════════════════════════════════════════
# 3. 安装 Native Host
# ═══════════════════════════════════════════════════════════════════════
Write-Host "[3/5] 安装 Native Host 清单..." -ForegroundColor Yellow

$hostJsonContent = Get-Content $HostJson -Raw -Encoding UTF8
$hostJsonContent = $hostJsonContent.Replace("HOST_PYTHON_PATH_PLACEHOLDER", $HostBat.Replace("\", "\\"))
$hostJsonContent = $hostJsonContent.Replace("EXTENSION_ID_PLACEHOLDER", $ExtId)

$hostDir = Join-Path $ChromeConfigDir "NativeMessagingHosts"
if (-not (Test-Path $hostDir)) {
    New-Item -ItemType Directory -Path $hostDir -Force | Out-Null
}

$manifestFile = Join-Path $hostDir "com.obsidian.wordimporter.json"
Set-Content -Path $manifestFile -Value $hostJsonContent -Encoding UTF8
Write-Host "       清单: $manifestFile" -ForegroundColor Green

# 注册表项（Windows 双保险）
$regPath = "HKCU:\Software\Google\Chrome\NativeMessagingHosts\com.obsidian.wordimporter"
New-Item -Path $regPath -Force | Out-Null
Set-ItemProperty -Path $regPath -Name "(Default)" -Value $manifestFile -Type String -Force
Write-Host "       注册表: HKCU\...\NativeMessagingHosts\com.obsidian.wordimporter" -ForegroundColor Green

# ═══════════════════════════════════════════════════════════════════════
# 4. 验证 Native Host
# ═══════════════════════════════════════════════════════════════════════
Write-Host ""
Write-Host "[4/5] 验证 Native Host..." -ForegroundColor Yellow

$VerifyScript = @"
import subprocess, json, struct, sys, threading

proc = subprocess.Popen(
    [r'$HostBat'],
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
        print('SUCCESS:' + resp.get('message', ''))
        sys.exit(0)
    else:
        print('WARN:' + resp.get('message', ''))
        sys.exit(0)
else:
    stderr = proc.stderr.read().decode('utf-8', errors='replace')
    print('FAIL: Native host 无响应')
    if stderr:
        print('STDERR:' + stderr)
    sys.exit(1)
"@

$verifyResult = & $Python -c $VerifyScript 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "       警告: Native host 验证失败" -ForegroundColor Red
    Write-Host "       $verifyResult" -ForegroundColor Red
} else {
    Write-Host "       $verifyResult" -ForegroundColor Green
}

# ═══════════════════════════════════════════════════════════════════════
# 5. 完成
# ═══════════════════════════════════════════════════════════════════════
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "                 安装完成！请按以下步骤加载扩展" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host "  下一步：在 Chrome 中加载扩展" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. 打开: chrome://extensions"
Write-Host "  2. 开启右上角「开发者模式」(Developer mode)"
Write-Host "  3. 点击「加载已解压的扩展程序」(Load unpacked)"
Write-Host "  4. 选择: $ScriptDir"
Write-Host ""
Write-Host "  5. 加载完成后，点击扩展图标配置 Vault 路径" -ForegroundColor White
Write-Host ""
Write-Host "使用: 选中英文单词 -> Ctrl+C -> 自动收录到 Obsidian"

try {
    Start-Process "chrome://extensions" -ErrorAction SilentlyContinue
    Write-Host ""
    Write-Host "已自动打开 Chrome 扩展管理页面" -ForegroundColor Gray
} catch {}
