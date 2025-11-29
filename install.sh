#!/bin/bash
#
# KORRIGIERTES Installations-Script für Raspberry Pi
# Behebt Probleme mit Debian Trixie und flexiblen Pfaden
#

set -e  # Exit bei Fehler

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================="
echo "Dokumentenverwaltungssystem Installation"
echo "Raspberry Pi - Setup (Debian Trixie)"
echo "========================================="

# Prüfe Root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Bitte als Root ausführen: sudo ./install.sh${NC}"
    exit 1
fi

# Speichere den ursprünglichen User (nicht root)
REAL_USER=${SUDO_USER:-$(logname)}
REAL_HOME=$(eval echo "~$REAL_USER")

echo -e "${GREEN}Installation für User: $REAL_USER${NC}"
echo -e "${GREEN}Home-Verzeichnis: $REAL_HOME${NC}"

echo ""
echo -e "${YELLOW}=== Schritt 1: System-Update ===${NC}"
apt-get update
apt-get upgrade -y

echo ""
echo -e "${YELLOW}=== Schritt 2: Python & Dependencies ===${NC}"
apt-get install -y python3 python3-pip python3-venv
apt-get install -y python3-dev build-essential

echo ""
echo -e "${YELLOW}=== Schritt 3: Scanner-Treiber (SANE) ===${NC}"
apt-get install -y sane sane-utils libsane-dev
apt-get install -y hplip hplip-gui  # HP Scanner Support
echo -e "${GREEN}✓ Scanner-Treiber installiert${NC}"

echo ""
echo -e "${YELLOW}=== Schritt 4: System-Abhängigkeiten ===${NC}"
echo "Installiere System-Pakete..."
apt-get update

# Installiere Pakete einzeln mit Error-Handling
PACKAGES=(
    "tesseract-ocr"
    "tesseract-ocr-deu"
    "tesseract-ocr-eng"
    "imagemagick"
    "poppler-utils"
    "libglib2.0-0t64"  # Debian Trixie Version
)

for pkg in "${PACKAGES[@]}"; do
    echo "Installiere $pkg..."
    if apt-get install -y "$pkg" 2>/dev/null; then
        echo -e "${GREEN}✓ $pkg installiert${NC}"
    else
        echo -e "${YELLOW}⚠ $pkg übersprungen (nicht verfügbar)${NC}"
    fi
done

# libgl1-mesa-glx wurde ersetzt durch libgl1
echo "Installiere OpenGL Libraries..."
if apt-get install -y libgl1 2>/dev/null; then
    echo -e "${GREEN}✓ libgl1 installiert${NC}"
else
    echo -e "${YELLOW}⚠ libgl1 nicht verfügbar, versuche libgl1-mesa-dri...${NC}"
    apt-get install -y libgl1-mesa-dri || echo -e "${YELLOW}⚠ OpenGL übersprungen${NC}"
fi

# Redis ist optional - Flask-Limiter kann auch ohne funktionieren
echo ""
echo -e "${YELLOW}Redis Server (optional für Rate Limiting):${NC}"
if apt-get install -y redis-server 2>/dev/null; then
    systemctl enable redis-server 2>/dev/null || true
    systemctl start redis-server 2>/dev/null || true
    echo -e "${GREEN}✓ Redis installiert${NC}"
else
    echo -e "${YELLOW}⚠ Redis nicht verfügbar - Flask-Limiter nutzt Memory-Backend${NC}"
fi

echo ""
echo -e "${YELLOW}=== Schritt 5: Libraries ===${NC}"
apt-get install -y libjpeg-dev zlib1g-dev
apt-get install -y libopenblas-dev  # Für NumPy/ML
echo -e "${GREEN}✓ Development Libraries installiert${NC}"

echo ""
echo -e "${YELLOW}=== Schritt 6: Ollama Installation ===${NC}"
echo "Installiere Ollama für lokales LLM..."
if curl -fsSL https://ollama.com/install.sh | sh; then
    echo -e "${GREEN}✓ Ollama installiert${NC}"
else
    echo -e "${RED}✗ Ollama Installation fehlgeschlagen${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}=== Schritt 7: Python Virtual Environment ===${NC}"

# Finde Projekt-Verzeichnis
PROJECT_DIR=""
if [ -d "$REAL_HOME/Autodocumentsorganizer" ]; then
    PROJECT_DIR="$REAL_HOME/Autodocumentsorganizer"
elif [ -d "$REAL_HOME/OrganisationsAI" ]; then
    PROJECT_DIR="$REAL_HOME/OrganisationsAI"
elif [ -d "$(pwd)" ] && [ -f "$(pwd)/main.py" ]; then
    PROJECT_DIR="$(pwd)"
else
    echo -e "${RED}Fehler: Projekt-Verzeichnis nicht gefunden!${NC}"
    echo "Bitte führe install.sh aus dem Projektverzeichnis aus"
    exit 1
fi

echo -e "${GREEN}Projekt-Verzeichnis: $PROJECT_DIR${NC}"
cd "$PROJECT_DIR" || exit 1

# Erstelle venv als richtiger User (nicht root)
if [ ! -d "venv" ]; then
    echo "Erstelle Virtual Environment..."
    sudo -u "$REAL_USER" python3 -m venv venv
    echo -e "${GREEN}✓ Virtual Environment erstellt${NC}"
