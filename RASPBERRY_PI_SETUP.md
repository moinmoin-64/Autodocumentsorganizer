# Raspberry Pi Setup Guide - OrganisationsAI

## Status der Installation ✅

Basierend auf Ihrer Installation sind folgende Komponenten bereits installiert:

- ✅ **Python 3** mit pip
- ✅ **System-Pakete**: CUPS, SANE, Scanner-Treiber
- ✅ **Ollama** (läuft im CPU-Modus)
- ✅ **Python Libraries**: OpenBLAS, JPEG, etc.

## Fehlende Schritte

### 1. Virtual Environment erstellen

```bash
cd ~/Autodocumentsorganizer

# Virtual Environment erstellen
python3 -m venv venv

# Aktivieren
source venv/bin/activate

# Dependencies installieren
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Konfiguration anpassen

#### a) Umgebungsvariablen (.env)

```bash
# Erstelle .env Datei
nano .env
```

Füge folgendes ein:

```bash
# SECRET_KEY für Flask (generiere mit: python3 -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY=dein_generierter_secret_key_hier

# Email-Passwort (optional, wenn Email-Integration genutzt wird)
EMAIL_PASSWORD=dein_email_passwort

# Optional: Alternative Pfade
# DATABASE_PATH=/home/oliver/Autodocumentsorganizer/data/documents.db
# OLLAMA_URL=http://localhost:11434
```

**Secret Key generieren:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

#### b) Email-Konfiguration (Optional)

Falls Sie Email-Integration nutzen möchten, bearbeiten Sie `config.yaml`:

```bash
nano config.yaml
```

Ändern Sie den Email-Abschnitt:

```yaml
email:
  enabled: true  # ← von false auf true ändern
  host: imap.gmail.com  # Ihr IMAP-Server
  port: 993
  user: ihre-email@gmail.com
  password: ""  # Wird aus .env (EMAIL_PASSWORD) geladen
  poll_interval: 300  # 5 Minuten
```

**Für Gmail:**
- Aktivieren Sie "2-Faktor-Authentifizierung"
- Erstellen Sie ein "App-Passwort" unter https://myaccount.google.com/apppasswords
- Nutzen Sie das App-Passwort in der `.env` Datei

### 3. Passwörter hashen (Sicherheit)

```bash
# Aktiviere venv falls noch nicht aktiv
source venv/bin/activate

# Führe Migration aus
python3 migrate_passwords.py

# Backup wird automatisch erstellt
```

### 4. Systemd Service installieren

```bash
# Log-Verzeichnis erstellen
sudo mkdir -p /var/log/document-manager
sudo chown oliver:oliver /var/log/document-manager

# Service-Datei kopieren
sudo cp systemd/document-manager.service /etc/systemd/system/

# Systemd neu laden
sudo systemctl daemon-reload

# Service aktivieren (startet automatisch beim Boot)
sudo systemctl enable document-manager

# Service starten
sudo systemctl start document-manager

# Status prüfen
sudo systemctl status document-manager
```

### 5. Logs überwachen

```bash
# Echtzeit-Logs ansehen
tail -f /var/log/document-manager/app.log

# Fehler-Logs
tail -f /var/log/document-manager/error.log

# Systemd Journal
sudo journalctl -u document-manager -f
```

### 6. Firewall konfigurieren (Optional)

Falls Sie von anderen Geräten auf die Web-UI zugreifen möchten:

```bash
# Port 5001 öffnen (Standard-Port aus config.yaml)
sudo ufw allow 5001/tcp

# Firewall Status
sudo ufw status
```

## Zugriff auf die Web-Oberfläche

Nach erfolgreicher Installation:

**Lokal auf dem Raspberry Pi:**
```
http://localhost:5001
```

**Von anderen Geräten im Netzwerk:**
```
http://[RASPBERRY_PI_IP]:5001
```

IP-Adresse herausfinden:
```bash
hostname -I
```

**Standard-Login:**
- Username: `admin`
- Passwort: (siehe `config.yaml` → `users` → `admin` → `password`)

⚠️ **Wichtig:** Nach dem ersten Login sollten Sie:
1. Das Admin-Passwort in `config.yaml` ändern
2. Passwort-Migration ausführen (`python3 migrate_passwords.py`)

## Ollama Models installieren

```bash
# Modell herunterladen (dauert je nach Größe)
ollama pull llama3.2:1b  # Kleines Modell für Raspberry Pi (1.3GB)

