# Changelog

## v3.0.0

- Replaced the Python native host with a Node.js native host.
- Fixed Vault auto-detection by allowing the native host to run when the popup Vault path is empty.
- Fixed phrase parsing so entries such as `survey methodology` are detected as complete phrases.
- Fixed rotated word files for nested target paths, for example `6英语/论文单词1.md`.
- Added target-file path validation to prevent writes outside the configured Vault.
- Improved Immersive Translate extraction selectors and bounded fallback DOM scans.
- Fixed Windows native-host verification for `.bat` launchers.
- Changed the Windows installer to generate a launcher in Chrome's Native Messaging directory instead of rewriting the tracked `native-host/host.bat`.
- Reduced Chrome extension permissions to only the permissions currently used.
