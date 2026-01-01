# Phase 5 API Reference - Error Tracking & Health Monitoring

## Basis-URLs
```
Error Tracking:  /api/errors
Health Checks:   /api/health
```

---

## ERROR TRACKING ENDPOINTS

### POST /api/errors
**Beschreibung:** Fehler-Batch vom Frontend erfassen

**Request:**
```json
{
  "errors": [
    {
      "type": "error|warning|info",
      "message": "Error message text",
      "filename": "app.js",
      "lineno": 123,
      "colno": 45,
      "stack": "Error: ...\n  at ...",
      "url": "https://example.com/page",
      "userAgent": "Mozilla/5.0 ...",
      "context": {
        "environment": "production",
        "release": "1.0.0",
        "userId": "user-123",
        "offline": false
      }
    }
  ]
}
```

**Response (201):**
```json
{
  "success": true,
  "inserted": 5,
  "total": 5
}
```

**Curl Example:**
```bash
curl -X POST http://localhost:5000/api/errors \
  -H "Content-Type: application/json" \
  -d '{
    "errors": [{
      "type": "error",
      "message": "Test error",
      "context": {
        "userId": "user-123",
        "environment": "production"
      }
    }]
  }'
```

---

### GET /api/errors/dashboard
**Beschreibung:** Error-Statistik Dashboard für zeitraum

**Query Parameters:**
```
days=7  # Last N days (default: 7)
```

**Response (200):**
```json
{
  "period": "7 days",
  "total": 247,
  "byType": {
    "error": 180,
    "warning": 45,
    "info": 22
  },
  "topErrors": [
    {
      "message": "Cannot read property 'value' of undefined",
      "count": 42,
      "lastSeen": "2026-01-15T14:32:00Z"
    }
  ],
  "byEnvironment": {
    "production": 200,
    "development": 47
  },
  "offline": 23,
  "online": 224,
  "byHour": [
    {
      "hour": "2026-01-15 14:00:00",
      "count": 18
    }
  ]
}
```

**Curl Example:**
```bash
curl http://localhost:5000/api/errors/dashboard?days=7
```

---

### GET /api/errors/groups
**Beschreibung:** Fehlergruppen abrufen (Fehler gruppiert nach Nachricht)

**Query Parameters:**
```
resolved=false  # Filter by resolution status (default: false)
limit=20        # Items per page (default: 20)
offset=0        # Pagination offset (default: 0)
```

**Response (200):**
```json
{
  "total": 15,
  "limit": 20,
  "offset": 0,
  "groups": [
    {
      "id": 1,
      "message": "Cannot read property 'value' of undefined",
      "count": 42,
      "lastSeen": "2026-01-15T14:32:00Z",
      "firstSeen": "2026-01-10T10:15:00Z",
      "resolved": false
    }
  ]
}
```

**Curl Example:**
```bash
curl "http://localhost:5000/api/errors/groups?resolved=false&limit=10"
```

---

### GET /api/errors/groups/{id}
**Beschreibung:** Details einer Fehlergruppe + letzte 50 Fehler

**Response (200):**
```json
{
  "group": {
    "id": 1,
    "message": "Cannot read property 'value' of undefined",
    "count": 42,
    "lastSeen": "2026-01-15T14:32:00Z",
    "firstSeen": "2026-01-10T10:15:00Z",
    "resolved": false
  },
  "errors": [
    {
      "id": 245,
      "type": "error",
      "message": "Cannot read property 'value' of undefined",
      "filename": "app.js",
      "lineno": 156,
      "colno": 10,
      "stack": "Error: ...",
      "url": "https://example.com/documents",
      "userAgent": "Mozilla/5.0",
      "userId": "user-123",
      "environment": "production",
      "release": "1.0.0",
      "offline": false,
      "timestamp": "2026-01-15T14:32:00Z",
      "resolved": false
    }
  ]
}
```

**Curl Example:**
```bash
curl http://localhost:5000/api/errors/groups/1
```

---

### PUT /api/errors/groups/{id}/resolve
**Beschreibung:** Fehlergruppe als gelöst markieren

**Request:**
```json
{}
```

