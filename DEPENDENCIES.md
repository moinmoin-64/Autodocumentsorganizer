# OrganisationsAI Installation - Dependency Checklist

## Aktualisiertes Dependency-Management

**Wichtig:** Alle Python-Dependencies werden zentral über `requirements.txt` installiert!

### Produktions-Dependencies (requirements.txt):
```bash
# Core Web Framework
Flask==3.0.0
Flask-Cors==4.0.0
Flask-Login==0.6.3

# Security
Flask-WTF==1.2.1
Flask-Limiter==3.5.0
Werkzeug==3.0.1
python-dotenv==1.0.0

# Database & ORM
SQLAlchemy==2.0.23          # ← NEU in Phase 5
alembic==1.13.1             # ← NEU in Phase 5

# Document Processing
pytesseract==0.3.10
pdf2image==1.17.0
opencv-python==4.8.1.78

# AI/ML
sentence-transformers>=3.0.0
numpy==1.26.0
scikit-learn==1.3.2

# ... (siehe requirements.txt für vollständige Liste)
```

### Entwicklungs-Dependencies (requirements-dev.txt):
```bash
# Testing
pytest==7.4.3               # ← NEU in Phase 5
pytest-cov==4.1.0
pytest-mock==3.12.0

# Code Quality
black==23.12.1
flake8==6.1.0
mypy==1.7.1

# ... (siehe requirements-dev.txt für vollständige Liste)
```

## Installation-Scripts

### 1. install.sh (Raspberry Pi - Root Installation)
```bash
# Installiert:
# - System-Pakete (tesseract, sane, etc.)
# - Python venv
# - requirements.txt (automatisch)
# - requirements-dev.txt (optional)
# - Systemd Service
# - Ollama Model

sudo ./install.sh
```

### 2. raspberry_pi_install.sh (User Installation)
```bash
# Installiert:
# - Python venv
# - requirements.txt
# - .env Setup
# - Log-Verzeichnisse
# - (optional) requirements-dev.txt

bash raspberry_pi_install.sh
```

### 3. Manuelle Installation (Entwicklung)
```bash
# 1. Virtual Environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate     # Windows

# 2. Production Dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Development Dependencies (optional)
pip install -r requirements-dev.txt

# 4. Verify Installation
pip list | grep -E 'Flask|SQLAlchemy|pytest'
```

## Dependency-Gruppen

### Kern-System:
- Flask + Extensions (Web Framework)
- SQLAlchemy + Alembic (Database ORM)
- Werkzeug (Security)
- python-dotenv (Environment)

### Document Processing:
- pytesseract (OCR)
- pdf2image (PDF Conversion)
- opencv-python (Image Processing)
- PyPDF2, pdfplumber (PDF Parsing)

### AI/ML:
- sentence-transformers (Semantic Search)
- numpy, scikit-learn (ML Utilities)

### Testing (Dev only):
- pytest + plugins (Testing Framework)
- black, flake8, mypy (Code Quality)

## Neue Dependencies in Phase 5

### Production:
```txt
SQLAlchemy==2.0.23       # ORM für type-safe DB-Zugriff
alembic==1.13.1          # Database Migrations
```

### Development:
```txt
pytest==7.4.3            # Testing Framework
pytest-cov==4.1.0        # Coverage Reporting
pytest-mock==3.12.0      # Mocking
pytest-asyncio==0.21.1   # Async Testing
pytest-xdist==3.5.0      # Parallel Testing
black==23.12.1           # Code Formatting
flake8==6.1.0            # Linting
mypy==1.7.1              # Type Checking
pylint==3.0.3            # Advanced Linting
```

## Verify Installation

```bash
# Check SQLAlchemy
python -c "import sqlalchemy; print(f'SQLAlchemy {sqlalchemy.__version__}')"

# Check pytest
python -c "import pytest; print(f'pytest {pytest.__version__}')"

# Check all core dependencies
python -c "
import flask
import sqlalchemy
import pytest
import werkzeug
print(f'✓ Flask {flask.__version__}')
print(f'✓ SQLAlchemy {sqlalchemy.__version__}')
print(f'✓ pytest {pytest.__version__}')
print(f'✓ Werkzeug {werkzeug.__version__}')
"
```

## Troubleshooting

### Dependencies fehlen nach Install?
```bash
# Re-run pip install
source venv/bin/activate
pip install -r requirements.txt --force-reinstall

# Verify
pip list
```

### SQLAlchemy nicht gefunden?
```bash
# Check ob in requirements.txt
grep SQLAlchemy requirements.txt

# Manuell installieren
pip install SQLAlchemy==2.0.23 alembic==1.13.1
```

### pytest nicht verfügbar?
```bash
# Install dev dependencies
pip install -r requirements-dev.txt
```

## Best Practices

1. **Immer requirements.txt nutzen** - Nicht manuell installieren
2. **venv aktivieren** - Vor jeder Installation
3. **requirements.txt aktuell halten** - Bei neuen Dependencies
4. **Pin versions** - Für reproduzierbare Builds
5. **requirements-dev.txt trennen** - Production vs Development

---

**Wichtig:** Alle Install-Scripts installieren automatisch `requirements.txt`!
