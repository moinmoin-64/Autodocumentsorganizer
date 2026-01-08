# OrganisationsAI - CLI Tools Anleitung

## Übersicht

Das Projekt bietet jetzt zwei professionelle CLI-Tools für einfache Installation und Verwaltung:

1. **install_wizard.py** - Automatisierte Installation und Konfiguration
2. **cli.py** - Tägliche Verwaltung und Entwicklung

---

## 1. Installation mit install_wizard.py

### Start
```bash
python install_wizard.py
```

### Funktionen

#### 1️⃣ Versionscheck
- Validiert Python 3.11+
- Verhindert Inkompatibilität

#### 2️⃣ Abhängigkeitscheck
- Prüft: pip, git, Node.js
- Installiert fehlende Tools

#### 3️⃣ Virtuelle Umgebung
- Erstellt .venv automatisch
- Pip-Update (setuptools, wheel)

#### 4️⃣ Python Packages
- Liest requirements.txt
- Installiert automatisch

#### 5️⃣ Umgebungskonfiguration
Interaktive Einstellung für:

**OCR (Optical Character Recognition)**
```
→ Tesseract installiert? (ja/nein)
→ Sprache wählen: [deu, eng, fra, ...]
```

**AI/ML**
```
→ Ollama installiert? (ja/nein)
→ Modell wählen: [llama2, neural-chat, mistral, ...]
```

**Datenbank**
```
→ Datenbanken-Typ: [SQLite, PostgreSQL]
→ SQLite: data/database.db
→ PostgreSQL: host, port, user, password
```

**Speicher**
```
→ Speicher-Backend: [Local, S3]
→ Local: data/uploads/
→ S3: bucket, region, access_key
```

**Sicherheit**
```
→ CORS Origins konfigurieren
→ Session Timeout setzen
→ Logging Level wählen
```

#### 6️⃣ Dateiaktualisierung
```yaml
# config.yaml wird automatisch angepasst
ocr:
  enabled: true
  language: deu
  
ai:
  model: llama2
  
database:
  type: postgresql
  host: localhost
```

#### 7️⃣ Datenbank-Initialisierung
```
→ Erstellt alle Tabellen
→ Initialisiert Indizes
→ Setzt Constraints
```

#### 8️⃣ Standard-Admin-Benutzer
```
Username: admin
Password: Automatisch generiert
Email: admin@organisationsai.local
Role: administrator
```

#### 9️⃣ TypeScript Compilation
```bash
npm run compile
```

#### 🔟 Test-Suite
```bash
pytest tests/ -v
```

### Beispiel: Komplette Installation

```bash
$ python install_wizard.py

═══════════════════════════════════════════════════════════
  OrganisationsAI - Installation Wizard
═══════════════════════════════════════════════════════════

[INFO] Schritt 1: Python Version
  ✓ Python 3.13.9 erforderlich
  ✓ Gefunden: Python 3.13.9

[INFO] Schritt 2: Abhängigkeiten
  ✓ pip: /usr/bin/pip
  ✓ git: /usr/bin/git
  ✓ node: /usr/bin/node

[INFO] Schritt 3: Virtuelle Umgebung
  → Virtual Environment wird erstellt...
  ✓ .venv erstellt

[INFO] Schritt 4: Pip Upgrade
  → pip wird aktualisiert...
  ✓ pip auf neuester Version

[INFO] Schritt 5: Packages installieren
  → Installing from requirements.txt...
  ✓ 47 Packages installiert

[INFO] Schritt 6: Konfiguration
  ? Datenbank Typ (sqlite/postgresql) [sqlite]: postgresql
  ? PostgreSQL Host [localhost]: db.example.com
  ? PostgreSQL Port [5432]: 5432
  ? PostgreSQL User [organisationsai]: admin
  ? PostgreSQL Passwort: ••••••••
  ? OCR Sprache (deu/eng/fra) [deu]: deu
  ? AI Modell (llama2/mistral) [llama2]: mistral
  ? Storage Backend (local/s3) [local]: s3
  ? S3 Bucket [organisationsai-uploads]: my-bucket

[INFO] Schritt 7: .env Datei
  → .env wird generiert...
  ✓ 15 Variablen gesetzt

[INFO] Schritt 8: Datenbank Init
  → Datenbank wird initialisiert...
  ✓ 12 Tabellen erstellt

[INFO] Schritt 9: Admin User
  → Admin benutzer wird erstellt...
  ✓ admin@organisationsai.local
  ? Neues Passwort setzen? (y/n) [y]: y

[INFO] Schritt 10: TypeScript Build
  → TypeScript wird kompiliert...
  ✓ 8 Dateien kompiliert

[INFO] Schritt 11: Tests
  → Pytest wird ausgeführt...
  ✓ 51/51 Tests erfolgreich

═══════════════════════════════════════════════════════════
 Installation abgeschlossen! 🎉
═══════════════════════════════════════════════════════════

Nächste Schritte:
  1. python main.py          # Server starten
  2. http://localhost:5000   # Browser öffnen
  3. python cli.py help      # CLI Anleitung
```

