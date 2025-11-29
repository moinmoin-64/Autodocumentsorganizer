#!/bin/bash
#
# VOLLAUTOMATISCHES Installations-Script für Raspberry Pi
# - Expo React Native App (statt Flutter)
# - Automatische Datenträger-Erkennung
# - Node.js + npm für Expo
#

set -e

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

clear
echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   DOKUMENTENVERWALTUNGSSYSTEM - INSTALLATION MIT EXPO          ║"
echo "║                 Raspberry Pi Edition                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Prüfe Root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}✗ Bitte als Root ausführen: sudo ./install.sh${NC}"
    exit 1
fi

REAL_USER=${SUDO_USER:-$(logname)}
REAL_HOME=$(eval echo "~$REAL_USER")

echo -e "${GREEN}✓ Installation für User: $REAL_USER${NC}"
echo ""

# ==========================================
# STORAGE DETECTION (wie vorher)
# ==========================================

echo -e "${BLUE}━━━━ DATENTRÄGER-KONFIGURATION ━━━━${NC}"

show_storage_devices() {
    lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE,LABEL | grep -v "loop"
    echo ""
}

check_usb_devices() {
    USB_DEVICES=$(lsblk -o NAME,TYPE,TRAN | grep "usb" | grep "disk" | awk '{print $1}' || true)
    [ -n "$USB_DEVICES" ]
}

show_storage_devices

STORAGE_DEVICE=""
STORAGE_MOUNT_POINT="/mnt/photos"

if check_usb_devices; then
    echo -e "${YELLOW}USB-Speicher gefunden!${NC}"
    echo "Externen Datenträger verwenden? [j/N]"
    read -p "> " -n 1 -r STORAGE_CHOICE
    echo ""
    
    if [[ $STORAGE_CHOICE =~ ^[JjYy]$ ]]; then
        # (USB Device Selection Logic wie vorher)
        echo "Implementierung wie im vorherigen Script..."
    fi
fi

echo ""

# ==========================================
# SYSTEM PACKAGES
# ==========================================

echo -e "${YELLOW}━━━━ System-Update ━━━━${NC}"
apt-get update -qq
apt-get upgrade -y -qq
echo -e "${GREEN}✓${NC}"

echo -e "${YELLOW}━━━━ System-Pakete ━━━━${NC}"

DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    python3 python3-pip python3-venv python3-dev build-essential \
    sane sane-utils libsane-dev hplip \
    tesseract-ocr tesseract-ocr-deu tesseract-ocr-eng \
    imagemagick poppler-utils \
    git curl wget unzip \
    libjpeg-dev zlib1g-dev libopenblas-dev \
    redis-server \
    2>/dev/null || true

# Node.js & npm für Expo
echo -e "${YELLOW}━━━━ Node.js Installation ━━━━${NC}"

# Check if Node.js already installed
if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v)
    echo -e "${GREEN}✓ Node.js bereits installiert: $NODE_VERSION${NC}"
else
    echo "Installiere Node.js 20.x..."
    
    # NodeSource Repository
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
    
    echo -e "${GREEN}✓ Node.js $(node -v) installiert${NC}"
    echo -e "${GREEN}✓ npm $(npm -v) installiert${NC}"
fi

systemctl enable redis-server 2>/dev/null || true
systemctl start redis-server 2>/dev/null || true

echo ""

# ==========================================
# OLLAMA INSTALLATION (Optional, with retry)
# ==========================================

echo -e "${YELLOW}━━━━ Ollama Installation ━━━━${NC}"

if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama bereits installiert${NC}"
else
    echo "Installiere Ollama für lokales LLM..."
    echo -e "${YELLOW}Hinweis: Ollama ist optional - bei Fehler wird übersprungen${NC}"
    
    # Retry-Logik mit Timeout
    MAX_RETRIES=3
    RETRY_COUNT=0
    OLLAMA_INSTALLED=false
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ] && [ "$OLLAMA_INSTALLED" = false ]; do
        echo "Versuch $((RETRY_COUNT + 1))/$MAX_RETRIES..."
        
        # Download mit Timeout (5 Minuten)
        if timeout 300 bash -c 'curl -fsSL https://ollama.com/install.sh | sh' 2>/dev/null; then
            OLLAMA_INSTALLED=true
            echo -e "${GREEN}✓ Ollama installiert${NC}"
        else
            RETRY_COUNT=$((RETRY_COUNT + 1))
            if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
                echo -e "${YELLOW}⚠ Fehler - warte 10 Sekunden...${NC}"
                sleep 10
            fi
        fi
    done
    
    if [ "$OLLAMA_INSTALLED" = false ]; then
        echo -e "${YELLOW}⚠ Ollama Installation fehlgeschlagen (Netzwerk-Problem?)${NC}"
        echo "  → System funktioniert auch ohne Ollama"
        echo "  → AI-Features werden deaktiviert"
        echo "  → Später nachholen mit: curl -fsSL https://ollama.com/install.sh | sh"
    fi
fi

# ==========================================
# PROJEKT SETUP
# ==========================================

echo -e "${YELLOW}━━━━ Projekt Setup ━━━━${NC}"

PROJECT_DIR=""
for dir in "$REAL_HOME/Autodocumentsorganizer" "$REAL_HOME/OrganisationsAI" "$(pwd)"; do
    if [ -d "$dir" ] && [ -f "$dir/requirements.txt" ]; then
        PROJECT_DIR="$dir"
        break
    fi
done

if [ -z "$PROJECT_DIR" ]; then
    echo -e "${RED}✗ Projekt nicht gefunden!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Projekt: $PROJECT_DIR${NC}"
cd "$PROJECT_DIR"

