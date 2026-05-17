# Changelog

## v3.0.2

- Stripped UI noise prefixes (e.g., "评论：", "翻译：") from page translations so only the actual meaning is saved.
- Added quality gate in native host: discards page translation when too short relative to the input word, falling back to API results.
- Normalized Unicode punctuation (ellipsis, zero-width spaces, soft hyphens) in copied text so sentences with smart formatting pass validation.
- Increased input character limit from 500 to 800 and HTTP timeout from 5s to 10s for longer sentences.
- Removed etymology from desktop notifications; keep it only in the Obsidian Markdown file.
- Changed etymology line format from `← *etymology*` to `> etymology` (blockquote) for clearer visual separation.
- Added "注释", "说明", "注意", "提示", "备注", "翻译" to UI noise detection in both content script and native host.

## v3.0.1

- Added support for English phrases and sentences with punctuation, up to 500 characters.
- Rejected page-translation UI labels such as `评论：` before using page text as the meaning.
- Fixed Immersive Translate target extraction so Chinese text still passes translation validation.
- Normalized Dictionary API part-of-speech labels, for example `noun/adjective.` to `n./adj.`.
- Skipped pronunciation/POS/etymology lookups for long sentences to avoid misleading word-level metadata.
- Truncated long notification titles while keeping the full entry in Obsidian.

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
