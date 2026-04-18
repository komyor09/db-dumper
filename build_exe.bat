@echo off

echo.
echo  =========================================
echo   db_dump GUI - Build EXE (PyInstaller)
echo  =========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found in PATH
    pause & exit /b 1
)

echo  [1/5] Checking PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo  [1/5] Installing PyInstaller...
    pip install pyinstaller --quiet
)
echo  [1/5] PyInstaller OK

echo  [2/5] Checking files...
if not exist "db_dump.py" (
    echo  [ERROR] db_dump.py not found
    pause & exit /b 1
)
if not exist "db_dump_gui.py" (
    echo  [ERROR] db_dump_gui.py not found
    pause & exit /b 1
)
echo  [2/5] Files OK

echo  [3/5] Converting icon.png to icon.ico...
set ICON_FLAG=
if exist "icon.png" (
    pip show pillow >nul 2>&1
    if errorlevel 1 (
        echo  [3/5] Installing Pillow for icon conversion...
        pip install pillow --quiet
    )
    python -c "from PIL import Image; img=Image.open('icon.png'); img.save('icon.ico', format='ICO', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])"
    if errorlevel 1 (
        echo  [3/5] WARNING: icon conversion failed, building without icon
    ) else (
        set ICON_FLAG=--icon=icon.ico
        echo  [3/5] Icon OK - icon.ico created
    )
) else (
    echo  [3/5] icon.png not found - building without icon
)

echo  [4/5] Cleaning old builds...
if exist "dist"           rmdir /s /q dist
if exist "build"          rmdir /s /q build
if exist "db_dump_gui.spec" del /q db_dump_gui.spec
echo  [4/5] Clean OK

echo  [5/5] Building exe...
echo.

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "db_dump_gui" ^
    --add-data "db_dump.py;." ^
    --hidden-import tkinter ^
    --hidden-import tkinter.ttk ^
    --hidden-import tkinter.filedialog ^
    --hidden-import tkinter.messagebox ^
    %ICON_FLAG% ^
    db_dump_gui.py

if errorlevel 1 (
    echo.
    echo  [ERROR] Build failed
    pause & exit /b 1
)

echo.
echo  =========================================
echo   Done!  dist\db_dump_gui.exe
echo  =========================================
echo.
echo  Place these files together:
echo    db_dump_gui.exe  +  db_dump.py
echo.
pause