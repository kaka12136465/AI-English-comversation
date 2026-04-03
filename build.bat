@echo off
chcp 65001 > nul
echo ================================================
echo   AI English Voice Coach - Build EXE
echo ================================================
echo.

echo [1/3] Installing PyInstaller...
pip install pyinstaller --quiet
if %errorlevel% neq 0 (
    echo ERROR: pip install failed.
    pause & exit /b 1
)

echo [2/3] Building .exe (this takes a minute)...
python -m PyInstaller ^
  --onefile ^
  --name "AI_English_Coach" ^
  --add-data "static;static" ^
  --hidden-import=uvicorn.logging ^
  --hidden-import=uvicorn.loops ^
  --hidden-import=uvicorn.loops.auto ^
  --hidden-import=uvicorn.protocols ^
  --hidden-import=uvicorn.protocols.http ^
  --hidden-import=uvicorn.protocols.http.auto ^
  --hidden-import=uvicorn.protocols.websockets ^
  --hidden-import=uvicorn.protocols.websockets.auto ^
  --hidden-import=uvicorn.lifespan ^
  --hidden-import=uvicorn.lifespan.on ^
  --hidden-import=anyio._backends._asyncio ^
  --hidden-import=anyio._backends._trio ^
  --collect-all anthropic ^
  --noconfirm ^
  main.py

if %errorlevel% neq 0 (
    echo ERROR: PyInstaller build failed.
    pause & exit /b 1
)

echo [3/3] Copying .env to dist folder...
if exist ".env" (
    copy /Y ".env" "dist\.env" > nul
    echo   .env copied.
) else (
    echo   WARNING: .env not found. Copy it manually to the dist folder.
)

echo.
echo ================================================
echo   Build complete!
echo   Location: dist\AI_English_Coach.exe
echo.
echo   HOW TO RUN:
echo   1. Copy dist\AI_English_Coach.exe and dist\.env
echo      to the same folder on any Windows PC.
echo   2. Double-click AI_English_Coach.exe
echo   3. Browser opens automatically.
echo ================================================
pause
