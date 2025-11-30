#!/bin/bash
#
# UNIFIED START SCRIPT
# Startet Backend + Expo Mobile App Development Server
#

set -e

# Farben
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

# Defaults
EXPO_MODE="--lan"
BACKEND_PORT=5001

# Argument Parsing
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --tunnel) EXPO_MODE="--tunnel"; shift ;;
        --web) EXPO_MODE="--web"; shift ;;
        --lan) EXPO_MODE="--lan"; shift ;;
        --port) BACKEND_PORT="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --tunnel    Expo über Internet (für Remote-Testing)"
            echo "  --web       Expo im Browser"
            echo "  --lan       Expo im LAN (Standard)"
            echo "  --port NUM  Backend-Port (Default: 5001)"
            exit 0
            ;;
        *) echo "Unbekannte Option: $1"; exit 1 ;;
    esac
done

clear
echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║        DOKUMENTENVERWALTUNG - START DEVELOPMENT            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Finde Projekt-Verzeichnis
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo -e "${BLUE}Projekt: $PROJECT_DIR${NC}"
echo ""

# ==========================================
# HELPER FUNCTIONS
# ==========================================

check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port in use
    else
        return 1  # Port free
    fi
}

wait_for_health() {
    local url=$1
    local max_wait=30
    
    echo "Warte auf Health-Check..."
    for i in $(seq 1 $max_wait); do
        if curl -sf "$url/health" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ Backend ist gesund!${NC}"
            return 0
        fi
        sleep 1
    done
    
    echo -e "${YELLOW}⚠ Backend antwortet nicht auf Health-Check${NC}"
    return 1
}

# ==========================================
# SCHRITT 1: Backend starten
# ==========================================

echo -e "${YELLOW}━━━━ Backend Server starten ━━━━${NC}"

# Port Check
if check_port $BACKEND_PORT; then
    echo -e "${YELLOW}⚠ Port $BACKEND_PORT bereits belegt${NC}"
    
    # Check if it's our service
    if systemctl is-active --quiet document-manager 2>/dev/null; then
        echo -e "${GREEN}✓ Backend läuft bereits als Service${NC}"
    else
        # Try to kill existing process on port
        echo "Beende alten Prozess auf Port $BACKEND_PORT..."
        PID=$(lsof -ti:$BACKEND_PORT)
        if [ -n "$PID" ]; then
            kill $PID 2>/dev/null
            sleep 2
        fi
    fi
fi

# Check if service is NOT running, then start backend
if ! systemctl is-active --quiet document-manager 2>/dev/null; then
    echo "Starte Flask Backend auf Port $BACKEND_PORT..."
    
    if [ ! -d "venv" ]; then
        echo -e "${RED}✗ Virtual Environment nicht gefunden!${NC}"
        echo "Führe zuerst: ./install.sh aus"
        exit 1
    fi
    
    source venv/bin/activate
    
    # Start in background with nohup
    nohup python app/server.py --port $BACKEND_PORT > /tmp/backend.log 2>&1 &
    BACKEND_PID=$!
    
    echo -e "${GREEN}✓ Backend gestartet (PID: $BACKEND_PID)${NC}"
    echo "  Logs: tail -f /tmp/backend.log"
    
    # Wait for backend with health check
    if wait_for_health "http://localhost:$BACKEND_PORT"; then
        echo -e "${GREEN}✓ Backend ist bereit und gesund${NC}"
    else
        echo -e "${RED}✗ Backend-Start fehlgeschlagen. Logs:${NC}"
        tail -n 20 /tmp/backend.log
        exit 1
    fi
fi

IP=$(hostname -I | awk '{print $1}' || echo "localhost")
echo -e "${CYAN}Backend URL: http://$IP:$BACKEND_PORT${NC}"
echo ""

# ==========================================
# SCHRITT 2: Expo App starten
# ==========================================

echo -e "${YELLOW}━━━━ Expo Development Server starten ━━━━${NC}"

EXPO_DIR="$PROJECT_DIR/mobile/photo_app_expo"

if [ -d "$EXPO_DIR" ]; then
    cd "$EXPO_DIR"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo "Installing dependencies..."
        npm install
    fi
    
    echo -e "${GREEN}Starting Expo in ${EXPO_MODE#--} mode...${NC}"
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                                                        ║${NC}"
    echo -e "${CYAN}║  📱  EXPO DEVELOPMENT SERVER                          ║${NC}"
    echo -e "${CYAN}║                                                        ║${NC}"
    echo -e "${CYAN}║  QR-Code wird angezeigt - Scanne mit Expo Go App!    ║${NC}"
    echo -e "${CYAN}║                                                        ║${NC}"
    echo -e "${CYAN}║  iOS:     Expo Go App aus App Store                   ║${NC}"
    echo -e "${CYAN}║  Android: Expo Go App aus Play Store                  ║${NC}"
    echo -e "${CYAN}║                                                        ║${NC}"
    if [[ "$EXPO_MODE" == "--tunnel" ]]; then
        echo -e "${CYAN}║  🌐 TUNNEL MODE aktiv - funktioniert überall!        ║${NC}"
    elif [[ "$EXPO_MODE" == "--web" ]]; then
        echo -e "${CYAN}║  🌐 WEB MODE - Browser wird geöffnet                 ║${NC}"
    else
        echo -e "${CYAN}║  📡 LAN MODE - nur im gleichen Netzwerk              ║${NC}"
    fi
    echo -e "${CYAN}║                                                        ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Start Expo
    npx expo start $EXPO_MODE
    
else
    echo -e "${YELLOW}⚠ Expo App nicht gefunden in: $EXPO_DIR${NC}"
    echo "Führe install.sh aus um Expo App zu installieren"
fi

# Cleanup on exit
trap "echo 'Stopping...'; [ -n '$BACKEND_PID' ] && kill $BACKEND_PID 2>/dev/null; exit" INT TERM