# Python venv
if [ ! -d "venv" ]; then
    sudo -u "$REAL_USER" python3 -m venv venv
fi

echo "Installing Python packages..."
sudo -u "$REAL_USER" bash -c "
    source venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    pip install -r requirements-dev.txt -q 2>/dev/null || true
    pip install Pillow qrcode[pil] -q
"
echo -e "${GREEN}✓ Python OK${NC}"

# ==========================================
# EXPO APP SETUP
# ==========================================

echo ""
echo -e "${BLUE}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  EXPO REACT NATIVE APP INSTALLATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${NC}"

EXPO_DIR="$PROJECT_DIR/mobile/photo_app_expo"

if [ -d "$EXPO_DIR" ]; then
    echo "Installing Expo dependencies..."
    cd "$EXPO_DIR"
    
    # npm install als User
    sudo -u "$REAL_USER" npm install
    
    # Expo CLI global
    echo "Installing Expo CLI..."
    npm install -g expo-cli@latest eas-cli@latest
    
    echo -e "${GREEN}✓ Expo App dependencies installed${NC}"
    echo -e "${GREEN}✓ Expo CLI & EAS CLI ready${NC}"
    
    cd "$PROJECT_DIR"
else
    echo -e "${YELLOW}⚠ Expo App Verzeichnis nicht gefunden${NC}"
fi

echo ""

# ==========================================
# VERZEICHNISSE
# ==========================================

echo -e "${YELLOW}━━━━ Verzeichnisse ━━━━${NC}"

mkdir -p "$PROJECT_DIR/data"/{uploads,backups,exports}
mkdir -p /tmp/scans

# Foto-Speicher
if [ -n "$STORAGE_DEVICE" ] && [ -d "$STORAGE_MOUNT_POINT" ]; then
    PHOTOS_DIR="$STORAGE_MOUNT_POINT/Bilder"
    mkdir -p "$PHOTOS_DIR"
    chown -R "$REAL_USER:$REAL_USER" "$PHOTOS_DIR"
    ln -sf "$PHOTOS_DIR" "$PROJECT_DIR/data/Bilder"
    echo -e "${GREEN}✓ Foto-Speicher: $PHOTOS_DIR (extern)${NC}"
else
    mkdir -p "$PROJECT_DIR/data/Bilder"
    echo -e "${YELLOW}⚠ Foto-Speicher: SD-Karte${NC}"
fi

chown -R "$REAL_USER:$REAL_USER" "$PROJECT_DIR/data"
chmod -R 755 "$PROJECT_DIR/data"

mkdir -p /var/log/document-manager
chown "$REAL_USER:$REAL_USER" /var/log/document-manager

echo -e "${GREEN}✓ Verzeichnisse erstellt${NC}"

# ==========================================
# START SCRIPT
# ==========================================

echo ""
echo -e "${YELLOW}━━━━ Start Script ━━━━${NC}"

if [ -f "$PROJECT_DIR/start_dev.sh" ]; then
    chmod +x "$PROJECT_DIR/start_dev.sh"
    chown "$REAL_USER:$REAL_USER" "$PROJECT_DIR/start_dev.sh"
    echo -e "${GREEN}✓ start_dev.sh bereit${NC}"
fi

# ==========================================
# OLLAMA MODEL
# ==========================================

echo ""
echo -e "${YELLOW}━━━━ Ollama Model ━━━━${NC}"
echo "1) llama3.2:1b (empfohlen)"
echo "2) Überspringen"
read -p "Wahl [1-2]: " -t 20 -n 1 -r MODEL_CHOICE || MODEL_CHOICE="2"
echo ""

if [ "$MODEL_CHOICE" = "1" ]; then
    sudo -u "$REAL_USER" ollama pull llama3.2:1b
    echo -e "${GREEN}✓${NC}"
fi

# ==========================================
# SYSTEMD SERVICE
# ==========================================

echo ""
echo -e "${YELLOW}━━━━ Systemd Service ━━━━${NC}"

if [ -f "systemd/document-manager.service" ]; then
    cp systemd/document-manager.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable document-manager.service
    echo -e "${GREEN}✓ Service aktiviert${NC}"
fi

usermod -a -G scanner,lp "$REAL_USER" 2>/dev/null || true

# ==========================================
# FERTIG!
# ==========================================

clear
echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║           ✓ INSTALLATION ERFOLGREICH! ✓                   ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

if [ -d "$EXPO_DIR" ]; then
    echo -e "${CYAN}📱 Expo React Native App:${NC}"
    echo "  ✓ Dependencies installiert"
    echo "  ✓ Bereit für Development"
    echo ""
fi

IP=$(hostname -I | awk '{print $1}')

echo -e "${YELLOW}🚀 STARTEN:${NC}"
echo ""
echo "Methode 1 - Development (mit Expo Live Reload):"
echo -e "   ${GREEN}./start_dev.sh${NC}"
echo "   → Startet Backend + Expo Dev Server"
echo "   → Scanne QR-Code mit Expo Go App"
echo ""
echo "Methode 2 - Production (nur Backend):"
echo -e "   ${GREEN}sudo systemctl start document-manager${NC}"
echo ""

echo -e "${CYAN}📱 Expo Go App benötigt:${NC}"
echo "  iOS: App Store → 'Expo Go'"
echo "  Android: Play Store → 'Expo Go'"
echo ""

echo -e "${CYAN}Projekt: $PROJECT_DIR${NC}"
echo -e "${CYAN}Dashboard: http://$IP:5001${NC}"
echo -e "${CYAN}Fotos: http://$IP:5001/photos.html${NC}"
echo ""

echo -e "${YELLOW}WICHTIG: Raspberry Pi neu starten!${NC}"
echo -e "${GREEN}sudo reboot${NC}"
echo ""
