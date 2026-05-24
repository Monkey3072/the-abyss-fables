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

set PY_CMD=
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Using: python
    set PY_CMD=python
) else (
    py --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo Using: py
        set PY_CMD=py
    ) else (
        echo.
        echo [ERROR] Python not found!
        echo.
        echo Please ensure:
        echo   1. Python is installed
        echo   2. Python is added to PATH environment variable
        echo.
        pause
        exit /b 1
    )
)

echo.
echo Starting game...
echo.

%PY_CMD% main.py
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
