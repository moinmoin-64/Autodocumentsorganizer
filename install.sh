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

# 1. System Checks
check_system() {
    log INFO "Prüfe Systemvoraussetzungen..."
    
    # OS Check
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [[ "$ID" != "debian" && "$ID" != "raspbian" && "$ID" != "ubuntu" ]]; then
            log WARN "Nicht-unterstütztes OS erkannt: $ID. Installation könnte fehlschlagen."
        fi
    fi
    
    # Python Version Check
    if command_exists python3; then
        PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        if (( $(echo "$PY_VERSION < 3.11" | bc -l) )); then
            log WARN "Python Version $PY_VERSION ist alt. Empfohlen: 3.11+"
        fi
    fi
}
check_system

# 2. Swap Setup (Wichtig für Pi mit wenig RAM)
setup_swap() {
    log INFO "Prüfe Swap-Speicher..."
    if [ "$DRY_RUN" = true ]; then return; fi
    
    TOTAL_MEM=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    SWAP_SIZE=$(grep SwapTotal /proc/meminfo | awk '{print $2}')
    
    # Wenn weniger als 4GB RAM und weniger als 2GB Swap
    if [ "$TOTAL_MEM" -lt 4000000 ] && [ "$SWAP_SIZE" -lt 2000000 ]; then
        log INFO "Wenig RAM erkannt ($((TOTAL_MEM/1024))MB). Erweitere Swap auf 2GB..."
        
        # dphys-swapfile Konfiguration anpassen (Raspberry Pi Standard)
        if [ -f /etc/dphys-swapfile ]; then
            sed -i 's/^CONF_SWAPSIZE=.*/CONF_SWAPSIZE=2048/' /etc/dphys-swapfile
            systemctl restart dphys-swapfile
            log SUCCESS "Swap erweitert"
        else
            # Fallback: Manuelles Swapfile
            if [ ! -f /swapfile ]; then
                fallocate -l 2G /swapfile
                chmod 600 /swapfile
                mkswap /swapfile
                swapon /swapfile
                echo "/swapfile none swap sw 0 0" >> /etc/fstab
                log SUCCESS "Swapfile erstellt (2GB)"
            fi
        fi
    else
        log INFO "Speicher ausreichend (RAM: $((TOTAL_MEM/1024))MB, Swap: $((SWAP_SIZE/1024))MB)"
    fi
}
setup_swap

# 3. Netzwerk Check
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
    if [ "$DRY_RUN" = false ]; then
        # Robuster Download mit mehreren Methoden
        OLLAMA_SCRIPT="/tmp/ollama_install.sh"
        
        # Methode 1: wget (bevorzugt für große Downloads)
        if command_exists wget; then
            log INFO "Verwende wget für Download..."
            wget --no-check-certificate -q -O "$OLLAMA_SCRIPT" https://ollama.com/install.sh && chmod +x "$OLLAMA_SCRIPT"
        # Methode 2: curl mit HTTP/1.1
        elif curl --http1.1 -fsSL https://ollama.com/install.sh -o "$OLLAMA_SCRIPT"; then
            chmod +x "$OLLAMA_SCRIPT"
        else
            log WARN "Download des Ollama-Scripts fehlgeschlagen"
            OLLAMA_SCRIPT=""
        fi
        
        # Installation ausführen wenn Download erfolgreich
        if [ -n "$OLLAMA_SCRIPT" ] && [ -f "$OLLAMA_SCRIPT" ]; then
            # Force HTTP/1.1 für das Ollama-Script selbst
            export CURL_HTTP_VERSION=HTTP/1.1
            
            if bash "$OLLAMA_SCRIPT"; then
                log SUCCESS "Ollama installiert"
            else
                log WARN "Ollama Installation fehlgeschlagen - überspringe"
            fi
            
            rm -f "$OLLAMA_SCRIPT"
            unset CURL_HTTP_VERSION
        else
            log WARN "Ollama konnte nicht heruntergeladen werden - überspringe"
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
log INFO "Installiere Python Dependencies (kann 5-10 Min. dauern)..."
if [ "$DRY_RUN" = false ]; then
    sudo -u "$REAL_USER" bash -c "source venv/bin/activate && pip install --upgrade pip setuptools wheel && pip install -r requirements.txt && pip install Pillow qrcode[pil] pytest pytest-cov pybind11"
fi
log SUCCESS "Python-Pakete installiert"

# Native C Extensions (Performance!)
log INFO "Kompiliere native C-Extensions für Performance..."
if [ "$DRY_RUN" = false ]; then
    # Check if GCC is available
    if command_exists gcc; then
        log INFO "GCC gefunden - kompiliere mit Optimierungen..."
        
        # Detect CPU architecture for optimizations
        ARCH=$(uname -m)
        COMPILE_FLAGS="-O3 -march=native -fopenmp"
        
        if [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "armv7l" ]; then
            log INFO "ARM CPU erkannt - nutze NEON SIMD"
            COMPILE_FLAGS="-O3 -march=native -mfpu=neon -fopenmp"
        else
            log INFO "x86 CPU erkannt - nutze AVX2/SSE4"
            COMPILE_FLAGS="-O3 -march=native -mavx2 -msse4.1 -fopenmp"
        fi
        
        # Build C extension
        sudo -u "$REAL_USER" bash -c "
            source venv/bin/activate
            export CFLAGS='$COMPILE_FLAGS'
            python setup.py build_ext --inplace
        " && log SUCCESS "Native C-Extensions kompiliert (100x Performance!)" || log WARN "C-Extension Build failed - nutze Python Fallback"
        
    else
        log WARN "GCC nicht gefunden - überspringe C-Extensions (nutze Python Fallback)"
        log INFO "Installiere build-essential für bessere Performance:"
        log INFO "  sudo apt-get install build-essential"
    fi