**Response (200):**
```json
{
  "success": true,
  "group": {
    "id": 1,
    "message": "Cannot read property 'value' of undefined",
    "count": 42,
    "lastSeen": "2026-01-15T14:32:00Z",
    "firstSeen": "2026-01-10T10:15:00Z",
    "resolved": true
  }
}
```

**Curl Example:**
```bash
curl -X PUT http://localhost:5000/api/errors/groups/1/resolve \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

### POST /api/errors/cleanup
**Beschreibung:** Alte Fehler-Logs löschen (älter als N Tage)

**Query Parameters:**
```
days=30  # Keep logs newer than N days (default: 30)
```

**Response (200):**
```json
{
  "success": true,
  "deleted": 1547
}
```

**Curl Example:**
```bash
curl -X POST http://localhost:5000/api/errors/cleanup?days=30
```

---

## HEALTH CHECK ENDPOINTS

### GET /api/health
**Beschreibung:** Vollständiger System Health Report

**Response (200 | 503):**
```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "2026-01-15T14:32:00Z",
  "uptime": "N/A",
  "services": {
    "database": {
      "status": "healthy|unhealthy",
      "type": "PostgreSQL/SQLite",
      "responseTime": 45
    },
    "cache": {
      "status": "healthy|degraded|unhealthy",
      "type": "Redis",
      "responseTime": 15
    }
  },
  "resources": {
    "cpu": {
      "percent": 25,
      "cores": 8
    },
    "memory": {
      "percent": 42,
      "used": 5120,
      "total": 16384
    },
    "disk": {
      "percent": 65,
      "used": 300,
      "total": 500
    }
  },
  "process": {
    "pid": 12345,
    "memory": {
      "rss": 256,
      "vms": 512
    },
    "cpu_percent": 1.5,
    "num_threads": 42,
    "status": "running"
  }
}
```

**Curl Example:**
```bash
curl http://localhost:5000/api/health
```

---

### GET /api/health/status
**Beschreibung:** Schneller Status Check (minimal JSON)

**Response (200 | 503):**
```json
{
  "healthy": true,
  "timestamp": "2026-01-15T14:32:00Z"
}
```

**Curl Example:**
```bash
curl http://localhost:5000/api/health/status
```

---

### GET /api/health/database
**Beschreibung:** Nur Datenbank-Status

**Response (200 | 500):**
```json
{
  "status": "healthy|unhealthy",
  "type": "PostgreSQL/SQLite",
  "responseTime": 45
}
```

**Curl Example:**
```bash
curl http://localhost:5000/api/health/database
```

---

### GET /api/health/cache
**Beschreibung:** Nur Cache (Redis) Status

**Response (200 | 503):**
```json
{
  "status": "healthy|degraded|unhealthy",
  "type": "Redis",
  "responseTime": 15
}
```

**Curl Example:**
```bash
curl http://localhost:5000/api/health/cache
```

---

### GET /api/health/resources
**Beschreibung:** System Ressourcen Auslastung

**Response (200):**
```json
{
  "cpu": {
    "percent": 25,
    "cores": 8
  },
  "memory": {
    "percent": 42,
    "used": 5120,
    "total": 16384
  },
  "disk": {
    "percent": 65,
    "used": 300,
    "total": 500
  }
}
```

**Curl Example:**
```bash
curl http://localhost:5000/api/health/resources
```

---

### GET /api/health/ready
**Beschreibung:** Kubernetes Readiness Probe

**Response (200 | 503):**
```json
{
  "ready": true,
  "timestamp": "2026-01-15T14:32:00Z"
}
```

**Curl Example:**
```bash
curl http://localhost:5000/api/health/ready
```

**Kubernetes Integration:**
```yaml
readinessProbe:
  httpGet:
    path: /api/health/ready
    port: 5000
  initialDelaySeconds: 10
  periodSeconds: 5
  failureThreshold: 3
```

---

### GET /api/health/live
**Beschreibung:** Kubernetes Liveness Probe

**Response (200 | 500):**
```json
{
  "alive": true,
  "timestamp": "2026-01-15T14:32:00Z"
}
```

**Curl Example:**
```bash
curl http://localhost:5000/api/health/live
```

**Kubernetes Integration:**
```yaml
livenessProbe:
  httpGet:
    path: /api/health/live
    port: 5000
  initialDelaySeconds: 30
  periodSeconds: 10
  failureThreshold: 3