# Alternativ größeres Modell (braucht mehr RAM):
# ollama pull llama3.2:3b  # (3GB)

# Modell testen
ollama run llama3.2:1b "Hallo, wie geht es dir?"

# Verfügbare Modelle anzeigen
ollama list
```

**Empfohlene Modelle für Raspberry Pi:**
- `llama3.2:1b` - Schnell, wenig RAM (empfohlen)
- `llama3.2:3b` - Bessere Qualität, mehr RAM benötigt
- `phi3:mini` - Alternative, 3.8GB

## Troubleshooting

### Service startet nicht

```bash
# Detaillierte Fehler anzeigen
sudo journalctl -u document-manager -n 50 --no-pager

# Manuell starten zum Testen
cd ~/Autodocumentsorganizer
source venv/bin/activate
python3 main.py
```

### Ollama funktioniert nicht

```bash
# Ollama Service Status
sudo systemctl status ollama

# Ollama neu starten
sudo systemctl restart ollama

# Verbindung testen
curl http://localhost:11434/api/tags
```

### Email-Integration funktioniert nicht

```bash
# Test-Script ausführen
cd ~/Autodocumentsorganizer
source venv/bin/activate
python3 test_email_service.py
```

### Datenbank-Probleme

```bash
# Backup erstellen
cp data/documents.db data/documents.db.backup

# Datenbank-Integrität prüfen
sqlite3 data/documents.db "PRAGMA integrity_check;"
```

## Performance-Optimierung für Raspberry Pi

### 1. RAM-Nutzung reduzieren

In `config.yaml`:

```yaml
system:
  performance:
    max_workers: 2  # Reduziere von 4 auf 2
    ocr_workers: 1  # Reduziere OCR-Worker
```

### 2. Swap vergrößern (bei wenig RAM)

```bash
# Swap-Größe prüfen
free -h

# Swap auf 2GB erhöhen
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Ändere: CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### 3. CPU-Gouverneur auf Performance

```bash
# Aktuellen Modus prüfen
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

# Auf Performance setzen
echo "performance" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

## Backup-Strategie

### Automatisches Backup einrichten

```bash
# Backup-Script ausführbar machen
chmod +x setup_backup_cron.sh

# Cron-Job einrichten (täglich um 2 Uhr)
./setup_backup_cron.sh
```

### Manuelles Backup

```bash
# Aktiviere venv
source venv/bin/activate

# Backup erstellen
python3 backup.py
```

Backups werden gespeichert in: `data/backups/`

## Nützliche Befehle

```bash
# Service neu starten
sudo systemctl restart document-manager

# Service stoppen
sudo systemctl stop document-manager

# Service-Logs löschen
sudo truncate -s 0 /var/log/document-manager/app.log

# Ressourcen-Nutzung anzeigen
htop

# Festplatten-Nutzung
df -h

# Ordner-Größe prüfen
du -sh ~/Autodocumentsorganizer/data
```

## Update-Prozedur

```bash
# 1. Service stoppen
sudo systemctl stop document-manager

# 2. Code aktualisieren (git pull oder neue Dateien kopieren)
cd ~/Autodocumentsorganizer
# git pull  # falls Git verwendet wird

# 3. Dependencies aktualisieren
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 4. Service starten
sudo systemctl start document-manager

# 5. Status prüfen
sudo systemctl status document-manager
```

## Support & Logs

Bei Problemen sammeln Sie folgende Informationen:

```bash
# System-Info
uname -a
python3 --version
pip list | grep -E 'Flask|werkzeug|APScheduler'

# Service-Status
sudo systemctl status document-manager

# Letzte 100 Zeilen App-Log
tail -n 100 /var/log/document-manager/app.log

# Letzte 50 Zeilen Error-Log
tail -n 50 /var/log/document-manager/error.log
```

---

**Viel Erfolg mit Ihrer OrganisationsAI Installation! 🚀**
