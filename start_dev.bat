@echo off
REM ========================================
REM UNIFIED WINDOWS DEVELOPMENT START SCRIPT
REM Startet Backend + Expo Mobile App
REM ========================================

setlocal enabledelayedexpansion

REM Parse arguments
set "EXPO_MODE=--lan"
set "BACKEND_PORT=5001"

:parse_args
if "%1"=="" goto start_banner
if /I "%1"=="--tunnel" set "EXPO_MODE=--tunnel" & shift & goto parse_args
if /I "%1"=="--web" set "EXPO_MODE=--web" & shift & goto parse_args
if /I "%1"=="--lan" set "EXPO_MODE=--lan" & shift & goto parse_args
if /I "%1"=="--port" set "BACKEND_PORT=%2" & shift & shift & goto parse_args
if /I "%1"=="/?" goto show_help
if /I "%1"=="-h" goto show_help
if /I "%1"=="--help" goto show_help
echo Unbekannte Option: %1
exit /b 1

:show_help
echo Usage: %0 [OPTIONS]
echo Options:
echo   --tunnel    Expo ueber Internet (fuer Remote-Testing)
echo   --web       Expo im Browser
echo   --lan       Expo im LAN (Standard)
echo   --port NUM  Backend-Port (Default: 5001)
echo   --help      Diese Hilfe
exit /b 0

:start_banner
cls
echo ========================================================
echo   DOKUMENTENVERWALTUNG - WINDOWS DEV START
echo ========================================================
echo.
echo Mode: %EXPO_MODE%
echo Port: %BACKEND_PORT%
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo [FEHLER] Virtual Environment nicht gefunden!
    echo Bitte zuerst install.sh auf Linux ausfuehren oder
    echo manuell venv erstellen: python -m venv venv
    pause
    exit /b 1
)

REM 1. Port Check and Auto-Cleanup
echo [1/3] Pruefe Port %BACKEND_PORT%...
netstat -ano | findstr ":%BACKEND_PORT%" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [INFO] Port %BACKEND_PORT% belegt - beende alten Prozess...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%BACKEND_PORT%"') do (
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
    echo [OK] Port freigegeben
)

REM 2. Backend starten
echo [2/3] Starte Backend Server (in neuem Fenster)...
start "Backend Server" cmd /k "call venv\Scripts\activate.bat && python app/server.py --port %BACKEND_PORT%"

REM Warten auf Backend
echo Warte auf Backend (max. 30 Sekunden)...
set /a MAX_WAIT=30
set /a COUNTER=0

:wait_loop
timeout /t 1 /nobreak >nul
set /a COUNTER+=1

REM Health Check (simplified for Windows)
curl -sf http://localhost:%BACKEND_PORT%/health >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Backend ist bereit!
    goto backend_ready
)

if %COUNTER% LSS %MAX_WAIT% goto wait_loop

echo [WARNUNG] Backend antwortet nicht. Trotzdem fortfahren...

:backend_ready
echo Backend URL: http://localhost:%BACKEND_PORT%
echo.

REM 3. Expo App starten
echo [3/3] Starte Expo App (%EXPO_MODE%)...

if not exist "mobile\photo_app_expo" (
    echo [FEHLER] Expo Verzeichnis nicht gefunden!
    pause
    exit /b 1
)

cd mobile\photo_app_expo

if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
    if %ERRORLEVEL% NEQ 0 (
        echo [FEHLER] npm install fehlgeschlagen!
        pause
        exit /b 1
    )
)

echo.
echo ╔════════════════════════════════════════╗
echo ║   EXPO DEVELOPMENT SERVER              ║
echo ╚════════════════════════════════════════╝
echo.
if "%EXPO_MODE%"=="--tunnel" (
    echo Mode: TUNNEL - Zugriff ueberall moeglich
) else if "%EXPO_MODE%"=="--web" (
    echo Mode: WEB - Browser wird geoeffnet
) else (
    echo Mode: LAN - Nur lokales Netzwerk
)
echo.

start "Expo Development Server" cmd /k "npx expo start %EXPO_MODE%"

echo.
echo ========================================================
echo   ERFOLGREICH GESTARTET!
echo ========================================================
echo.
echo Backend:  http://localhost:%BACKEND_PORT%
echo Frontend: Siehe Expo Fenster fuer QR-Code
echo.
echo Zwei neue Fenster sollten geoeffnet sein:
echo   1. Backend Server
echo   2. Expo Development Server
echo.
echo Zum Beenden: Beide Fenster schliessen oder Ctrl+C
echo.
pause
