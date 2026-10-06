@echo off
title StudyManager - EXE Builder
echo ============================================================
echo   StudyManager - EXE Builder
echo ============================================================
echo.

echo [1/3] Installing build tools (pyinstaller, customtkinter, pillow)...
python -m pip install --upgrade pyinstaller customtkinter pillow
if errorlevel 1 (
    echo.
    echo ERROR: pip install fail ho gaya. Python theek se install hai?
    pause
    exit /b 1
)

echo.
echo [2/3] Building StudyManager.exe (is me 2-5 minute lag sakte hain)...
python -m PyInstaller --noconfirm --onefile --windowed --name "StudyManager" --icon "assets\icons\logo.ico" --add-data "assets;assets" app.py
if errorlevel 1 (
    echo.
    echo ERROR: build fail ho gaya. Upar wali errors dekho.
    pause
    exit /b 1
)

echo.
echo [3/3] Done!
if exist "dist\StudyManager.exe" (
    echo.
    echo ============================================================
    echo   HO GAYA! dist\StudyManager.exe tayar hai.
    echo   Double-click kar ke chalao - koi kali window nahi khulegi.
    echo ============================================================
) else (
    echo ERROR: dist\StudyManager.exe nahi mili.
)
echo.
pause
