#!/bin/bash
#
# Installations-Script für Raspberry Pi
# Installiert alle Abhängigkeiten für das Dokumentenverwaltungssystem
#

echo "========================================="
echo "Dokumentenverwaltungssystem Installation"
echo "Raspberry Pi 5 - Setup"
echo "========================================="

# Prüfe Root
if [ "$EUID" -ne 0 ]; then
    echo "Bitte als Root ausführen (sudo ./install.sh)"
    exit 1
fi

echo ""
echo "=== Schritt 1: System-Update ==="
apt-get update
apt-get upgrade -y

echo ""
echo "=== Schritt 2: Python & Dependencies ==="
apt-get install -y python3 python3-pip python3-venv
apt-get install -y python3-dev build-essential

echo ""
echo "=== Schritt 3: Scanner-Treiber (SANE) ==="
apt-get install -y sane sane-utils libsane-dev
apt-get install -y hplip hplip-gui  # HP Scanner Support

echo ""
echo "=== Schritt 4: System-Abhängigkeiten & Redis ==="
echo "Installiere System-Pakete..."
apt-get update
apt-get install -y tesseract-ocr tesseract-ocr-deu tesseract-ocr-eng imagemagick poppler-utils libgl1-mesa-glx libglib2.0-0 redis-server

# Redis starten
systemctl enable redis-server
systemctl start redis-server

echo ""
echo "=== Schritt 5: Libraries ==="
apt-get install -y libjpeg-dev zlib1g-dev
apt-get install -y libopenblas-dev  # Für NumPy/ML

echo ""
echo "=== Schritt 6: Ollama Installation ==="
echo "Installiere Ollama für lokales LLM..."
curl -fsSL https://ollama.com/install.sh | sh

echo ""
echo "=== Schritt 7: Python Virtual Environment ==="
cd /home/pi/OrganisationsAI || exit
python3 -m venv venv
source venv/bin/activate

echo ""
echo "=== Schritt 8: Python Packages ==="
pip install --upgrade pip
pip install -r requirements.txt
pip install opencv-python==4.8.1.78
pip install prometheus-client==0.19.0

echo ""
echo "=== Schritt 9: Ollama Model Download ==="
echo "Lade Quantized Qwen2.5 Model herunter (ca. 4GB)..."
ollama pull qwen2.5:7b-q4_K_M

# Alternative: DeepSeek
# ollama pull deepseek-coder:1.3b

echo ""
echo "=== Schritt 10: Verzeichnisse erstellen ==="
mkdir -p /mnt/documents/storage
mkdir -p /mnt/documents/data
mkdir -p /tmp/scans
chmod -R 755 /mnt/documents

echo ""
echo "=== Schritt 11: Systemd Service ==="
cp systemd/document-manager.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable document-manager.service

echo ""
echo "=== Schritt 12: Scanner-Berechtigungen ==="
# Füge Benutzer zu Scanner-Gruppe hinzu
usermod -a -G scanner,lp pi

echo ""
echo "========================================="
echo "Installation abgeschlossen!"
echo "========================================="
echo ""
echo "Nächste Schritte:"
echo "1. Scanner anschließen und testen: scanimage -L"
echo "2. Konfiguration anpassen: nano config.yaml"
echo "3. System starten: sudo systemctl start document-manager"
echo "4. Status prüfen: sudo systemctl status document-manager"
echo "5. Dashboard öffnen: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "Log-Dateien: /var/log/document-manager/app.log"
echo "Dokumente: /mnt/documents/storage/"
echo ""
echo "WICHTIG: Raspberry Pi neu starten für Gruppen-Berechtigungen!"
echo ""
