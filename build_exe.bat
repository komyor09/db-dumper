@echo off
setlocal enabledelayedexpansion

echo.
echo  =========================================
echo   db_dump GUI - Build EXE (PyInstaller)
echo  =========================================
echo.

:: ── 1. Python ─────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found in PATH
    pause & exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo  [1/6] %%v

:: ── 2. PyInstaller ────────────────────────────
echo  [2/6] Checking PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo  [2/6] Installing PyInstaller...
    pip install pyinstaller --quiet
)
echo  [2/6] PyInstaller OK

:: ── 3. Файлы ──────────────────────────────────
echo  [3/6] Checking files...
if not exist "db_dump.py" (
    echo  [ERROR] db_dump.py not found
    pause & exit /b 1
)
if not exist "db_dump_gui.py" (
    echo  [ERROR] db_dump_gui.py not found
    pause & exit /b 1
)
echo  [3/6] Files OK

:: ── 4. Иконка ─────────────────────────────────
echo  [4/6] Preparing icon...
set ICON_FLAG=
if exist "icon.ico" (
    set ICON_FLAG=--icon=icon.ico
    echo  [4/6] icon.ico found - OK
) else if exist "icon.png" (
    pip show pillow >nul 2>&1
    if errorlevel 1 pip install pillow --quiet
    python -c "from PIL import Image; img=Image.open('icon.png'); img.save('icon.ico', format='ICO', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])"
    if errorlevel 1 (
        echo  [4/6] WARNING: icon conversion failed, building without icon
    ) else (
        set ICON_FLAG=--icon=icon.ico
        echo  [4/6] icon.png converted - OK
    )
) else (
    echo  [4/6] No icon found - building without icon
)

:: ── 5. Полная очистка ─────────────────────────
echo  [5/6] Full clean...
if exist "dist"             rmdir /s /q dist
if exist "build"            rmdir /s /q build
if exist "db_dump_gui.spec" del /q db_dump_gui.spec
if exist "__pycache__"      rmdir /s /q __pycache__
for /d /r . %%d in (__pycache__) do if exist "%%d" rmdir /s /q "%%d"
del /s /q *.pyc >nul 2>&1
echo  [5/6] Clean OK

:: ── 6. Сборка ─────────────────────────────────
echo  [6/6] Building exe...
echo.

::
:: АРХИТЕКТУРА:
::   db_dump_gui.exe  — GUI (PyInstaller bundle, содержит Python runtime)
::   db_dump.py       — CLI скрипт, лежит РЯДОМ с .exe, запускается через subprocess
::
:: db_dump_gui.py резолвит путь к db_dump.py через sys.executable:
::   _BASE_DIR = Path(sys.executable).parent   (когда frozen)
::   DB_DUMP_SCRIPT = _BASE_DIR / "db_dump.py"
::
:: Поэтому db_dump.py НЕ встраивается в exe, а копируется рядом после сборки.
::

pyinstaller ^
    --clean ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name "db_dump_gui" ^
    --hidden-import tkinter ^
    --hidden-import tkinter.ttk ^
    --hidden-import tkinter.filedialog ^
    --hidden-import tkinter.messagebox ^
    !ICON_FLAG! ^
    db_dump_gui.py

if errorlevel 1 (
    echo.
    echo  [ERROR] Build failed
    pause & exit /b 1
)

:: ВАЖНО: копируем свежий db_dump.py рядом с exe
:: GUI ищет его через Path(sys.executable).parent / "db_dump.py"
echo.
echo  Copying db_dump.py to dist\...
copy /y "db_dump.py" "dist\db_dump.py" >nul
if errorlevel 1 (
    echo  [ERROR] Failed to copy db_dump.py to dist\
    pause & exit /b 1
)
echo  db_dump.py copied OK

echo.
echo  =========================================
echo   Done!
echo  =========================================
echo.
echo  dist\db_dump_gui.exe   — запускаемый файл
echo  dist\db_dump.py        — CLI модуль (должен лежать рядом с exe)
echo.
echo  Отдавать пользователям оба файла из папки dist\
echo.
pause