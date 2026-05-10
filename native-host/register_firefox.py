#!/usr/bin/env python3
"""Register the extension in Firefox's extensions.json for permanent installation."""
import json, os, sys, time, glob

EXT_ID = "obsidian-word-importer@libai7l.github.io"
MANIFEST_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "manifest.json")
FF_BASE = os.path.join(os.path.expanduser("~"), ".mozilla", "firefox")

def find_profile():
    """Find the active Firefox profile directory."""
    profiles_ini = os.path.join(FF_BASE, "profiles.ini")
    if os.path.exists(profiles_ini):
        with open(profiles_ini) as f:
            content = f.read()
        # Parse ini-style sections
        import configparser
        cp = configparser.ConfigParser()
        cp.read_string(content)
        # First try the install default
        if cp.has_option("Install4F96D1932A9F858E", "Default"):
            path = os.path.join(FF_BASE, cp.get("Install4F96D1932A9F858E", "Default"))
            if os.path.isdir(path):
                return path
        # Then try profiles
        for section in cp.sections():
            if section.startswith("Profile"):
                if cp.has_option(section, "Path"):
                    path = os.path.join(FF_BASE, cp.get(section, "Path"))
                    if os.path.isdir(path) and os.path.exists(os.path.join(path, "prefs.js")):
                        return path
    # Fallback: glob for profile dirs
    for pattern in ["*.default-release", "*.default", "*.dev-edition-default"]:
        matches = glob.glob(os.path.join(FF_BASE, pattern))
        for m in matches:
            if os.path.isdir(m) and os.path.exists(os.path.join(m, "prefs.js")):
                return m
    return None

def get_manifest_version():
    try:
        with open(MANIFEST_PATH) as f:
            return json.load(f).get("version", "2.1")
    except Exception:
        return "2.1"

def register(profile_dir, ext_path):
    ext_json = os.path.join(profile_dir, "extensions.json")

    if os.path.exists(ext_json):
        with open(ext_json, "r") as f:
            data = json.load(f)
    else:
        data = {"schemaVersion": 31, "addons": []}

    # Remove old entry
    data["addons"] = [a for a in data.get("addons", []) if a.get("id") != EXT_ID]

    version = get_manifest_version()
    now_ms = int(time.time() * 1000)

    data["addons"].append({
        "id": EXT_ID,
        "syncGUID": EXT_ID + "-guid",
        "location": 0,
        "version": version,
        "type": "extension",
        "internalName": None,
        "updateURL": None,
        "updateKey": None,
        "optionsURL": None,
        "optionsType": None,
        "aboutURL": None,
        "iconURL": None,
        "icon64URL": None,
        "defaultLocale": {
            "name": "Obsidian Word Importer",
            "description": "选中英文单词 Ctrl+C 收录到 Obsidian",
            "creator": "libai7l",
        },
        "visible": True,
        "active": True,
        "userDisabled": False,
        "appDisabled": False,
        "embedderDisabled": False,
        "installDate": now_ms,
        "updateDate": now_ms,
        "applyBackgroundUpdates": 1,
        "path": ext_path,
        "unsigned": True,
        "sourceURI": None,
        "releaseNotesURI": None,
        "softDisabled": False,
        "foreignInstall": True,
        "strictCompatibility": False,
        "hasEmbeddedWebExtension": False,
        "isWebExtension": True,
        "isPlatformCompatible": True,
    })

    with open(ext_json, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Enable unsigned extensions
    prefs_js = os.path.join(profile_dir, "prefs.js")
    prefs_to_add = [
        'user_pref("extensions.autoDisableScopes", 0);',
        'user_pref("extensions.enabledScopes", 15);',
    ]
    if os.path.exists(prefs_js):
        with open(prefs_js, "r") as f:
            existing = f.read()
        with open(prefs_js, "a") as f:
            for pref in prefs_to_add:
                if pref not in existing:
                    f.write("\n" + pref + "\n")

    print(f"注册成功: {ext_json}")
    print(f"扩展 ID: {EXT_ID}")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        profile_dir = sys.argv[1]
    else:
        profile_dir = find_profile()

    if not profile_dir or not os.path.isdir(profile_dir):
        print("错误: 未找到 Firefox 配置文件", file=sys.stderr)
        sys.exit(1)

    ext_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    register(profile_dir, ext_path)