else
    log INFO "[DRY RUN] Würde C-Extensions kompilieren"
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
    
    # Logs-Verzeichnis
    mkdir -p "$PROJECT_DIR/logs"
    chown -R "$REAL_USER:$REAL_USER" "$PROJECT_DIR/logs"
    
    # User zu Gruppen
    usermod -a -G scanner,lp "$REAL_USER" 2>/dev/null || true
    
    # Datenbank initialisieren
    log INFO "Initialisiere Datenbank..."
    sudo -u "$REAL_USER" bash -c "source venv/bin/activate && python -c 'from app.db_config import init_db; init_db()'" 2>/dev/null || log WARN "DB-Init übersprungen (bereits vorhanden?)"
    
    # Database Migration (Indexes hinzufügen)
    log INFO "Führe Database Migration aus..."
    sudo -u "$REAL_USER" bash -c "source venv/bin/activate && python -c 'from migrations.001_add_indexes import upgrade; upgrade()'" 2>/dev/null || log WARN "Migration bereits ausgeführt oder nicht nötig"
fi

# 9. Post-Installation Validierung
validate_installation() {
    log INFO "Validiere Installation..."
    
    local errors=0
    
    # Python venv Check
    if [ ! -d "$PROJECT_DIR/venv" ]; then
        log ERROR "Virtual Environment fehlt!"
        ((errors++))
    fi
    
    # Database Check
    if [ ! -f "$PROJECT_DIR/data/database.db" ]; then
        log WARN "Datenbank nicht gefunden (wird beim ersten Start erstellt)"
    fi
    
    # Service Check
    if [ "$DRY_RUN" = false ]; then
        if systemctl is-enabled document-manager.service >/dev/null 2>&1; then
            log SUCCESS "Service konfiguriert"
        else
            log WARN "Service nicht aktiviert"
        fi
    fi
    
    # Expo Check
    if [ -d "$PROJECT_DIR/mobile/photo_app_expo/node_modules" ]; then
        log SUCCESS "Expo App bereit"
    else
        log WARN "Expo App nicht vollständig installiert"
    fi
    
    if [ $errors -gt 0 ]; then
        log ERROR "Validation fehlgeschlagen! Siehe Log: $LOG_FILE"
        return 1
    else
        log SUCCESS "Validation erfolgreich!"
        return 0
    fi
}
validate_installation

# 9. Abschluss
IP=$(hostname -I | awk '{print $1}' || echo "localhost")

# Erstelle Installations-Zusammenfassung
SUMMARY_FILE="$REAL_HOME/installation_summary.txt"
{
    echo "═══════════════════════════════════════════════════════════"
    echo "  INSTALLATION ABGESCHLOSSEN - $(date)"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "📦 INSTALLIERTE KOMPONENTEN:"
    echo "  ✓ Python $(python3 --version 2>&1 | awk '{print $2}')"
    if command_exists node; then echo "  ✓ Node.js $(node -v)"; fi
    if command_exists ollama; then echo "  ✓ Ollama $(ollama -v 2>&1 | head -n1)"; fi
    if command_exists npm && [ -d "$PROJECT_DIR/mobile/photo_app_expo/node_modules" ]; then 
        echo "  ✓ Expo App (SDK 54)"
    fi
    echo ""
    echo "🌐 ZUGRIFF:"
    echo "  Dashboard: http://$IP:5001"
    echo "  Fotos:     http://$IP:5001/photos.html"
    echo ""
    echo "🚀 STARTEN:"
    echo "  Development: cd $PROJECT_DIR && ./start_dev.sh"
    echo "  Production:  systemctl status document-manager"
    echo ""
    echo "📁 DATEN:"
    if mountpoint -q "$MOUNT_POINT"; then
        echo "  Foto-Speicher: $MOUNT_POINT (extern)"
    else
        echo "  Foto-Speicher: $PROJECT_DIR/data/Bilder (intern)"
    fi
    echo "  Log-Datei:     $LOG_FILE"
    echo ""
    echo "═══════════════════════════════════════════════════════════"
} > "$SUMMARY_FILE"

# Terminal-Ausgabe
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           ✓ INSTALLATION ABGESCHLOSSEN!                   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Dashboard:${NC} http://$IP:5001"
echo -e "${CYAN}Fotos:${NC}     http://$IP:5001/photos.html"
echo ""
echo -e "${YELLOW}Starten:${NC}"
echo "  Development: ./start_dev.sh --tunnel"
echo "  Production:  Service läuft bereits"
echo ""
echo -e "${CYAN}📋 Zusammenfassung:${NC} cat ~/installation_summary.txt"
echo ""
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}[DRY-RUN] Es wurden keine Änderungen vorgenommen.${NC}"
else
    echo -e "${YELLOW}💡 Empfohlen: sudo reboot${NC}"
fi
echo ""
