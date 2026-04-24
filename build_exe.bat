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
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo  [1/5] %%v

:: ── 2. PyInstaller ────────────────────────────
echo  [2/5] Checking PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo  [2/5] Installing PyInstaller...
    pip install pyinstaller --quiet
)
echo  [2/5] PyInstaller OK

:: ── 3. Файлы ──────────────────────────────────
echo  [3/5] Checking files...
if not exist "db_dump.py" (
    echo  [ERROR] db_dump.py not found
    pause & exit /b 1
)
if not exist "db_dump_gui.py" (
    echo  [ERROR] db_dump_gui.py not found
    pause & exit /b 1
)
echo  [3/5] Files OK

:: ── 4. Иконка ─────────────────────────────────
echo  [4/5] Preparing icon...
set ICON_FLAG=
if exist "icon.ico" (
    :: icon.ico уже есть — используем напрямую, без конвертации
    set ICON_FLAG=--icon=icon.ico
    echo  [4/5] icon.ico found - OK
) else if exist "icon.png" (
    pip show pillow >nul 2>&1
    if errorlevel 1 (
        echo  [4/5] Installing Pillow...
        pip install pillow --quiet
    )
    python -c "from PIL import Image; img=Image.open('icon.png'); img.save('icon.ico', format='ICO', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])"
    if errorlevel 1 (
        echo  [4/5] WARNING: icon conversion failed, building without icon
    ) else (
        set ICON_FLAG=--icon=icon.ico
        echo  [4/5] icon.png converted to icon.ico - OK
    )
) else (
    echo  [4/5] No icon found - building without icon
)

:: ── 5. Полная очистка ─────────────────────────
echo  [5/5] Full clean...

:: Удаляем артефакты сборки
if exist "dist"             rmdir /s /q dist
if exist "build"            rmdir /s /q build
if exist "db_dump_gui.spec" del /q db_dump_gui.spec

:: ВАЖНО: удаляем .pyc кеш — именно он вызывает проблему "старого кода"
if exist "__pycache__" rmdir /s /q __pycache__
for /d /r . %%d in (__pycache__) do (
    if exist "%%d" rmdir /s /q "%%d"
)
del /s /q *.pyc >nul 2>&1

echo  [5/5] Clean OK

:: ── 6. Сборка ─────────────────────────────────
echo.
echo  Building...
echo.

::
:: КЛЮЧЕВЫЕ ИЗМЕНЕНИЯ vs старый build_exe.bat:
::
:: 1. БЕЗ --add-data "db_dump.py;."
::    db_dump.py — это Python модуль, PyInstaller находит его сам через import analysis.
::    --add-data копирует файл как data (в temp), но import берёт скомпилированную
::    версию из PKG-архива — получаются две копии, используется старая.
::
:: 2. --clean — принудительно чистит internal PyInstaller cache (в %APPDATA%)
::    Именно этот кеш хранит скомпилированный .pyc даже после удаления dist/ и build/
::
:: 3. db_dump.py передаётся через --hidden-import — PyInstaller включает его
::    как нормальный Python модуль, а не data-файл.
::
pyinstaller ^
    --clean ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name "db_dump_gui" ^
    --hidden-import db_dump ^
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

echo.
echo  =========================================
echo   Done!  dist\db_dump_gui.exe
echo  =========================================
echo.
echo  dist\db_dump_gui.exe  — готово к использованию
echo  (db_dump.py встроен внутрь exe, отдельно не нужен)
echo.
pause