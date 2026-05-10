@echo off
:: Obsidian Word Importer - Native Messaging Host launcher for Windows
:: Chrome/Firefox native messaging requires a .bat or .exe entry point;
:: it cannot execute Python scripts directly like Linux can with shebangs.
::
:: Try the Windows py launcher first (most reliable), then python/python3.
py -3 "%~dp0host.py" 2>nul && exit /b 0
python  "%~dp0host.py" 2>nul && exit /b 0
python3 "%~dp0host.py" 2>nul && exit /b 0
echo [Obsidian Word Importer] Python not found on PATH >&2
exit /b 1
