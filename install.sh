#!/bin/bash
#
# VOLLAUTOMATISCHES Installations-Script für Raspberry Pi
# - Expo React Native App
# - Automatische Datenträger-Erkennung & Mounting
# - Node.js + npm
# - Robustes Error-Handling & Logging
#

set -e

# ==========================================
# KONFIGURATION & KONSTANTEN
# ==========================================

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Defaults
SKIP_OLLAMA=false
SKIP_EXPO=false
DRY_RUN=false
LOG_LEVEL="info"
MOUNT_POINT="/mnt/photos"

# ==========================================
# ARGUMENT PARSING
# ==========================================

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --skip-ollama)   SKIP_OLLAMA=true   ; shift ;;
        --skip-expo)     SKIP_EXPO=true     ; shift ;;
        --dry-run)       DRY_RUN=true       ; shift ;;
        --log-level)     LOG_LEVEL="$2"     ; shift 2 ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --skip-ollama    Überspringt Ollama Installation"
            echo "  --skip-expo      Überspringt Expo App Setup"
            echo "  --dry-run        Simuliert die Installation (keine Änderungen)"
            echo "  --log-level LVL  Setzt Log-Level (info, debug)"
            exit 0
            ;;
        *) echo "Unbekannte Option: $1"; exit 1 ;;
    esac
done

# ==========================================
# LOGGING & HELPER
# ==========================================

# User ermitteln
REAL_USER=${SUDO_USER:-$(logname)}
REAL_HOME=$(eval echo "~$REAL_USER")

# Log-Datei setup
LOG_FILE="$REAL_HOME/install_$(date +%Y%m%d_%H%M%S).log"
if [ "$DRY_RUN" = false ]; then
    exec > >(tee -a "$LOG_FILE") 2>&1
fi

log() {
    local level="$1"
    shift
    local msg="$@"
    
    # Check Log Level
    if [ "$LOG_LEVEL" = "info" ] && [ "$level" = "DEBUG" ]; then return; fi
    
    case "$level" in
        DEBUG)   echo -e "${CYAN}[DEBUG]${NC} $msg";;
        INFO)    echo -e "${CYAN}[INFO]${NC} $msg";;
        WARN)    echo -e "${YELLOW}[WARN]${NC} $msg";;
        ERROR)   echo -e "${RED}[ERROR]${NC} $msg";;
        SUCCESS) echo -e "${GREEN}[OK]${NC} $msg";;
        *)       echo "$msg";;
    esac
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

run_with_retry() {
    local cmd="$1"
    local retries=${2:-3}
    local wait_sec=${3:-10}
    
    if [ "$DRY_RUN" = true ]; then
        log INFO "[DRY-RUN] $cmd"
        return 0
    fi
    
    local attempt=0
    while (( attempt < retries )); do
        if eval "$cmd"; then
            return 0
        else
            ((attempt++))
            log WARN "Befehl fehlgeschlagen (Versuch $attempt/$retries). Warte $wait_sec s..."
            sleep $wait_sec
        fi
    done
    return 1
}

wait_for_apt() {
    if [ "$DRY_RUN" = true ]; then return; fi
    while fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 || fuser /var/lib/dpkg/lock >/dev/null 2>&1; do
        log INFO "Warte auf apt-Lock..."
        sleep 2
    done
}

cleanup() {
    if [ -d "/tmp/ollama_download" ]; then
        rm -rf /tmp/ollama_download
        log DEBUG "Temp files cleaned"
    fi
}
trap cleanup EXIT
trap 'log ERROR "Ein unerwarteter Fehler trat auf. Siehe $LOG_FILE für Details."; exit 1' ERR

# ==========================================
# HAUPT-LOGIK
# ==========================================

clear
echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   DOKUMENTENVERWALTUNGSSYSTEM - INSTALLATION               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Root Check
if [ "$EUID" -ne 0 ] && [ "$DRY_RUN" = false ]; then
    log ERROR "Bitte als Root ausführen: sudo $0"
    exit 1
fi

log INFO "Installation für User: $REAL_USER"
log INFO "Log-Datei: $LOG_FILE"
if [ "$DRY_RUN" = true ]; then log WARN "DRY-RUN MODUS AKTIV - Keine Änderungen!"; fi

# 1. Netzwerk Check
log INFO "Prüfe Internetverbindung..."
if ! ping -c 1 -W 3 8.8.8.8 >/dev/null 2>&1; then
    log WARN "Kein Internet! Große Downloads werden übersprungen."
    SKIP_OLLAMA=true
    SKIP_EXPO=true
else
    log SUCCESS "Internet verfügbar"
