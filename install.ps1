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
Write-Host "   Obsidian Word Importer v3.0 - Windows 一键安装" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# ═══════════════════════════════════════════════════════════════════════
# 1. 检测环境
# ═══════════════════════════════════════════════════════════════════════
Write-Host "[1/5] 检测环境..." -ForegroundColor Yellow

# 检测 Node.js
$Node     = $null
$NodePath = $null
foreach ($cmd in @("node")) {
    $result = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($result) {
        try {
            $ver = & $cmd --version 2>&1
            Write-Host "       Node.js: $ver"
            $Node     = $cmd
            $NodePath = $result.Source
            break
        } catch {}
    }
}

if (-not $Node) {
    Write-Host "错误: 未找到 Node.js，请先安装 Node.js" -ForegroundColor Red
    Write-Host "下载: https://nodejs.org/" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $HostBat)) {
    Write-Host "错误: 未找到 native-host\host.bat" -ForegroundColor Red
    exit 1
}

# 使用绝对路径重写 host.bat，Chrome 进程环境可能没有完整 PATH
$HostBatContent = '@echo off' + "`r`n" + '"' + $NodePath + '" "%~dp0host.js" %*'
Set-Content -Path $HostBat -Value $HostBatContent -Encoding ASCII
Write-Host "       host.bat -> $NodePath" -ForegroundColor Gray

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

# Prepare paths with escaped backslashes for use in JS strings
$ScriptDirEscaped = $ScriptDir.Replace("\", "\\")
$ScriptDirLowerEscaped = $ScriptDir.ToLower().Replace("\", "\\")

$ExtIdScript = @"
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const manifest = JSON.parse(fs.readFileSync(path.join('$ScriptDirEscaped', 'manifest.json'), 'utf-8'));
const keyB64 = manifest.key || '';
let h;
if (keyB64) {
    h = crypto.createHash('sha256').update(Buffer.from(keyB64, 'base64')).digest();
} else {
    h = crypto.createHash('sha256').update('$ScriptDirLowerEscaped').digest();
}
const chars = [];
for (let i = 0; i < 16; i++) {
    chars.push(String.fromCharCode(97 + (h[i] >> 4)));
    chars.push(String.fromCharCode(97 + (h[i] & 0x0f)));
}
console.log(chars.slice(0, 32).join(''));
"@

$ExtId = & $Node -e $ExtIdScript
Write-Host "       ID: $ExtId"

# ═══════════════════════════════════════════════════════════════════════
# 3. 安装 Native Host
# ═══════════════════════════════════════════════════════════════════════
Write-Host "[3/5] 安装 Native Host 清单..." -ForegroundColor Yellow

$hostJsonContent = Get-Content $HostJson -Raw -Encoding UTF8
$hostJsonContent = $hostJsonContent.Replace("HOST_NODE_PATH_PLACEHOLDER", $HostBat.Replace("\", "\\"))
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

$HostBatEscaped = $HostBat.Replace("\", "\\")

$VerifyScript = @"
const childProcess = require('child_process');

const proc = childProcess.spawn('$HostBatEscaped', [], {
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
            console.log('SUCCESS:' + resp.message);
            process.exit(0);
        } else {
            console.log('WARN:' + (resp.message || ''));
            process.exit(0);
        }
    } else {
        console.log('FAIL: Native host 无响应');
        if (stderr) console.log('STDERR:' + stderr);
        process.exit(1);
    }
});
"@

$verifyResult = & $Node -e $VerifyScript 2>&1
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
