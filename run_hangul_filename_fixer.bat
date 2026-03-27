@echo off
setlocal
cd /d "%~dp0"

where pyw >nul 2>nul
if %errorlevel%==0 (
    start "" pyw -3 "%~dp0hangul_filename_fixer.py" %*
    exit /b 0
)

py -3 "%~dp0hangul_filename_fixer.py" %*
