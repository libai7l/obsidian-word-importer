#!/usr/bin/env python3
"""Register the extension in Firefox for permanent installation.

Two strategies:
  1. Developer Edition / Nightly / ESR: proxy file in extensions/ dir
  2. Regular Firefox: must use signed XPI (web-ext sign) or about:debugging

Firefox regular release requires all extensions to be signed by Mozilla.
The proxy-file method only works on Firefox Developer Edition, Nightly, or ESR
where xpinstall.signatures.required can be set to false.
"""
import json, os, sys, time, glob, re, subprocess

EXT_ID = "obsidian-word-importer@libai7l.github.io"
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST_PATH = os.path.join(SCRIPT_DIR, "manifest.json")
FF_BASE = os.path.join(os.path.expanduser("~"), ".mozilla", "firefox")


def find_profile():
    """Find the active Firefox profile directory."""
    profiles_ini = os.path.join(FF_BASE, "profiles.ini")
    if not os.path.exists(profiles_ini):
        return None
    import configparser
    cp = configparser.ConfigParser()
    cp.read(profiles_ini)
    # First try the install default
    for section in cp.sections():
        if section.startswith("Install") and cp.has_option(section, "Default"):
            path = os.path.join(FF_BASE, cp.get(section, "Default"))
            if os.path.isdir(path):
                return path
    # Then any profile with prefs.js
    for section in cp.sections():
        if section.startswith("Profile") and cp.has_option(section, "Path"):
            path = os.path.join(FF_BASE, cp.get(section, "Path"))
            if os.path.isdir(path) and os.path.exists(os.path.join(path, "prefs.js")):
                return path
    # Fallback: glob
    import glob as g
    for pattern in ["*.default-release", "*.default"]:
        for m in sorted(g.glob(os.path.join(FF_BASE, pattern))):
            if os.path.isdir(m) and os.path.exists(os.path.join(m, "prefs.js")):
                return m
    return None


def get_firefox_channel():
    """Determine Firefox channel: release, beta, nightly, esr, or dev-edition."""
    try:
        result = subprocess.run(["firefox", "--version"], capture_output=True, text=True, timeout=5)
        ver = result.stdout + result.stderr
        if "Developer Edition" in ver or "dev-edition" in ver:
            return "dev"
        if "Nightly" in ver or "a1" in ver:
            return "nightly"
        if "ESR" in ver or "esr" in ver.lower():
            return "esr"
        if "Beta" in ver or "b" in ver.split("Firefox ")[-1][:2] if "Firefox" in ver else False:
            return "beta"
        return "release"
    except Exception:
        return "unknown"


def set_prefs(profile_dir):
    """Set Firefox preferences to allow loading our extension."""
    prefs_js = os.path.join(profile_dir, "prefs.js")
    prefs_needed = [
        'user_pref("extensions.autoDisableScopes", 0);',
        'user_pref("extensions.enabledScopes", 15);',
        'user_pref("xpinstall.signatures.required", false);',
    ]
    existing = ""
    if os.path.exists(prefs_js):
        with open(prefs_js, "r") as f:
            existing = f.read()
    added = []
    with open(prefs_js, "a") as f:
        for pref in prefs_needed:
            if pref.split("(")[1].split(",")[0] not in existing:
                f.write("\n" + pref + "\n")
                added.append(pref.split(",")[0].split('"')[1])
    return added


def install_proxy(profile_dir, ext_path):
    """Install via proxy file (works on Dev Edition / Nightly / ESR)."""
    ext_dir = os.path.join(profile_dir, "extensions")
    os.makedirs(ext_dir, exist_ok=True)

    proxy_file = os.path.join(ext_dir, EXT_ID)
    with open(proxy_file, "w") as f:
        f.write(ext_path + "\n")
    return proxy_file


def build_xpi():
    """Build an unsigned XPI (zip) file for the extension."""
    import zipfile, tempfile
    xpi_path = os.path.join(SCRIPT_DIR, "obsidian-word-importer.xpi")
    with zipfile.ZipFile(xpi_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(SCRIPT_DIR):
            # Skip files we don't want in the XPI
            dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "native-host")]
            for fn in files:
                if fn in (".gitignore", "key.pem", "install.sh", "obsidian-word-importer.xpi"):
                    continue
                if fn.endswith(".py") or fn == "host.json" or fn == "host.firefox.json":
                    continue
                full = os.path.join(root, fn)
                arcname = os.path.relpath(full, SCRIPT_DIR)
                zf.write(full, arcname)
    return xpi_path


def register(profile_dir, ext_path):
    channel = get_firefox_channel()
    print(f"Firefox 版本通道: {channel}")

    # Set prefs in either case
    prefs_added = set_prefs(profile_dir)
    if prefs_added:
        print(f"已设置偏好: {', '.join(prefs_added)}")

    if channel in ("dev", "nightly", "esr"):
        # Proxy file approach works
        proxy = install_proxy(profile_dir, ext_path)
        print(f"代理文件: {proxy}")
        print(f"扩展目录: {ext_path}")
        print("✓ Firefox 永久安装成功！重启 Firefox 后生效。")
        return True

    else:
        # Regular Firefox: try proxy file anyway, but warn
        proxy = install_proxy(profile_dir, ext_path)
        print(f"代理文件: {proxy}")

        # Build XPI for easy installation
        try:
            xpi = build_xpi()
            print(f"已构建 XPI: {xpi}")
            print()
            print("⚠️  Firefox 正式版要求扩展必须通过 Mozilla 签名。")
            print("    请选择以下方式之一:")
            print()
            print("    方式1 (推荐): 安装 Firefox Developer Edition")
            print("      wget -O /tmp/firefox-dev.tar.bz2 \\")
            print("        'https://download.mozilla.org/?product=firefox-devedition-latest-ssl&os=linux64&lang=zh-CN'")
            print("      sudo tar -xjf /tmp/firefox-dev.tar.bz2 -C /opt/")
            print("      sudo ln -sf /opt/firefox/firefox /usr/local/bin/firefox-dev")
            print("      然后运行 firefox-dev --no-remote & 启动后重新运行 ./install.sh")
            print()
            print("    方式2: 提交到 Mozilla Add-ons 签名")
            print("      打开 https://addons.mozilla.org/developers/addon/submit/")
            print(f"     上传文件: {xpi}")
            print("      选择「不公开列出」→ 下载签名的 XPI → 拖入 Firefox 窗口")
            print()
            print("    方式3: 临时加载 (每次重启浏览器后需重新加载)")
            print("      打开 about:debugging")
            print("      点击「此 Firefox」→「临时加载附加组件」")
            print(f"     选择: {os.path.join(SCRIPT_DIR, 'manifest.json')}")
            return False
        except Exception as e:
            print(f"构建 XPI 失败: {e}")
            return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        profile_dir = sys.argv[1]
    else:
        profile_dir = find_profile()

    if not profile_dir or not os.path.isdir(profile_dir):
        print("错误: 未找到 Firefox 配置文件", file=sys.stderr)
        sys.exit(1)

    ext_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    success = register(profile_dir, ext_path)
    sys.exit(0 if success else 1)

