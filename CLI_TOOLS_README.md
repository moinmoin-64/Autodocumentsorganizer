# 🚀 OrganisationsAI CLI Tools

Professionelle Kommandozeilen-Tools für Installation, Konfiguration und Verwaltung der OrganisationsAI Anwendung.

---

## 📋 Tools Übersicht

| Tool | Zweck | Komplexität |
|------|-------|------------|
| **quick_start_final.py** | Schnelle Basis-Installation in 2-5 Minuten | ⭐ Einfach |
| **install_wizard.py** | Vollständige Installation mit Konfiguration | ⭐⭐⭐ Mittel |
| **cli.py** | Tägliche Verwaltung & Entwicklung | ⭐⭐ Moderat |

---

## 1️⃣ Quick Start (Einfach)

### 💨 30-Sekunden Setup

```bash
# 1. Repository klonen
git clone https://github.com/yourname/organisationsai.git
cd organisationsai

# 2. Quick Start ausführen
python quick_start_final.py

# 3. Server starten
python main.py
```

### Was macht quick_start_final.py?

✅ Python 3.11+ Versionscheck  
✅ Virtuelle Umgebung erstellen  
✅ pip upgrade  
✅ Packages installieren  
✅ .env Datei generieren  
✅ Datenbank initialisieren  

**Zeit: ~2-5 Minuten**

### Output-Beispiel

```
════════════════════════════════════════════════════════════
  OrganisationsAI - Quick Start
════════════════════════════════════════════════════════════

[→] Checking Python version...
[✓] Python 3.13.9
[→] Creating virtual environment...
[✓] Virtual environment created
[→] Upgrading pip...
[✓] pip upgraded
[→] Installing packages...
[✓] Packages installed
[→] Creating .env file...
[✓] .env file created
[→] Initializing database...
[✓] Database initialized

════════════════════════════════════════════════════════════
✨ Setup Complete!
════════════════════════════════════════════════════════════

Next steps:

  1. Start development server:
     python main.py

  2. Open in browser:
     http://localhost:5000
```

---

## 2️⃣ Installation Wizard (Komplett)

### 📝 Interaktive Full-Installation

```bash
python install_wizard.py
```

### 11-Schritt Installation

```
1. Python Version Check          ← Validiert Python 3.11+
2. Dependency Check              ← pip, git, Node.js
3. Virtual Environment           ← .venv erstellen
4. Pip Upgrade                   ← Neueste Versionen
5. Package Installation          ← requirements.txt
6. Environment Configuration     ← Interaktive Setup
7. Config File Update            ← config.yaml aktualisieren
8. Database Initialization       ← Tabellen erstellen
9. Default User Creation         ← Admin-Benutzer
10. TypeScript Compilation       ← npm run compile
11. Unit Tests                   ← pytest ausführen
```

### Interaktive Fragen

```bash
# Datenbank
? Datenbank Typ [sqlite/postgresql]: postgresql
? PostgreSQL Host [localhost]: db.example.com
? PostgreSQL Port [5432]: 5432

# OCR
? OCR aktivieren [ja/nein]: ja
? Tesseract Sprache [deu/eng/fra]: deu

# AI/ML
? Ollama aktivieren [ja/nein]: ja
? AI Modell [llama2/mistral]: mistral

# Storage
? Storage Backend [local/s3]: s3
? S3 Bucket [my-bucket]: my-uploads

# Sicherheit
? CORS Origins [localhost:3000]: localhost:3000,example.com
```

### Auto-Generated Files

Nach Installation:

```
.env                      ← Alle Umgebungsvariablen
config.yaml              ← Anwendungskonfiguration
data/database.db         ← SQLite (oder PostgreSQL)
logs/                    ← Logging-Verzeichnis
backups/                 ← Datenbank-Backups
```

---

## 3️⃣ Management CLI (Täglich)

### 🎯 Kommando-Syntax

```bash
python cli.py <command> [subcommand] [options]
```

### 📚 Befehle nach Kategorie

#### 🔧 Development

```bash
# Server starten
python cli.py dev run

# Python Shell (mit App Context)
python cli.py dev shell
  >>> app
  >>> from app.models import Document

# Code Linting
python cli.py dev lint

# Code formatieren
python cli.py dev format
```

#### 🧪 Testing

```bash
# Unit Tests
python cli.py test unit

# Coverage Report
python cli.py test coverage

# End-to-End Tests
python cli.py test e2e
```

#### 🗄️ Database

```bash
# Datenbank initialisieren
python cli.py db init

# Migrationen ausführen
python cli.py db migrate

# Datenbank leeren (DEV!)
python cli.py db clean

# Backup erstellen
python cli.py db backup
```

#### 🏗️ Build

```bash
# TypeScript kompilieren
python cli.py build ts

# Docker Image bauen
python cli.py build docker --version 1.0.0
```

#### 🚀 Deployment

