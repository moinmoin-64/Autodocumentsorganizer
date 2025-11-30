# 📁 Intelligentes Dokumentenverwaltungssystem

> KI-gestütztes System zur automatischen Verwaltung, Kategorisierung und Analyse von Dokumenten mit Web-Interface und REST API

[![Tests](https://img.shields.io/badge/tests-42%20passing-success)](https://github.com/moinmoin-64/Autodocumentsorganizer)
[![Coverage](https://img.shields.io/badge/coverage-70%25-green)](https://github.com/moinmoin-64/Autodocumentsorganizer)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

---

## 🌟 Features

### 🤖 KI-Features
- **Automatische Kategorisierung** mit AI (Ollama/DeepSeek)
- **OCR-Processing** (Tesseract/EasyOCR) für gescannte Dokumente
- **Intelligente Texterkennung** mit Konfidenz-Scores
- **Duplikat-Erkennung** basierend auf Content-Hashing
- **Auto-Tagging** für bessere Organisation

### 📊 Verwaltung & Analytics
- **Erweiterte Suche** mit Filtern (Datum, Kategorie, Betrag, Tags)
- **Budget-Tracking** mit monatlichen Übersichten
- **Ausgaben-Analysen** mit interaktiven Charts
- **Gespeicherte Suchen** für häufige Abfragen
- **Audit-Log** für alle Systemaktionen

### 🌐 Web-Interface
- **Premium Light Mode Design** mit modernem UI
- **Drag & Drop Upload** für intuitive Bedienung
- **Toast Notifications** für User-Feedback
- **Responsive Layout** (Desktop-optimiert)
- **Interactive Charts** (Chart.js)

### 📱 Mobile App (Expo)
- **iOS-Style Design**
- **Kamera & Galerie Import**
- **Automatische Synchronisation**

### 🔐 Sicherheit
- **CSRF Protection** mit Flask-WTF
- **Rate Limiting** zum Schutz vor Missbrauch
- **Password Hashing** (scrypt)
- **Session Management**
- **Audit Logging**

### 📧 Integration
- **Email-Receiver** (IMAP) für automatischen Import
- **Export-Funktionen** (Excel, PDF)
- **REST API** für externe Tools
- **Scanner-Integration** (SANE/scanimage)

---

## 🚀 Quick Start

### Voraussetzungen
```bash
# Python 3.12+
python --version

# Tesseract OCR
sudo apt-get install tesseract-ocr tesseract-ocr-deu

# Optional: Ollama für AI-Features
curl -fsSL https://ollama.com/install.sh | sh
```

### Installation

#### Standard Installation
```bash
# Repository klonen
git clone https://github.com/moinmoin-64/Autodocumentsorganizer.git
cd Autodocumentsorganizer

# Dependencies installieren
pip install -r requirements.txt

# Entwicklungs-Dependencies (für Tests)
pip install -r requirements-dev.txt

# Datenbank initialisieren
python -c "from app.db_config import init_db; init_db()"

# Server starten (Linux/Mac)
python app/server.py

# Server starten (Windows)
.\start_dev.bat
```

#### Raspberry Pi Installation
```bash
bash install.sh
```

### Konfiguration

`.env` Datei erstellen:
```env
SECRET_KEY=your-secret-key-here
DATABASE_PATH=data/database.db
OLLAMA_URL=http://localhost:11434
```

`config.yaml` anpassen:
```yaml
ai:
  ollama:
    enabled: true
    model: qwen2.5:7b-q4_K_M
    url: http://localhost:11434

auth:
  enabled: true
  users:
    admin: "scrypt:..."  # Generiert mit: python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('password'))"

email:
  enabled: false  # true für Email-Integration
  host: imap.example.com
  user: your-email@example.com
  password: your-password
```

---

## 📖 Nutzung

### Web-Interface
```bash
# Server starten
python app/server.py

# Browser öffnen
http://localhost:5000
```

### API-Beispiele

#### Dokument hochladen
```bash
curl -X POST http://localhost:5000/api/upload \
  -F "file=@document.pdf"
```

#### Dokumente suchen
```bash
curl http://localhost:5000/api/documents?query=rechnung&category=Bank
```

#### Erweiterte Suche
```bash
curl -X POST http://localhost:5000/api/search/advanced \
  -H "Content-Type: application/json" \
  -d '{
    "query": "versicherung",
    "start_date": "2024-01-01",
    "min_amount": 100,
    "tags": ["wichtig"]
  }'
```

---

## 🧪 Testing

### Tests ausführen
```bash
# Alle Tests
pytest

# Nur Unit Tests
python run_tests.py unit

# Mit Coverage
pytest --cov=app --cov-report=html

# E2E Tests (Browser)
pytest tests/e2e -v
```

### Test Coverage
```bash
# Coverage Report generieren
pytest --cov=app --cov-report=term-missing

# HTML Report
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

---

## 🏗️ Architektur

### Backend-Struktur
```
app/
├── models/              # SQLAlchemy ORM Models
│   └── __init__.py      # Document, Tag, AuditLog, etc.
├── blueprints/          # API Blueprints
│   ├── documents.py     # Dokumentenverwaltung
│   ├── search.py        # Suchfunktionen
│   ├── tags.py          # Tag-Management
│   ├── stats.py         # Statistiken
│   ├── export.py        # Export-Funktionen
│   ├── chat.py          # Chatbot
│   └── photos.py        # Foto-Management
├── db_config.py         # SQLAlchemy Configuration
├── database.py          # Database Layer (ORM)
├── categorizer.py       # AI Kategorisierung
├── document_processor.py # OCR & Verarbeitung
├── upload_handler.py    # Upload-Logik
├── email_receiver.py    # IMAP Integration
└── server.py            # Flask Application
```

### Frontend-Struktur
```
app/static/
├── css/
│   └── style.css        # Premium Design System
├── js/
│   ├── app.js           # Main Application
│   ├── notifications.js # Toast System
│   └── drag-drop-upload.js # Upload Handler
└── index.html           # Main UI
```

### Database Schema
```
Document (documents)
├── id: Integer (PK)
├── filename: String
├── filepath: String
├── category: String
├── subcategory: String
├── date_document: DateTime
├── summary: Text
├── full_text: Text
├── amount: Float
└── tags: Relationship → Tag (Many-to-Many)

Tag (tags)
├── id: Integer (PK)
├── name: String (Unique)
├── color: String
└── documents: Relationship → Document

AuditLog (audit_logs)
├── id: Integer (PK)
├── timestamp: DateTime
├── user_id: String
├── action: String
└── document: Relationship → Document
```

---

## 🔧 API-Dokumentation

### Endpoints

#### Documents API
- `GET /api/documents` - Liste aller Dokumente
- `GET /api/documents/<id>` - Einzelnes Dokument
- `POST /api/upload` - Dokument hochladen
- `DELETE /api/documents/<id>` - Dokument löschen
- `PUT /api/documents/<id>` - Dokument aktualisieren

#### Search API
- `GET /api/search?query=...` - Einfache Suche
- `POST /api/search/advanced` - Erweiterte Suche mit Filtern
- `GET /api/search/saved` - Gespeicherte Suchen
- `POST /api/search/save` - Suche speichern

#### Tags API
- `GET /api/tags` - Alle Tags
- `POST /api/tags` - Tag erstellen
- `POST /api/tags/document/<doc_id>` - Tag zu Dokument hinzufügen
- `DELETE /api/tags/document/<doc_id>/tag/<tag_id>` - Tag entfernen

#### Statistics API
- `GET /api/stats` - Gesamtstatistiken
- `GET /api/stats/expenses?year=2024` - Ausgaben nach Jahr
- `GET /api/stats/categories` - Verteilung nach Kategorien
- `GET /api/stats/trends?year=2024` - Monatliche Trends

#### Export API
- `POST /api/export/excel` - Excel Export
- `POST /api/export/pdf` - PDF Export

---

## 🎨 Design System

### Farb-Palette
```css
/* Primary Colors */
--primary: #2563EB;      /* Royal Blue */
--accent: #10B981;       /* Emerald Green */

/* Semantic Colors */
--success: #10B981;
--warning: #F59E0B;
--danger: #EF4444;
--info: #3B82F6;

/* Neutrals */
--gray-50: #F8FAFC;
--gray-900: #0F172A;
```

### Typografie
- **Font Family:** Inter, system-ui
- **Base Size:** 16px
- **Scale:** 1.25 (Major Third)

---

## 🤝 Mitwirken

### Development Setup
```bash
# Fork & Clone
git clone https://github.com/your-username/Autodocumentsorganizer.git

# Install Dev Dependencies
pip install -r requirements-dev.txt

# Run Tests
pytest

# Code Style
black app/
flake8 app/
```

### Commit-Konventionen
```
feat: Neues Feature
fix: Bugfix
docs: Dokumentation
test: Tests
refactor: Code-Refactoring
style: Formatierung
```

---

## 📝 License

MIT License - siehe [LICENSE](LICENSE)

---

## 🙏 Credits

### Dependencies
- **Flask** - Web Framework
- **SQLAlchemy** - ORM
- **Tesseract** - OCR Engine
- **Ollama** - Local AI Models
- **Chart.js** - Datenvisualisierung
- **pytest** - Testing Framework

### Entwickler
**moinmoin-64** - [GitHub](https://github.com/moinmoin-64)

---

## 📧 Kontakt

- **GitHub Issues:** [Issues](https://github.com/moinmoin-64/Autodocumentsorganizer/issues)
- **Email:** your-email@example.com

---

## 🗺️ Roadmap

### Version 2.0 (Geplant)
- [ ] Dark Mode Support
- [ ] Multi-User mit Rollen
- [ ] Cloud Storage Integration
- [x] Mobile App (Expo React Native)
- [ ] Advanced AI Features (GPT-4)
- [ ] Workflow Automation
- [ ] Email Templates

---

**Made with ❤️ and AI**
