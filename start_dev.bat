@echo off
echo ========================================================
echo   DOKUMENTENVERWALTUNG - WINDOWS DEV START
echo ========================================================
echo.

:: 1. Backend starten
echo [1/2] Starte Backend Server (in neuem Fenster)...
if exist "venv\Scripts\activate.bat" (
    start "Backend Server" cmd /k "call venv\Scripts\activate.bat && python app/server.py"
) else (
    echo Warnung: venv nicht gefunden. Versuche globales Python...
    start "Backend Server" cmd /k "python app/server.py"
)

:: Warten bis Backend startet
timeout /t 5 /nobreak >nul

:: 2. Expo App starten
echo [2/2] Starte Expo App...
cd mobile\photo_app_expo

set "EXPO_ARGS="
if "%1"=="--web" set "EXPO_ARGS=--web"
if "%1"=="--tunnel" set "EXPO_ARGS=--tunnel"
if "%1"=="--lan" set "EXPO_ARGS=--lan"

if exist "node_modules" (
    start "Expo App" cmd /k "npx expo start %EXPO_ARGS%"
) else (
    echo Installing dependencies first...
    call npm install
    start "Expo App" cmd /k "npx expo start %EXPO_ARGS%"
)

echo.
echo Fertig! Zwei neue Fenster sollten sich geoeffnet haben.
echo Backend: http://localhost:5001
echo Frontend: Browser oeffnet sich automatisch
echo.
pause