```

---

## FRONTEND API

### errorTracker
```javascript
// Initialization
errorTracker.captureError(error)
errorTracker.captureMessage(message, level)
errorTracker.captureBreadcrumb(message, data)
errorTracker.setUser(userId, userData)
errorTracker.clearUser()

// Information
errorTracker.getStats()  // { total, errors, messages, warnings }

// Transmission
await errorTracker.flush()  // Manually flush to server
```

### performanceAnalytics
```javascript
// Metrics
performanceAnalytics.getMetrics()         // All metrics
performanceAnalytics.getPerformanceRating() // Ratings per metric
performanceAnalytics.getPerformanceScore()  // Overall score 0-100

// Reporting
performanceAnalytics.printReport()  // Console output
await performanceAnalytics.sendMetrics()  // Send to server

// Dashboard
window.performanceAnalytics.metrics  // Direct access
```

### errorDashboard (Dev only)
```javascript
// Auto-initialized in development
window.errorDashboard  // Reference to dashboard UI

// Methods
errorDashboard.loadErrors()  // Refresh error list
errorDashboard.clearErrors() // Clear all errors
```

---

## STATUS CODES

### Success
```
200  OK
201  Created
```

### Client Errors
```
400  Bad Request         (malformed JSON)
404  Not Found          (resource doesn't exist)
```

### Server Errors
```
500  Internal Error     (database/system error)
503  Unavailable        (service down)
```

---

## HEADERS

### Request
```
Content-Type: application/json
Authorization: Bearer token (if required)
```

### Response
```
Content-Type: application/json
X-Request-ID: unique-id
```

---

## RATE LIMITING

Empfohlene Limits (optional):
```
/api/errors           : 100 requests/minute
/api/errors/dashboard : 10 requests/minute
/api/health           : 60 requests/minute
/api/health/ready     : 30 requests/minute
```

---

## AUTHENTICATION

Alle Endpoints mit `@require_auth` benötigen:
```
Authorization: Bearer <token>
```

Derzeit offen:
- `POST /api/errors` (public, für Frontend)
- `GET /api/health` (public, für Monitoring)
- `GET /api/health/*` (public, für Kubernetes)

Geschützt:
- `GET /api/errors/*` (admin only)
- `PUT /api/errors/*` (admin only)
- `POST /api/errors/cleanup` (admin only)

---

## EXAMPLES

### Komplettes Error Tracking Szenario
```bash
# 1. Frontend sendet Fehler
curl -X POST http://localhost:5000/api/errors \
  -H "Content-Type: application/json" \
  -d '{
    "errors": [{
      "type": "error",
      "message": "Network timeout",
      "context": {
        "userId": "user-123",
        "environment": "production"
      }
    }]
  }'

# 2. Dashboard abrufen
curl http://localhost:5000/api/errors/dashboard?days=7

# 3. Fehlergruppen ansehen
curl http://localhost:5000/api/errors/groups?resolved=false

# 4. Group Details ansehen
curl http://localhost:5000/api/errors/groups/1

# 5. Group als gelöst markieren
curl -X PUT http://localhost:5000/api/errors/groups/1/resolve \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Health Monitoring Script
```bash
#!/bin/bash
# Check health every 30 seconds

while true; do
  STATUS=$(curl -s http://localhost:5000/api/health/status | grep -o '"healthy":[^,]*')
  RESOURCES=$(curl -s http://localhost:5000/api/health/resources)
  
  echo "[$(date)] Status: $STATUS"
  echo "Resources: $RESOURCES"
  
  sleep 30
done
```

---

## GLOSSARY

| Term | Bedeutung |
|------|-----------|
| Error Group | Mehrere Fehler mit gleicher Nachricht gruppiert |
| Breadcrumb | Context-Information über Benutzeraktion |
| Core Web Vitals | LCP, FID, CLS - wichtige Performance Metriken |
| Readiness Probe | Prüft ob Service Traffic annehmen kann |
| Liveness Probe | Prüft ob Service noch am Leben ist |
| Flush | Sende gepufferte Fehler zu Server |
| RUM | Real User Monitoring - echte User Metriken |

---

**Version:** 1.0  
**Last Updated:** Januar 2026  
**Phase:** 5
