#!/bin/bash
# Raspberry Pi Installation Script für OrganisationsAI
# Führt die verbleibenden Setup-Schritte automatisch aus

set -e  # Exit bei Fehler

echo "=================================================="
echo "OrganisationsAI - Raspberry Pi Setup"
echo "=================================================="

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Prüfe ob im richtigen Verzeichnis
if [ ! -f "main.py" ]; then
    echo -e "${RED}Fehler: main.py nicht gefunden!${NC}"
    echo "Bitte führe dieses Script aus dem Projektverzeichnis aus:"
    echo "  cd ~/Autodocumentsorganizer"
    echo "  bash raspberry_pi_install.sh"
    exit 1
fi

# 1. Virtual Environment
echo -e "\n${YELLOW}=== Schritt 1: Virtual Environment ===${NC}"
if [ ! -d "venv" ]; then
    echo "Erstelle Virtual Environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual Environment erstellt${NC}"
else
    echo -e "${GREEN}✓ Virtual Environment existiert bereits${NC}"
fi

# Aktiviere venv
source venv/bin/activate

# 2. Dependencies installieren
echo -e "\n${YELLOW}=== Schritt 2: Python Dependencies ===${NC}"
echo "Installiere Requirements..."
pip install --upgrade pip -q
pip install -r requirements.txt

echo -e "${GREEN}✓ Dependencies installiert${NC}"
echo -e "${GREEN}  → Flask, SQLAlchemy, Werkzeug, APScheduler${NC}"
echo -e "${GREEN}  → pytest, Coverage (dev)${NC}"

# Optional: Install dev dependencies
if [ -f "requirements-dev.txt" ]; then
    read -p "Development-Dependencies installieren? [J/n] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        pip install -r requirements-dev.txt -q
        echo -e "${GREEN}✓ Dev-Dependencies installiert${NC}"
    fi
fi

# 3. .env Datei erstellen
echo -e "\n${YELLOW}=== Schritt 3: .env Konfiguration ===${NC}"
if [ ! -f ".env" ]; then
    echo "Erstelle .env Datei..."
    
    # Generiere Secret Key
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    
    cat > .env << EOF
# Flask Secret Key (automatisch generiert)
SECRET_KEY=${SECRET_KEY}

# Email-Passwort (optional - nur wenn Email-Integration genutzt wird)
# EMAIL_PASSWORD=dein_email_app_passwort

# Optional: Datenbank-Pfad
# DATABASE_PATH=/home/$(whoami)/Autodocumentsorganizer/data/documents.db

# Optional: Ollama URL
# OLLAMA_URL=http://localhost:11434
EOF
    
    echo -e "${GREEN}✓ .env Datei erstellt${NC}"
    echo -e "${YELLOW}⚠ Bitte bearbeite .env wenn du Email-Integration nutzen möchtest${NC}"
else
    echo -e "${GREEN}✓ .env existiert bereits${NC}"
fi

# 4. Passwort-Migration
echo -e "\n${YELLOW}=== Schritt 4: Passwort-Hashing ===${NC}"
if [ -f "migrate_passwords.py" ]; then
    echo "Starte Passwort-Migration..."
    python3 migrate_passwords.py
    echo -e "${GREEN}✓ Passwörter gehasht${NC}"
else
    echo -e "${YELLOW}⚠ migrate_passwords.py nicht gefunden - überspringe${NC}"
fi

# 5. Log-Verzeichnis
echo -e "\n${YELLOW}=== Schritt 5: Log-Verzeichnis ===${NC}"
if [ ! -d "/var/log/document-manager" ]; then
    echo "Erstelle Log-Verzeichnis..."
    sudo mkdir -p /var/log/document-manager
    sudo chown $(whoami):$(whoami) /var/log/document-manager
    echo -e "${GREEN}✓ Log-Verzeichnis erstellt${NC}"
else
    echo -e "${GREEN}✓ Log-Verzeichnis existiert${NC}"
fi

# 6. Systemd Service
echo -e "\n${YELLOW}=== Schritt 6: Systemd Service ===${NC}"
if [ -f "systemd/document-manager.service" ]; then
    echo "Installiere Systemd Service..."
    sudo cp systemd/document-manager.service /etc/systemd/system/
    sudo systemctl daemon-reload
    
    # Frage ob Service aktiviert werden soll
    read -p "Service aktivieren (startet automatisch beim Boot)? [J/n] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        sudo systemctl enable document-manager
        echo -e "${GREEN}✓ Service aktiviert${NC}"
    fi
    
    # Frage ob Service gestartet werden soll
    read -p "Service jetzt starten? [J/n] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        sudo systemctl start document-manager
        echo -e "${GREEN}✓ Service gestartet${NC}"
        sleep 2
        sudo systemctl status document-manager --no-pager
    fi
else
    echo -e "${RED}✗ systemd/document-manager.service nicht gefunden${NC}"
fi

# 7. Ollama Model
echo -e "\n${YELLOW}=== Schritt 7: Ollama Model ===${NC}"
if command -v ollama &> /dev/null; then
    echo "Prüfe installierte Ollama Models..."
    if ! ollama list | grep -q "llama3.2"; then
        read -p "Möchtest du llama3.2:1b Model herunterladen? (1.3GB) [J/n] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            echo "Lade Model herunter (kann einige Minuten dauern)..."
            ollama pull llama3.2:1b
            echo -e "${GREEN}✓ Model heruntergeladen${NC}"
        fi
    else
        echo -e "${GREEN}✓ Ollama Model bereits installiert${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Ollama nicht gefunden${NC}"
fi

# Zusammenfassung
echo -e "\n${GREEN}=================================================="
echo "Installation abgeschlossen! ✓"
echo "==================================================${NC}"
echo ""
echo "Nächste Schritte:"
echo ""
echo "1. Web-UI aufrufen:"
echo "   http://localhost:5001"
echo "   oder von anderem Gerät:"
echo "   http://$(hostname -I | awk '{print $1}'):5001"
echo ""
echo "2. Login:"
echo "   → Siehe config.yaml für Username/Passwort"
echo ""
echo "3. Email-Integration (optional):"
echo "   → Bearbeite .env und config.yaml"
echo "   → Teste mit: python3 test_email_service.py"
echo ""
echo "4. Service-Befehle:"
echo "   sudo systemctl status document-manager"
echo "   sudo systemctl restart document-manager"
echo "   tail -f /var/log/document-manager/app.log"
echo ""
echo "5. Weitere Infos:"
echo "   → RASPBERRY_PI_SETUP.md"
echo ""

# Optional: IP anzeigen
IP=$(hostname -I | awk '{print $1}')
if [ ! -z "$IP" ]; then
    echo -e "${GREEN}Deine Raspberry Pi IP: $IP${NC}"
fi

echo ""
echo "Viel Erfolg! 🚀"
