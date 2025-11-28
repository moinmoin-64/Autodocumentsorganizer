# API Dokumentation

REST API Endpoints für das Dokumentenverwaltungssystem.

**Base URL**: `http://localhost:5000/api`

---

## 📊 Statistiken

### GET /stats/overview
Übersicht über alle Statistiken

**Response:**
```json
{
  "total_documents": 142,
  "categories": {
    "Rechnungen": 45,
    "Versicherungen": 12,
    "Verträge": 8
  }
}
```

### GET /stats/year/{year}
Statistiken für ein spezifisches Jahr

**Parameter:**
- `year` (int): Jahr

**Response:**
```json
{
  "year": 2024,
  "total": 45,
  "categories": {
    "Rechnungen": 30,
    "Versicherungen": 10,
    "Verträge": 5
  }
}
```

---

## 📄 Dokumente

### GET /documents
Liste aller Dokumente

**Query-Parameter:**
- `category` (optional): Filter nach Kategorie
- `year` (optional): Filter nach Jahr
- `limit` (optional): Max. Anzahl (default: 100)

**Response:**
```json
{
  "count": 10,
  "documents": [
    {
      "id": 1,
      "filename": "2024-01-15_Stromrechnung.pdf",
      "category": "Rechnungen",
      "subcategory": "Strom",
      "date_document": "2024-01-15",
      "date_added": "2024-01-16T10:30:00",
      "summary": "Stromrechnung Januar 2024",
      "filepath": "/mnt/documents/storage/2024/Rechnungen/Strom/..."
    }
  ]
}
```

### GET /documents/search
Volltextsuche mit BM25

**Query-Parameter:**
- `q` (required): Suchbegriff
- `limit` (optional): Max. Ergebnisse (default: 20)

**Response:**
```json
{
  "query": "stromrechnung",
  "count": 5,
  "results": [
    {
      "id": 1,
      "filename": "2024-01-15_Stromrechnung.pdf",
      "search_score": 8.5,
      ...
    }
  ]
}
```

### GET /documents/{id}
Einzelnes Dokument abrufen

### GET /documents/{id}/download
Dokument herunterladen

**Response:** Binary file download

---

## 📤 Upload

### POST /upload
Datei hochladen

**Form-Data:**
- `file`: Datei (PDF, JPG, PNG)

**Response:**
```json
{
  "success": true,
  "filename": "document.pdf",
  "temp_path": "/tmp/scans/upload_...",
  "status": "pending_processing"
}
```

### POST /upload/process/{filepath}
Hochgeladene Datei verarbeiten

**Response:**
```json
{
  "success": true,
  "document_id": 123,
  "category": "Rechnungen",
  "subcategory": "Strom",
  "confidence": 0.95,
  "filepath": "/mnt/documents/storage/..."
}
```

---

## 🛡️ Versicherungen

### GET /insurance/list
Alle Versicherungen

**Response:**
```json
{
  "count": 12,
  "insurances": [
    {
      "versicherer": "XY Versicherung",
      "typ": "KFZ",
      "police_nummer": "12345",
      "beitrag": 450.00,
      "zahlungsintervall": "jährlich",
      "laufzeit_ende": "2025-12-31",
      "jahr": 2024
    }
  ]
}
```

---

## 💶 Ausgaben

### GET /expenses/analysis
Ausgaben-Analyse (für Tortendiagramm)

**Query-Parameter:**
- `year` (optional): Jahr (default: aktuelles Jahr)

**Response:**
```json
{
  "year": 2024,
  "categories": {
    "Strom": 540.50,
    "Internet": 360.00,
    "Versicherung": 1200.00
  },
  "total": 2100.50
}
```

### GET /expenses/compare
Jahresvergleich

**Query-Parameter:**
- `year1` (optional): Jahr 1 (default: letztes Jahr)
- `year2` (optional): Jahr 2 (default: aktuelles Jahr)

**Response:**
```json
{
  "year1": 2023,
  "year2": 2024,
  "comparison": {
    "Strom": {
      "year1": 500.00,
      "year2": 540.50,
      "change": 40.50
    }
  }
}
```

---

## 💬 Chatbot

### POST /chat
Nachricht an Chatbot senden

**Request Body:**
```json
{
  "message": "Wie viele Versicherungen habe ich?",
  "context": {}
}
```

**Response:**
```json
{
  "message": "Wie viele Versicherungen habe ich?",
  "response": "Sie haben 12 Versicherungen...",
  "timestamp": "2024-01-16T10:30:00"
}
```

---

## ❤️ Health

### GET /health
System-Status

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-16T10:30:00",
  "database": "connected"
}
```

---

## 🔧 Nutzung-Beispiele

### cURL

```bash
# Statistiken
curl http://localhost:5000/api/stats/overview

# Suche
curl "http://localhost:5000/api/documents/search?q=strom&limit=10"

# Upload
curl -F "file=@document.pdf" http://localhost:5000/api/upload

# Chatbot
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Zeige mir meine Ausgaben"}'
```

### Python

```python
import requests

# Statistiken abrufen
response = requests.get('http://localhost:5000/api/stats/overview')
data = response.json()
print(f"Dokumente: {data['total_documents']}")

# Dokument hochladen
with open('rechnung.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:5000/api/upload', files=files)
    print(response.json())

# Suche
params = {'q': 'stromrechnung', 'limit': 5}
response = requests.get('http://localhost:5000/api/documents/search', params=params)
results = response.json()['results']
```

### JavaScript (Frontend)

```javascript
// Statistiken laden
const stats = await fetch('/api/stats/overview').then(r => r.json());
console.log('Dokumente:', stats.total_documents);

// Upload mit FormData
const formData = new FormData();
formData.append('file', fileInput.files[0]);
const response = await fetch('/api/upload', {
  method: 'POST',
  body: formData
});
```

---

## 🔒 Fehler-Codes

| Code | Bedeutung |
|------|-----------|
| 200 | OK |
| 400 | Bad Request (fehlende Parameter) |
| 404 | Not Found (Ressource existiert nicht) |
| 500 | Internal Server Error |

**Fehler-Response:**
```json
{
  "error": "Fehlerbeschreibung"
}
```
