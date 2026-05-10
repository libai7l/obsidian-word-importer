# ═══════════════════════════════════════════════════════════════════════
# Obsidian Word Importer - Windows 一键安装脚本
# 支持 Chrome / Edge / Chromium
# 用法:
#   powershell -ExecutionPolicy Bypass -File install.ps1
#   powershell -ExecutionPolicy Bypass -File install.ps1 -Browser chrome
#   powershell -ExecutionPolicy Bypass -File install.ps1 -Browser edge
#   powershell -ExecutionPolicy Bypass -File install.ps1 -Browser all
# ═══════════════════════════════════════════════════════════════════════
param(
    [string]$Browser = ""
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$HostPy = Join-Path $ScriptDir "native-host\host.py"
$HostJson = Join-Path $ScriptDir "native-host\host.json"

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   Obsidian Word Importer v2.1 - Windows 一键安装" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# ═══════════════════════════════════════════════════════════════════════
# 1. 检测环境
# ═══════════════════════════════════════════════════════════════════════
Write-Host "[1/4] 检测环境..." -ForegroundColor Yellow

# 检测 Python
$Python = $null
foreach ($cmd in @("python", "python3", "py")) {
    $result = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($result) {
        try {
            $ver = & $cmd --version 2>&1
            Write-Host "       Python: $ver"
            $Python = $cmd
            break
        } catch {}
    }
}

if (-not $Python) {
    Write-Host "错误: 未找到 Python 3，请先安装 Python" -ForegroundColor Red
    Write-Host "下载: https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

# 操作系统
Write-Host "       操作系统: Windows"

# ── 浏览器配置表 ──
$Browsers = @{
    "chrome" = @{
        "Process" = "chrome"
        "ConfigDir" = "$env:LOCALAPPDATA\Google\Chrome"
        "Display" = "Google Chrome"
    }
    "edge" = @{
        "Process" = "msedge"
        "ConfigDir" = "$env:LOCALAPPDATA\Microsoft\Edge"
        "Display" = "Microsoft Edge"
    }
    "chromium" = @{
        "Process" = "chrome"
        "ConfigDir" = "$env:LOCALAPPDATA\Chromium"
        "Display" = "Chromium"
    }
}

# ── 确定要安装的目标浏览器 ──
$TargetBrowsers = @()
if ($Browser) {
    $choices = $Browser -split ','
    foreach ($c in $choices) {
        $c = $c.Trim().ToLower()
        if ($c -eq "all") {
            $TargetBrowsers = $Browsers.Keys
            break
        }
        if ($Browsers.ContainsKey($c)) {
            $TargetBrowsers += $c
        } else {
            Write-Host "未知浏览器: $c (支持: chrome, edge, chromium, all)" -ForegroundColor Red
            exit 1
        }
    }
}

# 如果没指定，自动检测已安装的浏览器
if ($TargetBrowsers.Count -eq 0) {
    foreach ($key in $Browsers.Keys) {
        $configDir = $Browsers[$key].ConfigDir
        if (Test-Path $configDir) {
            $TargetBrowsers += $key
        }
    }
}

if ($TargetBrowsers.Count -eq 0) {
    Write-Host "未检测到已安装的浏览器" -ForegroundColor Red
    Write-Host "手动指定: .\install.ps1 -Browser chrome|edge|chromium|all" -ForegroundColor Yellow
    exit 1
}

Write-Host "       目标浏览器:"
foreach ($b in $TargetBrowsers) {
    Write-Host "         - $($Browsers[$b].Display)"
}

# ═══════════════════════════════════════════════════════════════════════
# 2. 计算扩展 ID
# ═══════════════════════════════════════════════════════════════════════
Write-Host "[2/4] 计算扩展 ID..." -ForegroundColor Yellow

$ExtIdScript = @"
import hashlib
path = r'$ScriptDir'.lower().encode('utf-8')
h = hashlib.sha256(path).digest()
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
Write-Host "[3/4] 安装 Native Host..." -ForegroundColor Yellow

foreach ($b in $TargetBrowsers) {
    $configDir = $Browsers[$b].ConfigDir
    $processName = $Browsers[$b].Process
    $displayName = $Browsers[$b].Display

    Write-Host ""
    Write-Host "       --- $displayName ---"

    # Native Host 清单目录
    $hostDir = Join-Path $configDir "NativeMessagingHosts"
    if (-not (Test-Path $hostDir)) {
        New-Item -ItemType Directory -Path $hostDir -Force | Out-Null
    }

    $manifestFile = Join-Path $hostDir "com.obsidian.wordimporter.json"

    # 生成清单
    $hostJsonContent = Get-Content $HostJson -Raw -Encoding UTF8
    $hostJsonContent = $hostJsonContent.Replace("HOST_PYTHON_PATH_PLACEHOLDER", $HostPy.Replace("\", "\\"))
    $hostJsonContent = $hostJsonContent.Replace("EXTENSION_ID_PLACEHOLDER", $ExtId)
    Set-Content -Path $manifestFile -Value $hostJsonContent -Encoding UTF8
    Write-Host "       清单: $manifestFile" -ForegroundColor Green

    # 关闭浏览器
    $proc = Get-Process -Name $processName -ErrorAction SilentlyContinue
    if ($proc) {
        Write-Host "       正在关闭 $displayName..."
        $proc | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }

    # 注册扩展（注入 Preferences）
    $prefsPaths = @(
        (Join-Path $configDir "Default\Preferences"),
        (Join-Path $configDir "Default\Secure Preferences")
    )

    foreach ($prefsPath in $prefsPaths) {
        if (-not (Test-Path $prefsPath)) { continue }

        $prefsScript = @"
import json

prefs_path = r'$prefsPath'
ext_id = '$ExtId'
ext_path = r'$ScriptDir'
manifest_path = r'$(Join-Path $ScriptDir "manifest.json")'

with open(prefs_path, 'r', encoding='utf-8') as f:
    prefs = json.load(f)

with open(manifest_path, 'r', encoding='utf-8') as f:
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

with open(prefs_path, 'w', encoding='utf-8') as f:
    json.dump(prefs, f, indent=2, ensure_ascii=False)
"@
        & $Python -c $prefsScript 2>$null
        $prefsName = Split-Path -Leaf $prefsPath
        Write-Host "       注册: $prefsName" -ForegroundColor Green
    }
}

# ═══════════════════════════════════════════════════════════════════════
# 4. 完成
# ═══════════════════════════════════════════════════════════════════════
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "               安装完成！请重启浏览器" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "已安装到:"
foreach ($b in $TargetBrowsers) {
    Write-Host "  $($Browsers[$b].Display)"
}
Write-Host ""
Write-Host "验证安装:"
Write-Host "  打开浏览器 -> 访问 chrome://extensions （Edge: edge://extensions）"
Write-Host "  确认 [Obsidian Word Importer] 已启用"
Write-Host ""
Write-Host "使用: 选中英文单词 -> Ctrl+C -> 自动收录到 Obsidian"
Write-Host "配置: 点击扩展图标 -> 设置 Vault 路径"
Write-Host ""
