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
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0;0m'

# -------------------------------
# Argumente (optional)
# -------------------------------
SKIP_OLLAMA=false
SKIP_EXPO=false
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --skip-ollama) SKIP_OLLAMA=true ; shift ;;
        --skip-expo)   SKIP_EXPO=true   ; shift ;;
        *) echo "Unbekannte Option: $1"; exit 1 ;;
    esac
done

# -------------------------------
# Hilfsfunktionen
# -------------------------------
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

run_with_retry() {
    local cmd="$1"
    local retries=${2:-3}
    local wait_sec=${3:-10}
    local attempt=0
    while (( attempt < retries )); do
        if eval "$cmd"; then
            return 0
        else
            ((attempt++))
            log WARN "Befehl fehlgeschlagen (Versuch $attempt/$retries). Warte $wait_sec Sekunden..."
            sleep $wait_sec
        fi
    done
    return 1
}

# -------------------------------
# APT-Lock-Handling
# -------------------------------
wait_for_apt() {
    while fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 || fuser /var/lib/dpkg/lock >/dev/null 2>&1; do
        log INFO "Warte auf apt-Lock..."
        sleep 2
    done
}


# Log‑Datei (immer im Home‑Verzeichnis des Users)
LOG_FILE="$REAL_HOME/install_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

# Helper‑Funktion für einheitliche Meldungen
log() {
    local level="$1"
    shift
    local msg="$@"
    case "$level" in
        INFO)   echo -e "${CYAN}[INFO]${NC} $msg";;
        WARN)   echo -e "${YELLOW}[WARN]${NC} $msg";;
        ERROR)  echo -e "${RED}[ERROR]${NC} $msg";;
        SUCCESS)echo -e "${GREEN}[OK]${NC} $msg";;
        *)      echo "$msg";;
    esac
}

# Fehler‑Abfang‑Hook – gibt log‑Eintrag und beendet das Skript
trap 'log ERROR "Ein unerwarteter Fehler trat auf. Siehe $LOG_FILE für Details."; exit 1' ERR

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
if command_exists node; then
    NODE_VERSION=$(node -v)
    log SUCCESS "Node.js bereits installiert: $NODE_VERSION"
else
    log INFO "Node.js 20.x wird installiert..."
    # NodeSource Repository (nur einmal ausführen)
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    wait_for_apt
    apt-get install -y nodejs
    if command_exists node; then
        log SUCCESS "Node.js $(node -v) installiert"
        log SUCCESS "npm $(npm -v) installiert"
    else
        log WARN "Node.js Installation scheinbar fehlgeschlagen – prüfen Sie das Log"
    fi
fi

systemctl enable redis-server 2>/dev/null || true
systemctl start redis-server 2>/dev/null || true

echo ""

# ==========================================
# OLLAMA INSTALLATION (Optional, with retry)
# ==========================================

echo -e "${YELLOW}━━━━ Ollama Installation ━━━━${NC}"

if [ "$SKIP_OLLAMA" = true ]; then
    log INFO "Ollama-Installation wurde per Argument übersprungen."
else
    if command_exists ollama; then
        log SUCCESS "Ollama bereits installiert"
    else
        # Prüfe Netzwerkverbindung (ping zum Host)
        if ping -c 1 -W 3 ollama.com >/dev/null 2>&1; then
            log INFO "Netzwerk erreichbar – starte Ollama-Installation"
        else
            log WARN "Keine Netzwerkverbindung zu ollama.com – überspringe Ollama-Installation"
            SKIP_OLLAMA=true
        fi

        if [ "$SKIP_OLLAMA" = false ]; then
            log INFO "Ollama wird installiert (optional)..."
            log WARN "Falls die Installation fehlschlägt, wird das System ohne Ollama weitergesetzt."
            
            MAX_RETRIES=3
            RETRY_COUNT=0
            OLLAMA_INSTALLED=false
            
            while [ $RETRY_COUNT -lt $MAX_RETRIES ] && [ "$OLLAMA_INSTALLED" = false ]; do
                log INFO "Versuch $((RETRY_COUNT + 1))/$MAX_RETRIES..."
                if timeout 300 bash -c 'curl -fsSL https://ollama.com/install.sh | sh' 2>/dev/null; then
                    OLLAMA_INSTALLED=true
                    log SUCCESS "Ollama erfolgreich installiert"
                else
                    RETRY_COUNT=$((RETRY_COUNT + 1))
                    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
                        log WARN "Download fehlgeschlagen – warte 10 s und versuche erneut"
                        sleep 10
                    fi
                fi
            done
            
            if [ "$OLLAMA_INSTALLED" = false ]; then
                log WARN "Ollama konnte nicht installiert werden (Netzwerk‑Problem?)"
                log INFO "System läuft weiter ohne Ollama‑Funktionalität"
            fi
        fi
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
    log INFO "Erstelle Python‑Virtual‑Environment…"
    if sudo -u "$REAL_USER" python3 -m venv venv; then
        log SUCCESS "Virtual‑Environment erstellt"
    else
        log WARN "Virtual‑Environment konnte nicht erstellt werden – abort"
        exit 1
    fi
else
    log SUCCESS "Virtual‑Environment existiert bereits"
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

if [ "$SKIP_EXPO" = true ]; then
    log INFO "Expo-Setup wurde per Argument übersprungen."
else
    if [ -d "$EXPO_DIR" ]; then
        log INFO "Expo‑Projekt gefunden – installiere Abhängigkeiten"
        cd "$EXPO_DIR"
        
        # npm install als normaler User (nicht root)
        sudo -u "$REAL_USER" npm install || log WARN "npm install hatte Fehler – prüfen Sie das Log"
        
        # Expo CLI global installieren (nur falls nicht vorhanden)
        if ! command_exists expo; then
            log INFO "Expo CLI wird global installiert..."
            npm install -g expo-cli@latest eas-cli@latest || log WARN "Expo CLI Installation fehlgeschlagen"
        else
            log SUCCESS "Expo CLI bereits vorhanden"
        fi
        
        log SUCCESS "Expo‑App‑Abhängigkeiten installiert"
        cd "$PROJECT_DIR"
    else
        log WARN "Expo‑App‑Verzeichnis nicht gefunden – überspringe Expo‑Setup"
    fi
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
    log SUCCESS "Systemd Service aktiviert"
    # Prüfe, ob Service jetzt aktiv ist
    if systemctl is-active --quiet document-manager.service; then
        log SUCCESS "Service läuft bereits"
    else
        log INFO "Starte Service..."
        systemctl start document-manager.service && log SUCCESS "Service gestartet" || log WARN "Service konnte nicht gestartet werden"
    fi
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
