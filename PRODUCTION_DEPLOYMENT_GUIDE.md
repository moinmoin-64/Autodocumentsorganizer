# 🚀 Production Deployment Guide

**Komplette Anleitung für Produktion**

---

## 1️⃣ Pre-Deployment Checklist

### System Requirements
- [ ] Linux Server (Ubuntu 20.04+ oder CentOS 8+)
- [ ] 4+ CPU Cores
- [ ] 8+ GB RAM
- [ ] 50+ GB Storage
- [ ] Docker & Docker-Compose installiert
- [ ] PostgreSQL 13+
- [ ] Redis 6+

### Security Checklist
- [ ] SSL/TLS Zertifikat (Let's Encrypt)
- [ ] Firewall konfiguriert
- [ ] SSH-Keys konfiguriert (keine Passwörter!)
- [ ] Fail2Ban oder ähnlich installiert
- [ ] Log-Rotation konfiguriert

### Backup Checklist
- [ ] Backup-Strategie definiert
- [ ] Backup-Storage vorbereitet
- [ ] Restore-Prozess getestet
- [ ] Off-site Backups eingerichtet

---

## 2️⃣ Environment-Vorbereitung

### 1. Server aktualisieren
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    net-tools \
    ntp \
    fail2ban
```

### 2. Docker installieren
```bash
# Docker Repository hinzufügen
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository \
    "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) \
    stable"

# Docker installieren
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose

# Docker ohne sudo verwenden
sudo usermod -aG docker $USER
newgrp docker
```

### 3. PostgreSQL & Redis
```bash
# PostgreSQL
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql

# Redis
sudo apt install -y redis-server
sudo systemctl start redis-server

# Services autostart
sudo systemctl enable postgresql redis-server
```

---

## 3️⃣ Application Deployment

### 1. Repository klonen
```bash
cd /opt
git clone https://github.com/yourname/organisationsai.git
cd organisationsai
```

### 2. SSL Zertifikat (Let's Encrypt)
```bash
# Certbot installieren
sudo apt install -y certbot python3-certbot-nginx

# Zertifikat generieren
sudo certbot certonly --standalone \
    -d yourdomain.com \
    -d www.yourdomain.com \
    -m your-email@example.com \
    --agree-tos

# Zertifikate sind jetzt unter /etc/letsencrypt/live/yourdomain.com/
```

### 3. Environment-Variablen konfigurieren
```bash
# Sichere Umgebung mit SECRET_KEY
cat > .env.production << 'EOF'
# === SICHERHEIT ===
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
DEBUG=False
FLASK_ENV=production

# === DATENBANK ===
DATABASE_URL=postgresql://user:password@localhost:5432/organisationsai
SQLALCHEMY_ECHO=False

# === REDIS ===
REDIS_URL=redis://localhost:6379/0

# === EMAIL ===
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_USE_TLS=True

# === LOGGING ===
LOG_LEVEL=INFO
LOG_FORMAT=json

# === OCR ===
OCR_ENABLED=True
TESSERACT_PATH=/usr/bin/tesseract

# === AI/ML ===
OLLAMA_ENABLED=False
OLLAMA_URL=http://localhost:11434

# === STORAGE ===
STORAGE_BACKEND=local
STORAGE_PATH=/var/organisationsai/uploads

# === CORS ===
CORS_ORIGINS=https://yourdomain.com

# === SECURITY ===
RATE_LIMIT_ENABLED=True
SESSION_TIMEOUT=3600
MAX_CONTENT_LENGTH=104857600
EOF

chmod 600 .env.production
```

### 4. Datenbank initialisieren
```bash
# PostgreSQL User & Database
sudo -u postgres psql << SQL
CREATE USER organisationsai WITH PASSWORD 'secure_password';
CREATE DATABASE organisationsai OWNER organisationsai;
GRANT ALL PRIVILEGES ON DATABASE organisationsai TO organisationsai;
SQL

# Migrations ausführen
docker-compose exec web python -m flask db upgrade
```

### 5. Docker Image bauen
```bash
# Mit Production Dockerfile
docker build -f Dockerfile.production \
    -t organisationsai:1.0.0 \
    -t organisationsai:latest .

# Optional: Zu Registry pushen
docker tag organisationsai:1.0.0 yourregistry.azurecr.io/organisationsai:1.0.0
docker push yourregistry.azurecr.io/organisationsai:1.0.0
```

### 6. Docker-Compose für Production
```bash
# Erstelle production docker-compose
cat > docker-compose.production.yml << 'EOF'
version: '3.8'

services:
  web:
    image: organisationsai:1.0.0
    container_name: organisationsai-web
    restart: always
    environment:
      - FLASK_APP=app.server:create_app
      - FLASK_ENV=production
    env_file:
      - .env.production
    volumes:
      - /var/organisationsai/data:/app/data
      - /var/organisationsai/logs:/app/logs
      - /etc/letsencrypt/live/yourdomain.com:/app/certs:ro
    ports:
      - "5001:5001"
    networks:
      - organisationsai-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15-alpine
    container_name: organisationsai-postgres
    restart: always
    environment:
      - POSTGRES_DB=organisationsai
      - POSTGRES_USER=organisationsai
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - organisationsai-postgres:/var/lib/postgresql/data
    networks:
      - organisationsai-net
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  redis:
    image: redis:7-alpine
    container_name: organisationsai-redis
    restart: always
    volumes:
      - organisationsai-redis:/data
    networks:
      - organisationsai-net
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  nginx:
    image: nginx:alpine
    container_name: organisationsai-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /path/to/nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt/live/yourdomain.com:/etc/letsencrypt:ro
    networks:
      - organisationsai-net
    depends_on:
      - web

networks:
  organisationsai-net:
    driver: bridge

volumes:
  organisationsai-postgres:
  organisationsai-redis:
EOF

# Container starten
docker-compose -f docker-compose.production.yml up -d
```

---

## 4️⃣ NGINX Configuration

```bash
cat > nginx.conf << 'EOF'
upstream organisationsai {
    server web:5001;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # SSL Best Practices
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://organisationsai;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /static/ {
        alias /app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF
```

---

## 5️⃣ Monitoring & Logging

### 1. Prometheus Installation
```bash
docker pull prom/prometheus

cat > prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  scrape_timeout: 10s

scrape_configs:
  - job_name: 'organisationsai'
    static_configs:
      - targets: ['localhost:5001']
EOF

docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

### 2. Logging mit ELK
```bash
# Elasticsearch, Logstash, Kibana Stack
docker pull docker.elastic.co/elasticsearch/elasticsearch:8.0.0
docker pull docker.elastic.co/kibana/kibana:8.0.0

# (Detaillierte Anleitung siehe ELK Docs)
```

---

## 6️⃣ Backup & Recovery

### Tägliche Backups
```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/organisationsai"

# PostgreSQL Backup
docker-compose exec -T postgres pg_dump \
    -U organisationsai \
    organisationsai > "$BACKUP_DIR/db_$DATE.sql"

# Daten-Verzeichnis Backup
tar -czf "$BACKUP_DIR/data_$DATE.tar.gz" /var/organisationsai/data

# Alte Backups löschen (älter als 30 Tage)
find "$BACKUP_DIR" -type f -mtime +30 -delete

# Optional: Zu S3/Cloud hochladen
aws s3 sync "$BACKUP_DIR" s3://your-backup-bucket/organisationsai/
```

### Restore-Prozess
```bash
# Datenbank wiederherstellen
docker-compose exec -T postgres psql \
    -U organisationsai \
    organisationsai < backup.sql

# Daten wiederherstellen
tar -xzf data_backup.tar.gz -C /var/organisationsai/
```

---

## 7️⃣ Monitoring & Alerts

### Health Checks
```bash
# Regelmäßig prüfen
curl -f https://yourdomain.com/health || alert "Application unhealthy"
```

### Log Monitoring
```bash
# Fehler im Log überwachen
tail -f /var/organisationsai/logs/error.log | grep -i "error\|exception"
```

---

## 8️⃣ Performance Tuning

### PostgreSQL
```sql
-- postgresql.conf Optimierungen
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
```

### Redis
```
# redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
```

---

## 9️⃣ Troubleshooting

### Container nicht startend
```bash
docker-compose logs web
docker-compose logs postgres
```

### Datenbank-Verbindung fehlgeschlagen
```bash
docker-compose exec web python -c "from app.database import get_db; print(get_db())"
```

### Performance-Probleme
```bash
docker stats  # CPU/Memory Nutzung
docker-compose exec postgres psql -U organisationsai -c "SELECT * FROM pg_stat_statements"
```

---

## 🔟 Nach Deployment

- [ ] SSL zertifikat auto-renewal testen
- [ ] Backups testen
- [ ] Monitoring aktivieren
- [ ] Logging konfigurieren
- [ ] Load-Tests durchführen
- [ ] Firewall-Regeln prüfen
- [ ] Dokumentation für Team erstellen
- [ ] Incident-Response Plan definieren

---

**Zuletzt aktualisiert: Januar 8, 2026**
