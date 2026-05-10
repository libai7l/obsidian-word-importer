@echo off
:: Obsidian Word Importer - Native Messaging Host launcher for Windows
::
:: The install.ps1 script overwrites this file with the detected absolute
:: Python path. This file serves as a fallback for manual setups.
::
:: Chrome launches native hosts with a minimal environment; we try common
:: Python locations by absolute path before falling back to PATH.

:: Most reliable: Windows py launcher (installed system-wide)
C:\Windows\py.exe -3 "%~dp0host.py" 2>nul && exit /b 0

:: Common absolute paths for user-installed Python
"%LOCALAPPDATA%\Programs\Python\Python313\python.exe" "%~dp0host.py" 2>nul && exit /b 0
"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" "%~dp0host.py" 2>nul && exit /b 0
"%LOCALAPPDATA%\Programs\Python\Python311\python.exe" "%~dp0host.py" 2>nul && exit /b 0
"%LOCALAPPDATA%\Programs\Python\Python310\python.exe" "%~dp0host.py" 2>nul && exit /b 0

:: System-wide Python installs
C:\Python313\python.exe "%~dp0host.py" 2>nul && exit /b 0
C:\Python312\python.exe "%~dp0host.py" 2>nul && exit /b 0
C:\Python311\python.exe "%~dp0host.py" 2>nul && exit /b 0
C:\Python310\python.exe "%~dp0host.py" 2>nul && exit /b 0

:: PATH-based fallbacks (may not work from Chrome's minimal environment)
py    -3 "%~dp0host.py" 2>nul && exit /b 0
python   "%~dp0host.py" 2>nul && exit /b 0
python3  "%~dp0host.py" 2>nul && exit /b 0

echo [Obsidian Word Importer] Python not found >&2
echo [Obsidian Word Importer] Please install Python 3 from https://www.python.org/downloads/ >&2
exit /b 1
