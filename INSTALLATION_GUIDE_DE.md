# 📦 Detaillierte Installationsanleitung

> Intelligentes Dokumentenverwaltungssystem mit KI, OCR und Mobile App

**Stand:** November 2024  
**Plattformen:** Raspberry Pi, Ubuntu, Debian, Windows (Development)

---

## 📋 Inhaltsverzeichnis

1. [Systemvoraussetzungen](#systemvoraussetzungen)
2. [Raspberry Pi Installation](#raspberry-pi-installation)
3. [Ubuntu/Debian Installation](#ubuntudebian-installation)
4. [Windows Development Setup](#windows-development-setup)
5. [Mobile App (Expo) einrichten](#mobile-app-expo-einrichten)
6. [Erste Schritte](#erste-schritte)
7. [Konfiguration](#konfiguration)
8. [Troubleshooting](#troubleshooting)

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
- Ollama (optional)
- Redis

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
   - Benutzername: [pi](file:///c:/Users/olist/Programmieren/OrganisationsAI/tests/test_e2e.py#298-332)
   - Passwort: `[dein-passwort]`
   - WiFi konfigurieren (optional)
   - Zeitzone: `Europe/Berlin`
   - Tastaturlayout: [de](file:///c:/Users/olist/Programmieren/OrganisationsAI/app/server.py#158-162)

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

**[1/9] System-Checks** ✅
- OS-Kompatibilität
- Python-Version
- Internet-Verbindung

**[2/9] Swap-Konfiguration** 💾
- Prüft verfügbaren RAM
- Erweitert Swap auf 2GB bei Bedarf

**[3/9] Speicher-Setup** 💿
- Erkennt USB-Speicher
- Fragt nach Nutzung (Timeout: 10s)
- Mountet automatisch

**[4/9] System-Pakete** 📦
```
Python, Node.js, Tesseract, ImageMagick, 
Redis, Scanner-Tools, Build-Tools
```

**[5/9] Ollama Installation** 🤖
- Download mit HTTP/1.1 (stabil)
- Retry-Logik bei Fehlern
- Optional überspringbar

**[6/9] Python-Umgebung** 🐍
- Virtual Environment erstellen
- Dependencies installieren
- Pillow & QR-Code Support

**[7/9] Expo App Setup** 📱
- npm dependencies installieren
- SDK 54 Pakete prüfen
- EAS CLI installieren

**[8/9] Datenbank & Service** 🗄️
- Datenbank initialisieren
- Verzeichnisse erstellen
- Systemd-Service konfigurieren
- Service aktivieren & starten

**[9/9] Validierung** ✅
- Virtual Environment ✓
- Datenbank ✓
- Service ✓
- Expo App ✓

#### 4.4 Dauer

⏱️ **Total:** 20-40 Minuten
- System-Pakete: ~5 Min.
- Ollama: ~5-10 Min.
- Python-Pakete: ~5-10 Min.
- Expo: ~5-10 Min.

#### 4.5 Erfolgs-Meldung

```
╔════════════════════════════════════════╗
║   ✓ INSTALLATION ABGESCHLOSSEN!        ║
╚════════════════════════════════════════╝

Dashboard: http://192.168.1.42:5001
Fotos:     http://192.168.1.42:5001/photos.html

Starten:
  Development: ./start_dev.sh --tunnel
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

#### 6.3 Fotos-Seite testen

```
http://192.168.1.42:5001/photos.html
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

### Schritt 1: WSL2 installieren (empfohlen)

**Option A - WSL2 (empfohlen):**

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

**Option B - Direkt auf Windows:**

### Schritt 2: Manuelle Dependencies

1. **Python 3.12+ installieren**
   - https://www.python.org/downloads/
   - ✅ "Add to PATH" aktivieren

2. **Node.js 20.x installieren**
   - https://nodejs.org/

3. **Git installieren**
   - https://git-scm.com/downloads

### Schritt 3: Projekt klonen

```powershell
cd C:\Users\[dein-name]\Programmieren
git clone https://github.com/moinmoin-64/Autodocumentsorganizer.git
cd Autodocumentsorganizer
```

### Schritt 4: Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Schritt 5: Expo App

```powershell
cd mobile\photo_app_expo
npm install
npx expo install --fix
```

### Schritt 6: Starten

```powershell
# Im Projekt-Root
.\start_dev.bat --tunnel
```

Öffnet 2 neue Fenster:
1. Backend Server
2. Expo Development Server

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

### Schritt 5: Fotos hochladen

1. **Kamera** (Blauer Button) → Neues Foto machen
2. **Import** (Grüner Button) → Aus Galerie wählen
3. Automatischer Upload!

**Gespeichert in:**
```
/mnt/photos/Bilder/2024/11/30/photo_143022.jpg
```

---

## 🎯 Erste Schritte

### Web-Interface nutzen

#### Dashboard
```
http://192.168.1.42:5001
```

**Features:**
- Dokumente hochladen (Drag & Drop)
- Suche mit Filtern
- Kategorien verwalten
- Statistiken ansehen

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
   - OCR-Texterkennung
   - KI-Kategorisierung
   - Datum-Extraktion
   - Schlagwort-Generierung

### Scanner nutzen (optional)

```bash
# Scanner suchen
scanimage -L

# Test-Scan
scanimage --format=png > test.png
```

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

**Auth:**
```yaml
auth:
  enabled: true
  users:
    admin: "scrypt:..." # Gehashtes Passwort
```

Passwort hashen:
```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('dein-passwort'))"
```

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

### Problem: Expo kann nicht verbinden

**Symptom:** "Unable to connect to Metro"

**Checkliste:**
- ✅ Gleiches WiFi-Netzwerk (Pi & Handy)?
- ✅ Backend läuft? `curl http://192.168.1.42:5001`
- ✅ Firewall aus? `sudo ufw status`
- ✅ `--tunnel` Flag benutzt?

**Lösung:**
```bash
# Mit Tunnel-Mode
./start_dev.sh --tunnel

# Firewall öffnen (falls nötig)
sudo ufw allow 5001
sudo ufw allow 8081
```

---

### Problem: Ollama Installation fehlgeschlagen

**Symptom:** HTTP/2 Fehler oder Timeout

**Lösung:**
```bash
# Installation überspringen
sudo ./install.sh --skip-ollama

# Manuell installieren (später)
curl --http1.1 -fsSL https://ollama.com/install.sh | sh
```

---

### Problem: Wenig Speicherplatz

**Symptom:** "No space left on device"

**Lösung:**
```bash
# Speicherplatz prüfen
df -h

# Alte Logs löschen
sudo journalctl --vacuum-time=7d

# Docker-Images löschen (falls vorhanden)
docker system prune -a

# USB-Speicher für Fotos nutzen
# Wird beim install.sh gefragt!
```

---

### Problem: Permission Denied

**Symptom:** "Permission denied" bei Dateien

**Lösung:**
```bash
# Besitzer korrigieren
sudo chown -R $USER:$USER ~/Autodocumentsorganizer

# Script neu ausführen
sudo ./install.sh
```

---

## 📚 Weitere Ressourcen

### Dokumentation

- **README.md** - Projekt-Übersicht
- **QUICKSTART.md** - Schnellstart-Guide
- **~/**installation_summary.txt** - Installations-Zusammenfassung

### Support

- **GitHub Issues:** https://github.com/moinmoin-64/Autodocumentsorganizer/issues
- **Logs:** `~/install_*.log`
- **Backend-Logs:** `/tmp/backend.log`

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
- [ ] Expo App verbindet sich ✅
- [ ] Foto-Upload klappt ✅
- [ ] OCR verarbeitet PDFs ✅
- [ ] Service startet automatisch ✅
- [ ] Backup-Ordner existiert ✅

---

## 🎉 Geschafft!

Dein System ist jetzt einsatzbereit:

- ✅ **Backend** läuft auf Raspberry Pi
- ✅ **Web-Dashboard** ist erreichbar
- ✅ **Mobile App** ist verbunden
- ✅ **OCR + KI** sind aktiv
- ✅ **Automatischer Start** bei Boot

**Viel Erfolg! 🚀**

---

**Letzte Aktualisierung:** November 2024  
**Version:** 2.0 (Expo SDK 54, Automatische Scripts)