```bash
# Docker Deploy
python cli.py deploy docker --port 8000

# Kubernetes Deploy
python cli.py deploy k8s --namespace production
```

#### ℹ️ Info

```bash
# System Information
python cli.py info

# Erweiterte Hilfe
python cli.py help
```

---

## 🔄 Typische Workflows

### 📅 Tägliche Entwicklung

```bash
# Morgens: Environment starten
python cli.py dev run              # Server auf port 5000

# Tagsüber: Tests während Entwicklung
python cli.py test unit            # Schnelle Tests

# Code vor Commit
python cli.py dev format           # Black formatting
python cli.py dev lint             # Pylint checks

# Abends: Backup & Status
python cli.py db backup            # Datenbank sichern
python cli.py info                 # System Status
```

### 🚀 Release-Prozess

```bash
# 1. Alle Tests erfolgreich
python cli.py test coverage

# 2. Datenbank sichern
python cli.py db backup

# 3. Migrations
python cli.py db migrate

# 4. Docker Image
python cli.py build docker --version 2.0.0

# 5. Deployment
python cli.py deploy k8s --namespace production
```

### 🐛 Debugging-Session

```bash
# Python Shell öffnen
python cli.py dev shell

# Interaktiv arbeiten
>>> db = DocumentDB()
>>> docs = db.get_documents(status='pending')
>>> for doc in docs:
...     print(doc.title)
...     db.update_document(doc.id, status='processed')
```

---

## ⚙️ Umgebungsvariablen

### Auto-Generierte .env

```env
# Sicherheit
SECRET_KEY=aXxsD8jK2mN9pQrT5uVwXyZaBcDeFgHiJkLm...
SESSION_TIMEOUT=3600
DEBUG=False

# Datenbank
DATABASE_URL=postgresql://user:pass@host/db
SQLALCHEMY_ECHO=False

# Features
ENABLE_SCANNER=True
ENABLE_EMAIL=False
ENABLE_CLUSTERING=True

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# OCR
OCR_ENABLED=True
OCR_LANGUAGE=deu

# AI/ML
AI_ENABLED=True
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral
```

---

## 🎨 Farbige Output

Alle CLI-Tools verwenden ANSI-Farben für bessere Lesbarkeit:

```
[✓] GREEN     → Erfolg/OK
[✗] RED       → Fehler
[→] BLUE      → Info/Action
[!] YELLOW    → Warnung
[...]         → Status
```

---

## 🛠️ Fehlerbehandlung

### Python nicht gefunden

```bash
# Überprüfen
python --version

# Installieren
# Windows: python.org
# Linux: apt install python3.12
# macOS: brew install python@3.12
```

### pip nicht verfügbar

```bash
python -m ensurepip --upgrade
```

### Virtual Environment Issue

```bash
# Neu erstellen
rm -rf .venv  # Linux/macOS
rmdir /s .venv  # Windows

python -m venv .venv
```

### Datenbank gesperrt

```bash
python cli.py db backup
python cli.py db clean
python cli.py db init
```

---

## 📊 Performance-Tipps

### Schnellere Tests

```bash
# Nur schnelle Tests
python cli.py test unit -k "not slow"

# Parallel Testing
pytest tests/ -n auto  # mit pytest-xdist
```

### Optimierte Dev Session

```bash
# Terminal 1: Server
python cli.py dev run

# Terminal 2: Watch Tests
pytest tests/ --ff --lf -w  # last failed, watch
```

---

## 📖 Dokumentation

| Datei | Inhalt |
|-------|--------|
| **README.md** | Projekt-Übersicht |
| **README_COMPLETE.md** | Umfassende Dokumentation |
| **CLI_GUIDE_DE.md** | Detaillierte CLI-Anleitung |
| **INSTALLATION_GUIDE_DE.md** | Installation & Konfiguration |
| **API.md** | REST API Referenz |

---

## 🚀 Schnellstart-Kommandos

```bash
# Kopiere diese Aliases
alias ai='python cli.py'
alias airun='python cli.py dev run'
alias aitest='python cli.py test unit'
alias aibuild='python cli.py build docker'

# Nutze sie dann
ai dev run
ai test unit
ai db backup
ai build docker --version 1.0
```

---

## 📞 Support

**Probleme?**

1. Überprüfe [CLI_GUIDE_DE.md](CLI_GUIDE_DE.md)
2. Versuche `python cli.py help`
3. Überprüfe Logs in `logs/` Verzeichnis
4. Erstelle ein GitHub Issue

---

## 📝 Version Information

- **CLI Version**: 1.0
- **Python**: 3.11+
- **Last Updated**: Januar 2025

---

## 🎯 Quick Links

- 🔧 [CLI Guide](CLI_GUIDE_DE.md)
- 📦 [Installation Guide](INSTALLATION_GUIDE_DE.md)
- 📚 [Full Documentation](README_COMPLETE.md)
- 🔌 [API Reference](API.md)

---

*Viel Erfolg mit OrganisationsAI! 🎉*
