@echo off
:: Obsidian Word Importer - Native Messaging Host launcher for Windows
::
:: The install.ps1 script overwrites this file with the detected absolute
:: Node.js path. This file serves as a fallback for manual setups.
::
:: Chrome launches native hosts with a minimal environment; we try common
:: Node.js locations by absolute path before falling back to PATH.

:: Common absolute paths for user-installed Node.js
"%ProgramFiles%\nodejs\node.exe" "%~dp0host.js" 2>nul && exit /b 0
"%LOCALAPPDATA%\Programs\nodejs\node.exe" "%~dp0host.js" 2>nul && exit /b 0
"%ProgramFiles(x86)%\nodejs\node.exe" "%~dp0host.js" 2>nul && exit /b 0

:: PATH-based fallbacks (may not work from Chrome's minimal environment)
node    "%~dp0host.js" 2>nul && exit /b 0

echo [Obsidian Word Importer] Node.js not found >&2
echo [Obsidian Word Importer] Please install Node.js from https://nodejs.org/ >&2
exit /b 1
