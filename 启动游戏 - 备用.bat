@echo off
title Deep Abyss Fable - Starting...
cd /d "%~dp0"
echo.
echo ========================================
echo       Deep Abyss Fable
echo       Text Adventure Game
echo ========================================
echo.
echo Current directory: %cd%
echo.

python main.py
set EXIT_CODE=%errorlevel%

echo.
echo ========================================
if %EXIT_CODE% equ 0 (
    echo Game exited normally.
) else (
    echo [ERROR] Game exited with code: %EXIT_CODE%
)
echo ========================================
echo.
pause
