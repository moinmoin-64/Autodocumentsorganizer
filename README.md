# Intelligentes Dokumentenverwaltungssystem für Raspberry Pi

Ein KI-gestütztes System zur automatischen Kategorisierung und Verwaltung gescannter Dokumente mit Web-Dashboard und Chatbot-Integration.

## 🌟 Features

- **Automatische Dokumentenverarbeitung**: Scanner-Integration mit OCR (Tesseract)
- **KI-basierte Kategorisierung**: Intelligente Einordnung mit Sentence Transformers
- **Intelligente Ordnerstruktur**: Automatische Organisation nach Jahr/Kategorie/Subkategorie
- **CSV-Daten-Extraktion**: Strukturierte Datenextraktion für Analysen
- **Web-Dashboard**: Responsive Interface mit Charts und Statistiken
- **Ollama-Chatbot**: Lokaler AI-Assistent für Fragen zu Dokumenten
- **BM25-Suche**: Intelligente Volltextsuche
- **Jahresvergleiche**: Ausgaben-Analysen und Trends

## 📋 Voraussetzungen

- **Hardware**: Raspberry Pi 5 (8GB RAM empfohlen)
- **Storage**: 2TB SSD (USB-angeschlossen)
- **Scanner**: HP Scanner/Drucker (SANE-kompatibel)
- **OS**: Raspberry Pi OS (64-bit)

## 🚀 Installation

### 1. Repository klonen

```bash
cd /home/pi
git clone <your-repo-url> OrganisationsAI
cd OrganisationsAI
```

### 2. Installations-Script ausführen

```bash
chmod +x install.sh
sudo ./install.sh
```

Das Script installiert:
- Python-Abhängigkeiten
- SANE Scanner-Treiber (inkl. HP-Support)
- Tesseract OCR (Deutsch + Englisch)
- Ollama mit TinyLlama Model
- Systemd Service für Auto-Start

### 3. Konfiguration anpassen

```bash
nano config.yaml
```

Wichtige Einstellungen:
- Scanner-Gerät
- Speicherpfade (/mnt/documents/)
- Ollama Model (tinyllama oder deepseek-coder:1.3b)

### 4. 2TB SSD mounten

```bash
sudo mkdir -p /mnt/documents
sudo mount /dev/sda1 /mnt/documents  # Anpassen je nach Device
sudo chown -R pi:pi /mnt/documents
```

Für automatisches Mounting in `/etc/fstab` eintragen.

### 5. System starten

```bash
sudo systemctl start document-manager
sudo systemctl status document-manager
```

### 6. Dashboard öffnen

Im Browser öffnen:
```
http://<raspberry-pi-ip>:5000
```

## 📁 Projektstruktur

```
OrganisationsAI/
├── app/
│   ├── scanner_handler.py      # Scanner-Integration
│   ├── document_processor.py   # OCR & Text-Extraktion
│   ├── categorizer.py           # AI-Kategorisierung
│   ├── storage_manager.py       # Dateistruktur-Verwaltung
│   ├── data_extractor.py        # CSV-Daten-Extraktion
│   ├── database.py              # SQLite Datenbank
│   ├── search_engine.py         # BM25-Suche
│   ├── server.py                # Flask Web Server
│   ├── ollama_client.py         # Chatbot-Integration
│   └── static/
│       ├── index.html           # Dashboard HTML
│       ├── css/style.css        # Styles
│       └── js/
│           ├── app.js           # Dashboard-Logik
│           └── chatbot.js       # Chatbot-Logik
├── main.py                      # Haupteinstiegspunkt
├── config.yaml                  # Konfiguration
├── requirements.txt             # Python-Abhängigkeiten
├── install.sh                   # Installations-Script
└── systemd/
    └── document-manager.service # Systemd Service
```

## 📊 Datenstruktur auf SSD

```
/mnt/documents/
├── storage/                     # Gespeicherte Dokumente
│   ├── 2024/
│   │   ├── Rechnungen/
│   │   │   ├── Strom/
│   │   │   └── Internet/
│   │   ├── Versicherungen/
│   │   │   ├── Haftpflicht/
│   │   │   └── KFZ/
│   │   └── Verträge/
│   └── 2025/
├── data/                        # CSV-Daten
│   ├── 2024/
│   │   ├── rechnungen_data.csv
│   │   ├── versicherungen_data.csv
│   │   └── verträge_data.csv
│   └── 2025/
├── structure.json               # Komplette Ordnerstruktur
└── database.db                  # SQLite Datenbank
```

## 🎯 Workflow

1. **Dokument scannen** → HP Scanner am Pi angeschlossen
2. **Automatische Verarbeitung**:
   - OCR-Text-Extraktion (Tesseract)
   - Datum & Beträge erkennen
   - AI-Kategorisierung (Sentence Transformers)
   - Intelligente Ordner-Erstellung
   - Strukturierte Daten in CSV
3. **Web-Dashboard**:
   - Statistiken & Charts
   - Versicherungs-Liste
   - Ausgaben-Analyse
   - Jahresvergleiche
4. **Chatbot-Assistent**:
   - Fragen zu Dokumenten
   - Ollama mit TinyLlama

## 🔧 Entwicklung & Testing

### Manuell starten (für Testing)

```bash
cd /home/pi/OrganisationsAI
source venv/bin/activate
python main.py
```

### Logs ansehen

```bash
tail -f /var/log/document-manager/app.log
```

### Scanner testen

```bash
scanimage -L                    # Scanner auflisten
scanimage --format=jpeg > test.jpg  # Test-Scan
```

### Ollama testen

```bash
ollama run tinyllama "Hallo, wie geht es dir?"
```

## 📡 API Endpoints

- `GET /api/stats/overview` - Übersichts-Statistiken
- `GET /api/stats/year/<year>` - Jahres-Statistiken
- `GET /api/documents` - Dokumenten-Liste
- `GET /api/documents/search?q=<query>` - Suche
- `GET /api/documents/<id>/download` - Download
- `GET /api/insurance/list` - Versicherungen
- `GET /api/expenses/analysis?year=<year>` - Ausgaben-Analyse
- `GET /api/expenses/compare?year1=<y1>&year2=<y2>` - Jahresvergleich
- `POST /api/chat` - Chatbot

## 🔒 Sicherheit

- **Kein externer Zugriff**: System läuft nur im lokalen Netzwerk
- **Keine Verschlüsselung**: Sensible Daten sind nur lokal gespeichert
- **Backup empfohlen**: Regelmäßige Backups der SSD erstellen

## 🛠️ Fehlerbehebung

### Scanner wird nicht erkannt

```bash
# SANE-Status prüfen
sudo systemctl status saned

# HP-Gerät scan
hp-setup

# Berechtigungen prüfen
groups pi  # Sollte "scanner" enthalten
```

### Ollama funktioniert nicht

```bash
# Service-Status
sudo systemctl status ollama

# Model neu laden
ollama pull tinyllama
```

### Wenig RAM (< 8GB)

Verwende leichteres Ollama Model oder deaktiviere Chatbot:
```yaml
# In config.yaml
ai:
  ollama:
    model: "none"  # Deaktiviert Chatbot
```

## 📝 Lizenz

MIT License

## 🤝 Support

Bei Fragen oder Problemen: Issue auf GitHub erstellen

---

**Made with ❤️ for Raspberry Pi 5**