---

## 2. Management mit cli.py

### Basis-Syntax
```bash
python cli.py <command> [subcommand] [options]
```

### 📝 Development Befehle

#### Server starten
```bash
python cli.py dev run
# Startet Flask auf http://localhost:5000
```

#### Python Shell mit App-Context
```bash
python cli.py dev shell
# >>> app  # Flask app disponibel
# >>> from app.models import Document
```

#### Code-Linting
```bash
python cli.py dev lint
# Pylint über app/ Verzeichnis
```

#### Code formatieren
```bash
python cli.py dev format
# Black formatting
```

### 🧪 Test Befehle

#### Unit Tests
```bash
python cli.py test unit
# Alle tests/ ausführen
# Output: Passed/Failed/Skipped
```

#### Coverage Report
```bash
python cli.py test coverage
# Coverage Report generieren
# Output: htmlcov/index.html
```

#### End-to-End Tests
```bash
python cli.py test e2e
# Nur E2E Tests
```

### 🗄️ Datenbank Befehle

#### Datenbank initialisieren
```bash
python cli.py db init
# CREATE TABLE statements ausführen
```

#### Datenbank migrieren
```bash
python cli.py db migrate
# Alembic migrations ausführen
```

#### Datenbank leeren (DEV ONLY!)
```bash
python cli.py db clean
# Alle Tabellen löschen + neu erstellen
# Fragt nach Bestätigung!
```

#### Datenbank sichern
```bash
python cli.py db backup
# Backup: backups/database_20240115_143022.db
```

### 🔨 Build Befehle

#### TypeScript kompilieren
```bash
python cli.py build ts
# app/static/js/dist/ wird aktualisiert
```

#### Docker Image bauen
```bash
python cli.py build docker --version 1.0.0
# Erstellt: organisationsai:1.0.0
```

### 🚀 Deployment Befehle

#### Docker Deploy
```bash
python cli.py deploy docker --port 8000
# Startet Container auf Port 8000
```

#### Kubernetes Deploy
```bash
python cli.py deploy k8s --namespace production
# kubectl apply -f k8s/ in production namespace
```

### ℹ️ System Information

#### System Info anzeigen
```bash
python cli.py info
# Python Version
# Platform
# Project Root
# Virtual Env Path
# Config Paths
```

#### Erweiterte Hilfe
```bash
python cli.py help
# Alle Befehle mit Beschreibungen
```

---

## 3. Workflow Beispiele

### 🎯 Typischer Development-Tag

```bash
# 1. Server starten
python cli.py dev run

# 2. (In anderem Terminal) Tests ausführen
python cli.py test unit

# 3. Code formatieren
python cli.py dev format

# 4. Linting vor Commit
python cli.py dev lint

# 5. Datenbank sichern
python cli.py db backup

# 6. Neue Version deployen
python cli.py build docker --version 1.2.3
python cli.py deploy docker
```

### 📊 Release-Prozess