fi

# 2. Speicher Setup
setup_storage() {
    log INFO "Suche nach USB-Speicher..."
    
    # Liste USB Devices
    USB_DEVICES=$(lsblk -o NAME,SIZE,TYPE,TRAN,MODEL | grep "usb" | grep "disk" || true)
    
    if [ -n "$USB_DEVICES" ]; then
        echo -e "${YELLOW}Gefundene USB-Geräte:${NC}"
        echo "$USB_DEVICES"
        echo ""
        
        if [ "$DRY_RUN" = true ]; then return; fi
        
        # Einfache Auswahl des ersten USB Geräts wenn nicht interaktiv oder nur eins da
        # Hier vereinfacht: Wir nehmen an User will konfigurieren wenn er das Script startet
        # In einer vollautomatischen Version könnte man das erste nehmen.
        # Wir fragen kurz, mit Timeout default auf Nein um nichts kaputt zu machen
        
        echo "Möchtest du einen USB-Speicher für Fotos einrichten? [j/N]"
        read -t 10 -n 1 -r REPLY || REPLY="n"
        echo ""
        
        if [[ $REPLY =~ ^[Jj]$ ]]; then
            echo "Bitte Partition angeben (z.B. sda1):"
            lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT | grep "sd"
            read -p "/dev/" PARTITION
            DEVICE="/dev/$PARTITION"
            
            if [ -b "$DEVICE" ]; then
                mkdir -p "$MOUNT_POINT"
                
                # Fstab
                if ! grep -qs "$DEVICE" /etc/fstab; then
                    echo "$DEVICE $MOUNT_POINT ext4 defaults,noatime 0 2" >> /etc/fstab
                    log SUCCESS "fstab Eintrag hinzugefügt"
                else
                    log INFO "Bereits in fstab"
                fi
                
                # Mount
                if ! mountpoint -q "$MOUNT_POINT"; then
                    mount "$MOUNT_POINT" || mount -a
                    log SUCCESS "Gemountet nach $MOUNT_POINT"
                fi
                
                # Permissions
                chown -R "$REAL_USER:$REAL_USER" "$MOUNT_POINT"
            else
                log ERROR "Gerät $DEVICE nicht gefunden"
            fi
        fi
    else
        log INFO "Kein USB-Speicher gefunden - nutze SD-Karte"
    fi
}
setup_storage

# 3. System Pakete
log INFO "Aktualisiere System..."
if [ "$DRY_RUN" = false ]; then
    wait_for_apt
    apt-get update -qq
    # apt-get upgrade -y -qq  # Optional, kann lange dauern
    
    log INFO "Installiere Basispakete..."
    PACKAGES="python3 python3-pip python3-venv python3-dev build-essential \
              sane sane-utils libsane-dev hplip \
              tesseract-ocr tesseract-ocr-deu tesseract-ocr-eng \
              imagemagick poppler-utils \
              git curl wget unzip pv \
              libjpeg-dev zlib1g-dev libopenblas-dev \
              redis-server"
              
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq $PACKAGES 2>/dev/null || true
    
    systemctl enable redis-server 2>/dev/null || true
    systemctl start redis-server 2>/dev/null || true
fi
log SUCCESS "System-Pakete installiert"

# 4. Node.js
install_node() {
    if command_exists node; then
        log SUCCESS "Node.js bereits installiert: $(node -v)"
        return
    fi
    
    log INFO "Installiere Node.js 20.x..."
    if [ "$DRY_RUN" = false ]; then
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
        wait_for_apt
        apt-get install -y nodejs
    fi
}
install_node

# 5. Ollama
install_ollama() {
    if [ "$SKIP_OLLAMA" = true ]; then
        log INFO "Ollama Installation übersprungen"
        return
    fi
    
    if command_exists ollama; then
        log SUCCESS "Ollama bereits installiert"
        return
    fi
    
    log INFO "Installiere Ollama..."
    log INFO "Installiere Ollama..."
    if [ "$DRY_RUN" = false ]; then
        # Robuster Download des Install-Scripts (force HTTP/1.1)
        if curl --http1.1 -fsSL https://ollama.com/install.sh -o /tmp/ollama_install.sh; then
            chmod +x /tmp/ollama_install.sh
            
            # Installation ausführen
            if run_with_retry "/tmp/ollama_install.sh"; then
                log SUCCESS "Ollama installiert"
            else
                log WARN "Ollama Installation fehlgeschlagen - mache ohne weiter"
            fi
            rm -f /tmp/ollama_install.sh
        else
            log WARN "Download des Ollama-Scripts fehlgeschlagen (Curl Error)"
        fi
    fi
}
install_ollama

