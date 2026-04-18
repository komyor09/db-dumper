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

echo  [1/4] Checking PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo  [1/4] Installing PyInstaller...
    pip install pyinstaller --quiet
)
echo  [1/4] PyInstaller OK

echo  [2/4] Checking files...
if not exist "db_dump.py" (
    echo  [ERROR] db_dump.py not found
    pause & exit /b 1
)
if not exist "db_dump_gui.py" (
    echo  [ERROR] db_dump_gui.py not found
    pause & exit /b 1
)
echo  [2/4] Files OK

echo  [3/4] Cleaning old builds...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
if exist "db_dump_gui.spec" del /q db_dump_gui.spec
echo  [3/4] Clean OK

echo  [4/4] Building exe...
echo.

pyinstaller --onefile --windowed --name "db_dump_gui" --add-data "db_dump.py;." --hidden-import tkinter --hidden-import tkinter.ttk --hidden-import tkinter.filedialog --hidden-import tkinter.messagebox db_dump_gui.py

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
