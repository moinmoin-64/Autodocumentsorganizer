# Schnellstart-Anleitung

Für schnelles Testen des Systems auf deinem Entwicklungsrechner (vor Raspberry Pi Deployment).

## 1. Dependencies installieren

```bash
# Virtual Environment erstellen
python -m venv venv

# Aktivieren (Windows)
venv\Scripts\activate

# Aktivieren (Linux/Mac)
source venv/bin/activate

# Packages installieren
pip install -r requirements.txt
```

## 2. System testen

```bash
# Quick Start Script (prüft alle Komponenten)
python quickstart.py
```

Dieses Script testet:
- ✓ Alle Python-Dependencies
- ✓ config.yaml Konfiguration
- ✓ Datenbank-Initialisierung
- ✓ AI-Categorizer (optional)

## 3. Server starten

```bash
# Hauptsystem starten (Linux/Mac)
python main.py

# Oder mit Development Script (Windows)
.\start_dev.bat --web

```

Dashboard öffnen: http://localhost:5000

## 4. Testen

### Unit Tests ausführen

```bash
# Einzelner Test
python -m pytest tests/test_document_processor.py -v

# Alle Tests
python -m pytest tests/ -v
```

### Funktionen testen

**Dokument hochladen:**
1. Dashboard öffnen
2. Upload-Bereich nutzen (Drag & Drop oder Klicken)
3. PDF/Bild hochladen
4. System verarbeitet automatisch

**Suche testen:**
1. Suchfeld oben rechts
2. Suchbegriff eingeben
3. Ergebnisse erscheinen

**Chatbot testen:**
1. Ollama muss laufen: `ollama serve`
2. Model laden: `ollama pull tinyllama`
3. Chatbot-Button unten rechts klicken
4. Fragen stellen

## 5. Troubleshooting

### Fehler: "No module named 'app'"

```bash
# Im Projekt-Root-Verzeichnis sein:
cd OrganisationsAI
python main.py
```

### Fehler: "Tesseract not found"

**Windows:**
1. https://github.com/UB-Mannheim/tesseract/wiki downloaden
2. Installieren nach C:\Program Files\Tesseract-OCR
3. PATH aktualisieren

**Linux:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-deu
```

### Fehler: "Ollama connection failed"

Chatbot funktioniert auch ohne Ollama (Fallback-Responses).

Für volle Funktionalität:
```bash
# Ollama installieren
curl -fsSL https://ollama.com/install.sh | sh

# Model laden
ollama pull tinyllama

# Server starten
ollama serve
```

### Port 5000 bereits belegt

In `config.yaml` ändern:
```yaml
web:
  port: 8000  # Anderen Port wählen
```

## 6. Entwicklung

### Code-Struktur

```
app/
├── scanner_handler.py      # Scanner-Integration
├── document_processor.py   # OCR & Analyse
├── categorizer.py           # KI-Kategorisierung
├── storage_manager.py       # Datei-Verwaltung
├── data_extractor.py        # CSV-Extraktion
├── database.py              # SQLite DB
├── search_engine.py         # BM25-Suche
├── server.py                # Flask Server
├── upload_handler.py        # File Upload
├── ollama_client.py         # Chatbot
└── static/                  # Frontend
    ├── index.html
    ├── css/style.css
    └── js/app.js, chatbot.js
```

### Neue Kategorie hinzufügen

In `config.yaml`:
```yaml
categories:
  main:
    - MeineNeueKategorie
  
  keywords:
    MeineNeueKategorie:
      - keyword1
      - keyword2
```

In `categorizer.py` neue Subkategorie-Logik hinzufügen (optional).

### API nutzen

Alle Endpoints unter `/api/*`:

```bash
# Statistiken
curl http://localhost:5000/api/stats/overview

# Suche
curl "http://localhost:5000/api/documents/search?q=rechnung"

# Versicherungen
curl http://localhost:5000/api/insurance/list
```

## 7. Produktiv-Deployment

Siehe [README.md](README.md) für vollständige Raspberry Pi Installation.

Kurzversion:
```bash
# Auf Raspberry Pi
git clone <repo> /home/pi/OrganisationsAI
cd /home/pi/OrganisationsAI
sudo ./install.sh

# System startet automatisch beim Booten
```

---

**Viel Erfolg! 🚀**

Bei Problemen: Issue auf GitHub erstellen oder Logs prüfen (`document_manager.log`)