```bash
# 1. Tests sicherstellen
python cli.py test coverage

# 2. Datenbank backup
python cli.py db backup

# 3. Datenbank migrations
python cli.py db migrate

# 4. Docker Image bauen
python cli.py build docker --version 2.0.0

# 5. Production deployen
python cli.py deploy k8s --namespace production
```

### 🔧 Debugging-Session

```bash
# 1. Python Shell öffnen
python cli.py dev shell

# >>> from app.db_operations import DocumentDB
# >>> db = DocumentDB()
# >>> docs = db.get_documents(limit=10)
# >>> for doc in docs:
# ...     print(doc.title, doc.status)
```

---

## 4. Environment-Variablen

### Automatisch generiert durch install_wizard.py

```env
# Sicherheit
SECRET_KEY=aXxsD8jK2mN9pQrT5uVwXyZaBcDeFgHiJkLmNoPqRsTuVwXyZ
SESSION_TIMEOUT=3600

# Datenbank
DATABASE_URL=postgresql://user:pass@host:5432/organisationsai
SQLALCHEMY_ECHO=false

# OCR
OCR_ENABLED=true
OCR_LANGUAGE=deu
TESSERACT_PATH=/usr/bin/tesseract

# AI/ML
AI_MODEL=mistral
OLLAMA_URL=http://localhost:11434

# Storage
STORAGE_BACKEND=s3
S3_BUCKET=organisationsai-uploads
AWS_REGION=eu-west-1

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5000

# Features
ENABLE_SCANNER=true
ENABLE_EMAIL=true
ENABLE_OCLUSTERING=true
```

---

## 5. Fehlerbehebung

### Fehler: "Python 3.11+ erforderlich"
```bash
# Python-Version checken
python --version

# Neue Python Version installieren
# Windows: python.org/downloads
# Linux: apt install python3.12
# macOS: brew install python@3.12
```

### Fehler: "pip nicht gefunden"
```bash
# Windows
python -m ensurepip

# Linux/macOS
python3 -m ensurepip --upgrade
```

### Fehler: "Virtuelle Umgebung wird nicht aktiviert"
```bash
# Windows
.venv\Scripts\activate.bat

# Linux/macOS
source .venv/bin/activate
```

### Fehler: "Datenbank locked"
```bash
# SQLite Datei entsperren
python cli.py db backup
python cli.py db clean
python cli.py db init
```

---

## 6. Weitere Ressourcen

- **README.md** - Projekt Übersicht
- **README_COMPLETE.md** - Umfassende Dokumentation
- **INSTALLATION_GUIDE_DE.md** - Detaillierte Installation
- **API.md** - REST API Dokumentation
- **config.yaml** - Konfigurationsoptionen

---

## 7. Tipps & Tricks

### 💡 Schnelle Befehle

```bash
# Alias erstellen
alias ai='python cli.py'
alias aibuild='python cli.py build'
alias aitest='python cli.py test unit'

# Dann verwenden:
ai dev run
ai test coverage
ai db backup
```

### 🎨 Farbige Ausgabe

Alle CLI Tools unterstützen ANSI-Farben:
- 🟢 GREEN: Erfolg (✓)
- 🟡 YELLOW: Warnung (!)
- 🔴 RED: Fehler (✗)
- 🔵 BLUE: Info (→)

### 📦 Offline-Modus

```bash
# install_wizard.py funktioniert offline wenn:
# - .venv bereits existiert
# - Packages bereits installiert
# - Internet nur für GitHub-Repos nötig
```

### ⚡ Performance-Tipps

```bash
# Schnellere Tests
python cli.py test unit -k "not slow"

# Nur neue Test-Dateien
python cli.py test unit --lf  # last failed

# Parallel Testing
pytest tests/ -n auto  # mit pytest-xdist
```

---

## 8. Kontakt & Support

- **GitHub Issues**: Repository Issues für Bugs
- **Email**: support@organisationsai.local
- **Docs**: [ReadTheDocs Link]
- **Chat**: Discord/Slack Community

---

*Zuletzt aktualisiert: Januar 2025*
