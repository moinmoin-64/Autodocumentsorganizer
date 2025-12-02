# 📦 Detaillierte Installationsanleitung

> Intelligentes Dokumentenverwaltungssystem mit KI, OCR, Redis-Caching, Monitoring und Docker

**Stand:** Dezember 2024  
**Version:** 3.0 (Modernized Stack)  
**Plattformen:** Raspberry Pi, Ubuntu, Debian, Windows (Development), Docker

---

## 📋 Inhaltsverzeichnis

1. [Systemvoraussetzungen](#systemvoraussetzungen)
2. [Schnellstart mit Docker](#schnellstart-mit-docker)
3. [Raspberry Pi Installation](#raspberry-pi-installation)
4. [Ubuntu/Debian Installation](#ubuntudebian-installation)
5. [Windows Development Setup](#windows-development-setup)
6. [Mobile App (Expo) einrichten](#mobile-app-expo-einrichten)
7. [Erste Schritte](#erste-schritte)
8. [Konfiguration](#konfiguration)
9. [Monitoring & Health](#monitoring--health)
10. [Troubleshooting](#troubleshooting)

---

## 🖥️ Systemvoraussetzungen

### Hardware-Anforderungen

**Minimum (Raspberry Pi):**
- Raspberry Pi 4 (4GB RAM empfohlen)
- 32GB microSD-Karte
- Optional: USB-Speicher für Fotos
- Netzwerkverbindung (LAN oder WiFi)

**Empfohlen:**
- 8GB RAM
- 64GB+ Speicher
- Dedizierte externe Festplatte für Dokumente/Fotos

### Software-Voraussetzungen

**Betriebssystem:**
- Raspberry Pi OS (64-bit) **empfohlen**
- Ubuntu 22.04+ LTS
- Debian 11+

**Auto-installiert vom Script:**
- Python 3.11+
- Node.js 20.x
- Tesseract OCR
- ImageMagick
- Ollama (optional, AI-Chatbot)
- Redis (Caching)
- Docker (optional, für einfaches Deployment)

---

## 🐳 Schnellstart mit Docker

**Schnellste Methode - Empfohlen für Testing & Development!**

### Option A: Docker Compose (Lokal)

```bash
# Projekt klonen
git clone https://github.com/moinmoin-64/Autodocumentsorganizer.git
cd Autodocumentsorganizer

# Starten
docker-compose up -d

# Fertig! App läuft auf:
open http://localhost:5001
```

**Das ist alles!** 🎉
- ✅ Backend, Redis, Prometheus - alles inklusive
- ✅ Keine Dependencies manuell installieren
- ✅ Identisch auf Linux, Mac, Windows

### Option B: Nur Backend (ohne Docker)

Siehe [Raspberry Pi Installation](#raspberry-pi-installation) für traditionelles Setup.

---

## 🥧 Raspberry Pi Installation

### Schritt 1: OS vorbereiten

#### 1.1 Raspberry Pi Imager herunterladen

```bash
# Auf deinem PC/Mac
https://www.raspberrypi.com/software/
```

#### 1.2 SD-Karte flashen

1. **Raspberry Pi Imager öffnen**
2. **OS wählen:** Raspberry Pi OS (64-bit)
3. **SD-Karte wählen**
4. **⚙️ Einstellungen konfigurieren:**
   - Hostname: `raspberrypi`
   - SSH aktivieren ✅
   - Benutzername: `pi`
   - Passwort: `[dein-passwort]`
   - WiFi konfigurieren (optional)
   - Zeitzone: `Europe/Berlin`
   - Tastaturlayout: `de`

5. **Schreiben & Warten** (~10 Min.)

#### 1.3 Raspberry Pi starten

1. SD-Karte einlegen
2. Optional: USB-Speicher anschließen
3. Netzwerkkabel anschließen
4. Stromkabel anschließen → bootet automatisch

---

### Schritt 2: Verbindung herstellen

#### 2.1 IP-Adresse finden

**Option A - Router:**
```
Router Web-Interface → Geräteliste → "raspberrypi" → IP notieren
Beispiel: 192.168.1.42
```

**Option B - IP-Scanner:**
```bash
# Windows: Advanced IP Scanner
# Mac/Linux:
nmap -sn 192.168.1.0/24 | grep raspberrypi
```

#### 2.2 SSH-Verbindung

**Windows (PowerShell):**
```powershell
ssh pi@192.168.1.42
# Passwort eingeben
```

**Mac/Linux:**
```bash
ssh pi@192.168.1.42
# Passwort eingeben
```

✅ **Erfolgreich:** Terminal zeigt `pi@raspberrypi:~ $`

---

### Schritt 3: Projekt klonen

```bash
# Git installieren (falls nicht vorhanden)
sudo apt-get update
sudo apt-get install git -y

# Repository klonen
cd ~
git clone https://github.com/moinmoin-64/Autodocumentsorganizer.git
cd Autodocumentsorganizer
```

✅ **Prüfen:**
```bash
ls -la
# Sollte zeigen: install.sh, app/, mobile/, config.yaml, etc.
```

---

### Schritt 4: Installation ausführen

#### 4.1 Script ausführbar machen

```bash
chmod +x install.sh
chmod +x start_dev.sh
```

#### 4.2 Installation starten

```bash
sudo ./install.sh
```

> ⚠️ **Wichtig:** Als Root ausführen (mit `sudo`)!

#### 4.3 Installation läuft automatisch ab

Das Script führt **vollautomatisch** folgende Schritte aus:

**[1/10] System-Checks** ✅
- OS-Kompatibilität
- Python-Version
- Internet-Verbindung

**[2/10] Swap-Konfiguration** 💾
- Prüft verfügbaren RAM
- Erweitert Swap auf 2GB bei Bedarf

**[3/10] Speicher-Setup** 💿
- Erkennt USB-Speicher
- Fragt nach Nutzung (Timeout: 10s)
- Mountet automatisch

**[4/10] System-Pakete** 📦
```
Python, Node.js, Tesseract, ImageMagick, 
Redis, Scanner-Tools, Build-Tools
```

**[4.5/10] Docker Installation** 🐳 **(NEU!)**
- Fragt: "Docker installieren?"
- Installiert Docker + Docker Compose
- Fügt User zu docker-Gruppe hinzu

**[5/10] Ollama Installation** 🤖
- Download mit HTTP/1.1 (stabil)
- Retry-Logik bei Fehlern
- Optional überspringbar

**[6/10] Python-Umgebung** 🐍
- Virtual Environment erstellen
- Dependencies installieren
- **Neu:** `pydantic`, `redis` automatisch

**[7/10] Native C/C++ Extensions** ⚡ **(Performance!)**
- Kompiliert `image_fast.c`
- Kompiliert `ocr_accelerator.cpp`
- Kompiliert `search_indexer.cpp`
- **Ergebnis:** 30-100x schneller!

**[8/10] Expo App Setup** 📱
- npm dependencies installieren
- SDK 54 Pakete prüfen
- EAS CLI installieren

**[9/10] Datenbank & Service** 🗄️
- Datenbank initialisieren
- Database migrations ausführen
- Verzeichnisse erstellen
- Systemd-Service konfigurieren
- Service aktivieren & starten

**[10/10] Validierung** ✅
- Virtual Environment ✓
- Datenbank ✓
- Service ✓
- Expo App ✓
- Native Extensions ✓

#### 4.4 Dauer

⏱️ **Total:** 25-45 Minuten
- System-Pakete: ~5 Min.
- Docker: ~3 Min.
- Ollama: ~5-10 Min.
- Python-Pakete: ~5-10 Min.
- **Native Extensions:** ~5 Min. **(NEU!)**
- Expo: ~5-10 Min.

#### 4.5 Erfolgs-Meldung

```
╔════════════════════════════════════════╗
║   ✓ INSTALLATION ABGESCHLOSSEN!        ║
╚════════════════════════════════════════╝

📦 INSTALLIERTE KOMPONENTEN:
  ✓ Python 3.11
  ✓ Node.js 20.x
  ✓ Ollama (AI)
  ✓ Expo App (SDK 54)
  ✓ Native Extensions (C/C++)
  ✓ Docker 24.x.x

🌐 ZUGRIFF:
  Dashboard:   http://192.168.1.42:5001
  Fotos:       http://192.168.1.42:5001/photos.html
  Health:      http://192.168.1.42:5001/api/monitoring/health
  Metrics:     http://192.168.1.42:5001/metrics

🚀 STARTEN:
  Development: ./start_dev.sh --tunnel
  Docker:      docker-compose up -d
  Production:  Service läuft bereits

📋 Zusammenfassung: cat ~/installation_summary.txt

💡 Empfohlen: sudo reboot
```

---

### Schritt 5: System neu starten

```bash
sudo reboot
```

**Warten:** ~1 Minute

**Neu verbinden:**
```bash
ssh pi@192.168.1.42
cd Autodocumentsorganizer
```

---

### Schritt 6: System testen

#### 6.1 Service-Status prüfen

```bash
# Backend-Service prüfen
sudo systemctl status document-manager

# Sollte zeigen: active (running)
```

#### 6.2 Web-Dashboard öffnen

Auf deinem PC/Laptop im Browser:
```
http://192.168.1.42:5001
```

✅ **Du siehst:** Dokumentenverwaltung Dashboard

#### 6.3 Neue Endpoints testen

**Health Check:**
```
http://192.168.1.42:5001/api/monitoring/health
```

Response zeigt Status von:
- ✅ Database
- ✅ Ollama (AI)
- ✅ Redis (Cache)
- ✅ Disk Space

**Prometheus Metrics:**
```
http://192.168.1.42:5001/metrics
```

**System Stats:**
```
http://192.168.1.42:5001/api/monitoring/system
```

---

## 🖥️ Ubuntu/Debian Installation

Identisch zu Raspberry Pi, aber:

### Unterschiede:

1. **Kein Image flashen** (bereits installiert)
2. **Direkter Start:**
   ```bash
   git clone https://github.com/moinmoin-64/Autodocumentsorganizer.git
   cd Autodocumentsorganizer
   sudo ./install.sh
   ```

### Empfohlene Optionen:

```bash
# Ohne Ollama (spart Zeit auf Desktop)
sudo ./install.sh --skip-ollama

# Nur Backend, ohne Expo
sudo ./install.sh --skip-expo

# Debug-Mode für Fehlersuche
sudo ./install.sh --log-level debug
```

---

## 💻 Windows Development Setup

### Option A: Docker (Empfohlen)

1. **Docker Desktop installieren**
   - https://www.docker.com/products/docker-desktop/

2. **Projekt starten**
   ```powershell
   git clone https://github.com/moinmoin-64/Autodocumentsorganizer.git
   cd Autodocumentsorganizer
   docker-compose up -d
   ```

### Option B: WSL2

```powershell
# In PowerShell (als Administrator)
wsl --install -d Ubuntu-22.04
```

Nach Installation:
```bash
# In WSL2-Terminal
git clone https://github.com/moinmoin-64/Autodocumentsorganizer.git
cd Autodocumentsorganizer
sudo ./install.sh
```

### Option C: Direkt auf Windows

#### Schritt 1: Manuelle Dependencies

1. **Python 3.12+ installieren**
   - https://www.python.org/downloads/
   - ✅ "Add to PATH" aktivieren

2. **Node.js 20.x installieren**
   - https://nodejs.org/

3. **Git installieren**
   - https://git-scm.com/downloads

#### Schritt 2: Projekt klonen

```powershell
cd C:\Users\[dein-name]\Programmieren
git clone https://github.com/moinmoin-64/Autodocumentsorganizer.git
cd Autodocumentsorganizer
```

#### Schritt 3: Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

#### Schritt 4: Starten

```powershell
.\start_dev.bat --tunnel
```

---

## 📱 Mobile App (Expo) einrichten

### Schritt 1: Expo Go App installieren

**iPhone:**
- App Store → "Expo Go" → Installieren

**Android:**
- Play Store → "Expo Go" → Installieren

### Schritt 2: Development Server starten

**Auf Raspberry Pi / Linux:**
```bash
./start_dev.sh --tunnel
```

**Auf Windows:**
```powershell
.\start_dev.bat --tunnel
```

> 💡 **`--tunnel` ist wichtig** für Remote-Zugriff!

### Schritt 3: QR-Code scannen

Terminal zeigt:
```
╔════════════════════════════════════════╗
║  📱  EXPO DEVELOPMENT SERVER           ║
║  🌐 TUNNEL MODE aktiv                  ║
╚════════════════════════════════════════╝

█▀▀▀▀▀█ ... [QR-Code] ... █▀▀▀▀▀█
```

**Scannen:**
- **iOS:** Kamera-App öffnen → QR scannen
- **Android:** Expo Go App → "Scan QR Code"

### Schritt 4: Server-URL eingeben

Beim **ersten Start** der App:
```
Server-Adresse:
http://192.168.1.42:5001

→ "Verbinden" klicken
```

✅ **Erfolgreich:** Foto-Gallery erscheint!

---

## 🎯 Erste Schritte

### Web-Interface nutzen

#### Dashboard
```
http://192.168.1.42:5001
```

**Features:**
- Dokumente hochladen (Drag & Drop)
- **Async-Processing** (keine Blockierung mehr!)
- Suche mit Filtern
- Kategorien verwalten
- Statistiken ansehen (mit Redis-Caching)

#### Foto-Verwaltung
```
http://192.168.1.42:5001/photos.html
```

**Features:**
- Grid-Ansicht (iOS-Style)
- Vollbild-Viewer
- Download
- Upload via Drag & Drop

### Dokument hochladen

1. Dashboard öffnen
2. Drag & Drop oder "Upload" klicken
3. PDF/Bild auswählen
4. **Automatisch:**
   - **OCR-Texterkennung** (50x schneller mit C++)
   - **KI-Kategorisierung** (via Ollama)
   - **Datum-Extraktion**
   - **Schlagwort-Generierung**

---

## ⚙️ Konfiguration

### config.yaml bearbeiten

```bash
nano config.yaml
```

#### Wichtige Einstellungen:

**Web-Server:**
```yaml
web:
  host: 0.0.0.0  # Alle Interfaces
  port: 5001
  secret_key: "dein-geheimer-schluessel"
```

**Redis (NEU!):**
```yaml
redis:
  host: localhost
  port: 6379
  db: 0
```

**Ollama (KI):**
```yaml
ai:
  ollama:
    enabled: true
    url: http://localhost:11434
    model: llama3.2:1b  # Für Raspberry Pi
```

**E-Mail (optional):**
```yaml
email:
  enabled: false  # true für automatischen Import
  host: imap.gmail.com
  user: deine-email@gmail.com
  password: app-passwort
  poll_interval: 300  # Sekunden
```

---

## 📊 Monitoring & Health

### Health Checks

**Detaillierter Status:**
```bash
curl http://192.168.1.42:5001/api/monitoring/health
```

**Response:**
```json
{
  "status": "ok",
  "components": {
    "database": {"status": "ok"},
    "ollama": {"status": "ok", "url": "http://localhost:11434"},
    "redis": {"status": "ok", "host": "localhost"},
    "disk": {"status": "ok", "percent": 45.2, "free": 120000000}
  }
}
```

### System-Statistiken

```bash
curl http://192.168.1.42:5001/api/monitoring/system
```

**Zeigt:**
- CPU-Auslastung
- RAM-Nutzung
- Swap-Nutzung

### Prometheus Metrics

```bash
curl http://192.168.1.42:5001/metrics
```

**Für:**
- Grafana Dashboards
- Alerting
- Performance-Tracking

---

## 🐛 Troubleshooting

### Problem: Installation schlägt fehl

**Symptom:** Script bricht mit Fehler ab

**Lösung:**
```bash
# Log-Datei prüfen
cat ~/install_*.log

# Netzwerk prüfen
ping -c 3 8.8.8.8

# Ohne Ollama neu versuchen
sudo ./install.sh --skip-ollama
```

---

### Problem: Backend startet nicht

**Symptom:** Port 5001 nicht erreichbar

**Lösung:**
```bash
# Service-Status prüfen
sudo systemctl status document-manager

# Logs ansehen
sudo journalctl -u document-manager -f

# Manuell starten
./start_dev.sh
```

---

### Problem: Redis nicht erreichbar

**Symptom:** Health Check zeigt Redis unavailable

**Lösung:**
```bash
# Redis-Status prüfen
sudo systemctl status redis-server

# Redis starten
sudo systemctl start redis-server

# Testen
redis-cli ping
# Sollte antworten: PONG
```

---

### Problem: Native Extensions fehlen

**Symptom:** Warnung: "Native extensions not found"

**Lösung:**
```bash
# GCC installieren
sudo apt-get install build-essential

# Extensions neu kompilieren
source venv/bin/activate
python setup.py build_ext --inplace
```

---

## 📚 Weitere Ressourcen

### Dokumentation

- **README.md** - Projekt-Übersicht
- **DOCKER_GUIDE.md** - Docker & Kubernetes Deployment
- **QUICKSTART.md** - Schnellstart-Guide
- **~/installation_summary.txt** - Installations-Zusammenfassung

### Support

- **GitHub Issues:** https://github.com/moinmoin-64/Autodocumentsorganizer/issues
- **Logs:** `~/install_*.log`
- **Backend-Logs:** `/tmp/backend.log`
- **Application Logs:** `logs/`

### Wichtige Befehle

```bash
# Service Management
sudo systemctl start document-manager
sudo systemctl stop document-manager
sudo systemctl restart document-manager
sudo systemctl status document-manager

# Development
./start_dev.sh --tunnel        # Mit Remote-Zugriff
./start_dev.sh --web           # Im Browser
./start_dev.sh --lan           # Lokal

# Docker
docker-compose up -d           # Starten
docker-compose down            # Stoppen
docker-compose logs -f app     # Logs ansehen

# Updates
git pull origin main
sudo systemctl restart document-manager

# Backup
tar -czf backup.tar.gz data/ config.yaml
```

---

## ✅ Erfolgs-Checkliste

Nach Installation sollte alles funktionieren:

- [ ] Dashboard erreichbar: `http://[IP]:5001` ✅
- [ ] Fotos-Seite funktioniert ✅
- [ ] Health Check: `/api/monitoring/health` ✅
- [ ] Metrics: `/metrics` ✅
- [ ] Redis läuft: `redis-cli ping` ✅
- [ ] Expo App verbindet sich ✅
- [ ] Foto-Upload klappt ✅
- [ ] OCR verarbeitet PDFs (50x schneller!) ✅
- [ ] Service startet automatisch ✅

---

## 🎉 Geschafft!

Dein System ist jetzt **production-ready**:

- ✅ **Backend** läuft auf Raspberry Pi
- ✅ **Web-Dashboard** ist erreichbar
- ✅ **Mobile App** ist verbunden
- ✅ **OCR + KI** sind aktiv (massiv beschleunigt)
- ✅ **Redis Caching** aktiv
- ✅ **Monitoring** konfiguriert
- ✅ **CI/CD** mit GitHub Actions
- ✅ **Docker** ready
- ✅ **Automatischer Start** bei Boot

**Viel Erfolg! 🚀**

---

**Letzte Aktualisierung:** Dezember 2024  
**Version:** 3.0 (Modernized Stack - Async, Redis, Monitoring, Docker)
