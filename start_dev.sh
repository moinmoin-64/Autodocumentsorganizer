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
NC='\033[0m'

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
# SCHRITT 1: Backend starten
# ==========================================

echo -e "${YELLOW}━━━━ Backend Server starten ━━━━${NC}"

# Check if running as service
if systemctl is-active --quiet document-manager; then
    echo -e "${GREEN}✓ Backend läuft bereits als Service${NC}"
    echo "  Status: systemctl status document-manager"
else
    # Start backend in background
    echo "Starte Flask Backend..."
    
    source venv/bin/activate
    
    # Start in background with nohup
    nohup python app/server.py > /tmp/backend.log 2>&1 &
    BACKEND_PID=$!
    
    echo -e "${GREEN}✓ Backend gestartet (PID: $BACKEND_PID)${NC}"
    echo "  Logs: tail -f /tmp/backend.log"
    
    # Wait for backend to be ready
    echo "Warte auf Backend..."
    for i in {1..10}; do
        if curl -s http://localhost:5001 > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Backend bereit!${NC}"
            break
        fi
        sleep 1
    done
fi

IP=$(hostname -I | awk '{print $1}' || echo "localhost")
echo -e "${CYAN}Backend URL: http://$IP:5001${NC}"
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
    
    echo -e "${GREEN}Starting Expo...${NC}"
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
    echo -e "${CYAN}║  Optionen:                                             ║${NC}"
    echo -e "${CYAN}║  --tunnel   Für Remote-Zugriff (empfohlen)            ║${NC}"
    echo -e "${CYAN}║  --web      Im Browser starten                        ║${NC}"
    echo -e "${CYAN}║  --lan      Im lokalen Netzwerk (Standard)            ║${NC}"
    echo -e "${CYAN}║                                                        ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Start Expo
    if [[ "$1" == "--web" ]]; then
        echo -e "${GREEN}Starting Expo in WEB mode...${NC}"
        npx expo start --web
    else
        # Start Expo (foreground, damit man QR sieht)
        npx expo start --lan
    fi
    
else
    echo -e "${YELLOW}⚠ Expo App nicht gefunden in: $EXPO_DIR${NC}"
    echo "Führe install.sh aus um Expo App zu installieren"
fi

# Cleanup on exit
trap "echo 'Stopping...'; kill $BACKEND_PID 2>/dev/null; exit" INT TERM