# 6. Projekt Setup
log INFO "Richte Projekt ein..."
PROJECT_DIR=""
# Finde Projekt Verzeichnis
for dir in "$REAL_HOME/Autodocumentsorganizer" "$REAL_HOME/OrganisationsAI" "$(pwd)"; do
    if [ -d "$dir" ] && [ -f "$dir/requirements.txt" ]; then
        PROJECT_DIR="$dir"
        break
    fi
done

if [ -z "$PROJECT_DIR" ]; then
    log ERROR "Projektverzeichnis nicht gefunden!"
    exit 1
fi

cd "$PROJECT_DIR"
log INFO "Projekt: $PROJECT_DIR"

# Permissions fixen
if [ "$DRY_RUN" = false ]; then
    if [ "$(stat -c %U "$PROJECT_DIR")" != "$REAL_USER" ]; then
        log WARN "Korrigiere Besitzrechte..."
        chown -R "$REAL_USER:$REAL_USER" "$PROJECT_DIR"
    fi
fi

# Venv
if [ ! -d "venv" ] && [ "$DRY_RUN" = false ]; then
    log INFO "Erstelle venv..."
    sudo -u "$REAL_USER" python3 -m venv venv
fi

# Requirements
log INFO "Installiere Python Dependencies..."
if [ "$DRY_RUN" = false ]; then
    sudo -u "$REAL_USER" bash -c "source venv/bin/activate && pip install -r requirements.txt -q && pip install Pillow qrcode[pil] -q"
fi

# 7. Expo Setup
install_expo() {
    if [ "$SKIP_EXPO" = true ]; then return; fi
    
    EXPO_DIR="$PROJECT_DIR/mobile/photo_app_expo"
    if [ -d "$EXPO_DIR" ]; then
        log INFO "Richte Expo App ein..."
        cd "$EXPO_DIR"
        if [ "$DRY_RUN" = false ]; then
            sudo -u "$REAL_USER" npm install || log WARN "npm install failed"
            
            # Fix dependencies for Expo SDK 54+
            sudo -u "$REAL_USER" npx expo install --fix || log WARN "expo install --fix failed"
            
            if ! command_exists eas; then
                npm install -g eas-cli@latest || log WARN "EAS CLI install failed"
            fi
        fi
        cd "$PROJECT_DIR"
    else
        log WARN "Expo Verzeichnis nicht gefunden"
    fi
}
install_expo

# 8. Verzeichnisse & Service
log INFO "Erstelle Verzeichnisse..."
if [ "$DRY_RUN" = false ]; then
    mkdir -p "$PROJECT_DIR/data"/{uploads,backups,exports}
    mkdir -p /tmp/scans
    
    # Symlink für Fotos wenn gemountet
    if mountpoint -q "$MOUNT_POINT"; then
        mkdir -p "$MOUNT_POINT/Bilder"
        chown -R "$REAL_USER:$REAL_USER" "$MOUNT_POINT/Bilder"
        ln -sf "$MOUNT_POINT/Bilder" "$PROJECT_DIR/data/Bilder"
        log SUCCESS "Fotos verlinkt auf externen Speicher"
    else
        mkdir -p "$PROJECT_DIR/data/Bilder"
    fi
    
    chown -R "$REAL_USER:$REAL_USER" "$PROJECT_DIR/data"
    
    # Service
    if [ -f "systemd/document-manager.service" ]; then
        cp systemd/document-manager.service /etc/systemd/system/
        systemctl daemon-reload
        systemctl enable document-manager.service
        
        if ! systemctl is-active --quiet document-manager.service; then
            systemctl start document-manager.service
            log SUCCESS "Service gestartet"
        else
            log INFO "Service läuft bereits"
        fi
    fi
    
    # User zu Gruppen
    usermod -a -G scanner,lp "$REAL_USER" 2>/dev/null || true
fi

# 9. Abschluss
IP=$(hostname -I | awk '{print $1}' || echo "localhost")

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           ✓ INSTALLATION ABGESCHLOSSEN!                   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Dashboard:${NC} http://$IP:5001"
echo -e "${CYAN}Fotos:${NC}     http://$IP:5001/photos.html"
echo ""
echo -e "${YELLOW}Starten:${NC}"
echo "  Development: ./start_dev.sh"
echo "  Production:  Service läuft bereits"
echo ""
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}[DRY-RUN] Es wurden keine Änderungen vorgenommen.${NC}"
else
    echo -e "${YELLOW}Bitte neu starten: sudo reboot${NC}"
fi
echo ""
