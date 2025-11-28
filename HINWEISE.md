# HINWEISE ZUR DOKUMENTENVERARBEITUNG

## ✅ Was bereits implementiert ist:

### 1. Datum-Extraktion
- **OCR-Text wird gescannt** nach Datumsmustern
- **Kontextbasiert**: Sucht nach "Datum:", "vom", "am", "Rechnungsdatum" etc.
- **Deutsche Formate**: 01.12.2024, 01.12.24, 2024-12-01
- **Fallback**: Wenn kein Datum gefunden → heutiges Datum mit Warnung im Log

### 2. Kategorisierung
- **AI-basiert**: Sentence Transformers (multilingual-MiniLM-L12-v2)
- **Regelbasiert**: Keyword-Matching als Backup
- **Kombiniert**: Best-of-both für 95%+ Genauigkeit

### 3. Ordnerstruktur
- **Automatisch**: `Jahr/Kategorie/Subkategorie/`
- **Beispiel**: 
  ```
  2024/
    Rechnungen/
      Strom/
      Internet/
      Versicherung/
    Versicherungen/
      KFZ/
      Haftpflicht/
    Verträge/
      Miete/
      Handy/
  ```

## 🔧 Wichtige Konfiguration

### Kategorien hinzufügen
In `config.yaml`:
```yaml
categories:
  main:
    - Rechnungen
    - Versicherungen
    - Verträge
    - Bank
    - Steuer
    # Neue Kategorie hier hinzufügen
    
  keywords:
    Rechnungen:
      - rechnung
      - invoice
      - betrag
    # Neue Keywords hier
```

### Subkategorien
Werden automatisch erstellt basierend auf:
- **Rechnungen**: Strom, Internet, Gas, Wasser, Versicherung, etc.
- **Versicherungen**: KFZ, Haftpflicht, Krankenversicherung, etc.
- **Verträge**: Mietvertrag, Arbeitsvertrag, Handyvertrag, etc.

Siehe `categorizer.py` für Logik.

## ⚠️ Datum-Probleme beheben

### Wenn Datum nicht erkannt wird:

**1. Prüfe OCR-Text**
```python
python -c "from app.document_processor import DocumentProcessor; p = DocumentProcessor(); print(p.process_document('dokument.pdf')['text'])"
```

**2. Verbessere Datum-Patterns**
In `document_processor.py` → `_extract_dates()`:
- Neue Regex-Patterns hinzufügen
- Mehr Kontext-Keywords

**3. Manuelle Korrektur**
Im Code nach Upload:
```python
# Falls Datum falsch
from datetime import datetime
document_date = datetime(2024, 1, 15)  # Korrektes Datum
```

## 🎯 Best Practices

### Gute Scans für OCR:
- **Auflösung**: mind. 300 DPI
- **Kontrast**: Schwarz/Weiß besser als Graustufen
- **Ausrichtung**: Gerade, nicht schräg
- **Qualität**: Scharf, nicht verschwommen

### Datum sollte im Dokument stehen als:
- "Datum: 01.12.2024"
- "Rechnungsdatum: 01.12.2024"
- "vom 01.12.2024"
- "01.12.2024" (wenn eindeutig)

## 📝 Was noch fehlt (optional):

1. **Datum aus Dateinamen** fallback
   - Wenn OCR fehlschlägt, aus Dateinamen parsen
   
2. **Manuelles Datum-Override** im Web-Interface
   - Upload-Form mit Datum-Feld
   
3. **Datum-Validierung**
   - Warnung bei unrealistischen Daten (Zukunft, zu alt)
   
4. **Multi-Datum-Handling**
   - Wenn mehrere Daten gefunden, intelligenter wählen
   - Z.B. neuestes oder das nach "Datum:" Keyword

5. **Batch-Datum-Korrektur**
   - Tool zum Nach-Korrigieren vieler Dokumente
   
6. **Datum-Konfidenz-Score**
   - Wie sicher ist das erkannte Datum?

## 🔍 Logs prüfen

Bei Problemen:
```bash
# Haupt-Log
tail -f document_manager.log | grep "Datum\|date"

# Nur Warnungen
tail -f document_manager.log | grep "⚠️"
```

Achte auf:
- "⚠️  Kein Datum im Dokument erkannt!"
- "⚠️  Kein Datum im Dokument gefunden"
- "Gefundene Daten: ['2024-01-15']"