else
    echo -e "${GREEN}✓ Virtual Environment existiert bereits${NC}"
fi

echo ""
echo -e "${YELLOW}=== Schritt 8: Python Packages ===${NC}"
# Aktiviere venv und installiere als richtiger User
sudo -u "$REAL_USER" bash -c "
    source venv/bin/activate
    pip install --upgrade pip -q
    echo 'Installing Python packages from requirements.txt...'
    pip install -r requirements.txt
    echo 'Installing development dependencies...'
    pip install -r requirements-dev.txt || echo 'Dev dependencies optional'
"
echo -e "${GREEN}✓ Python Packages installiert${NC}"
echo -e "${GREEN}  → Flask, SQLAlchemy, pytest, etc.${NC}"

echo ""
echo -e "${YELLOW}=== Schritt 9: Ollama Model Download ===${NC}"
echo "Welches Model möchtest du installieren?"
echo "1) llama3.2:1b  (1.3GB, schnell, für Pi empfohlen)"
echo "2) llama3.2:3b  (3GB, bessere Qualität)"
echo "3) qwen2.5:7b-q4_K_M  (4GB, beste Qualität)"
echo "4) Überspringen"
read -p "Wahl [1-4]: " -n 1 -r MODEL_CHOICE
echo ""

case $MODEL_CHOICE in
    1)
        echo "Lade llama3.2:1b herunter..."
        sudo -u "$REAL_USER" ollama pull llama3.2:1b
        echo -e "${GREEN}✓ Model heruntergeladen${NC}"
        ;;
    2)
        echo "Lade llama3.2:3b herunter..."
        sudo -u "$REAL_USER" ollama pull llama3.2:3b
        echo -e "${GREEN}✓ Model heruntergeladen${NC}"
        ;;
    3)
        echo "Lade qwen2.5:7b-q4_K_M herunter..."
        sudo -u "$REAL_USER" ollama pull qwen2.5:7b-q4_K_M
        echo -e "${GREEN}✓ Model heruntergeladen${NC}"
        ;;
    *)
        echo -e "${YELLOW}⚠ Model-Download übersprungen${NC}"
        ;;
esac

echo ""
echo -e "${YELLOW}=== Schritt 10: Verzeichnisse erstellen ===${NC}"
# Nutze data/ Verzeichnis im Projekt
mkdir -p "$PROJECT_DIR/data/uploads"
mkdir -p "$PROJECT_DIR/data/backups"
mkdir -p "$PROJECT_DIR/data/exports"
mkdir -p /tmp/scans
chown -R "$REAL_USER:$REAL_USER" "$PROJECT_DIR/data"
chmod -R 755 "$PROJECT_DIR/data"
echo -e "${GREEN}✓ Verzeichnisse erstellt${NC}"

echo ""
echo -e "${YELLOW}=== Schritt 11: Systemd Service ===${NC}"
if [ -f "systemd/document-manager.service" ]; then
    cp systemd/document-manager.service /etc/systemd/system/
    systemctl daemon-reload
    
    read -p "Service aktivieren (Auto-Start)? [J/n] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        systemctl enable document-manager.service
        echo -e "${GREEN}✓ Service aktiviert${NC}"
    fi
else
    echo -e "${YELLOW}⚠ systemd/document-manager.service nicht gefunden${NC}"
fi

echo ""
echo -e "${YELLOW}=== Schritt 12: Scanner-Berechtigungen ===${NC}"
usermod -a -G scanner,lp "$REAL_USER" 2>/dev/null || echo -e "${YELLOW}⚠ Gruppen existieren noch nicht${NC}"

echo ""
echo -e "${YELLOW}=== Schritt 13: Log-Verzeichnis ===${NC}"
mkdir -p /var/log/document-manager
chown "$REAL_USER:$REAL_USER" /var/log/document-manager
echo -e "${GREEN}✓ Log-Verzeichnis erstellt${NC}"

echo ""
echo -e "${GREEN}========================================="
echo "Installation abgeschlossen! ✓"
echo "=========================================${NC}"
echo ""
echo "Nächste Schritte:"
echo ""
echo "1. Wechsle zum User: exit (aus root)"
echo ""
echo "2. Passwort-Migration ausführen:"
echo "   cd $PROJECT_DIR"
echo "   source venv/bin/activate"
echo "   python3 migrate_passwords.py"
echo ""
echo "3. .env Datei konfigurieren:"
echo "   nano $PROJECT_DIR/.env"
echo "   # SECRET_KEY generieren mit:"
echo "   python3 -c \"import secrets; print(secrets.token_hex(32))\""
echo ""
echo "4. Service starten:"
echo "   sudo systemctl start document-manager"
echo "   sudo systemctl status document-manager"
echo ""
echo "5. Dashboard öffnen:"
IP=$(hostname -I | awk '{print $1}')
echo "   http://$IP:5001"
echo ""
echo "Log-Dateien: /var/log/document-manager/app.log"
echo "Projekt: $PROJECT_DIR"
echo ""
echo -e "${YELLOW}WICHTIG: Raspberry Pi neu starten für Gruppen-Berechtigungen!${NC}"
echo ""
