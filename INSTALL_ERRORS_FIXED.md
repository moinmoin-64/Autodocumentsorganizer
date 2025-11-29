# Fehleranalyse & Lösungen - Raspberry Pi Installation

## 🔴 Probleme in der Original-Installation

### 1. **libgl1-mesa-glx nicht verfügbar**
```
E: Package 'libgl1-mesa-glx' has no installation candidate
```

**Ursache:**  
- Debian Trixie hat `libgl1-mesa-glx` durch `libgl1` ersetzt
- Alte Ubuntu/Debian Paketnamen funktionieren nicht mehr

**Lösung:**  
✅ In `install.sh` korrigiert:
```bash
# ALT (funktioniert nicht):
apt-get install -y libgl1-mesa-glx

# NEU (funktioniert):
apt-get install -y libgl1
# Fallback: libgl1-mesa-dri
```

---

### 2. **Redis Server nicht gefunden**
```
Failed to enable unit: Unit redis-server.service does not exist
Failed to start redis-server.service: Unit redis-server.service not found.
```

**Ursache:**  
- Redis-Paket nicht in allen Debian-Repositories verfügbar
- Flask-Limiter benötigt Redis nur als optional für verteilte Rate-Limiting

**Lösung:**  
✅ Redis als **optional** markiert:
```bash
# Versuche Redis zu installieren, aber fahre fort wenn nicht verfügbar
if apt-get install -y redis-server 2>/dev/null; then
    systemctl enable redis-server
else
    echo "⚠ Redis nicht verfügbar - Flask-Limiter nutzt Memory-Backend"
fi
```

✅ In `server.py` ist Memory-Fallback bereits konfiguriert:
```python
limiter = Limiter(
    app=app,
    storage_uri="memory://"  # ← Funktioniert ohne Redis!
)
```

---

### 3. **Falscher Pfad im Install-Script**
```
./install.sh: line 55: cd: /home/pi/OrganisationsAI: No such file or directory
```

**Ursache:**  
- Hartkodierter Pfad `/home/pi/OrganisationsAI`
- Ihr tatsächlicher Pfad: `/home/oliver/Autodocumentsorganizer`

**Lösung:**  
✅ Auto-Detection des Projekt-Verzeichnisses:
```bash
# NEU: Intelligente Pfad-Erkennung
REAL_USER=${SUDO_USER:-$(logname)}
REAL_HOME=$(eval echo "~$REAL_USER")

if [ -d "$REAL_HOME/Autodocumentsorganizer" ]; then
    PROJECT_DIR="$REAL_HOME/Autodocumentsorganizer"
elif [ -d "$REAL_HOME/OrganisationsAI" ]; then
    PROJECT_DIR="$REAL_HOME/OrganisationsAI"
elif [ -f "$(pwd)/main.py" ]; then
    PROJECT_DIR="$(pwd)"
fi
```

---

### 4. **HPLIP Python Syntax Warnings**
```
/usr/share/hplip/base/g.py:304: SyntaxWarning: invalid escape sequence '\|'
```

**Ursache:**  
- HPLIP-Paket enthält veralteten Python-Code
- Nicht-kritisch, nur Warnungen

**Lösung:**  
⚠️ Kann ignoriert werden - HPLIP funktioniert trotzdem  
Alternativ: Nach Installation aktualisieren wenn verfügbar

---

### 5. **libglib2.0-0 → libglib2.0-0t64**

**Ursache:**  
- Debian Trixie verwendet neue Paketnamen mit `t64` Suffix (Time64 Support)

**Lösung:**  
✅ Paketname aktualisiert:
```bash
apt-get install -y libglib2.0-0t64  # Debian Trixie
```

---

## ✅ Korrigiertes install.sh

Das neue `install.sh` behebt alle Probleme:

1. ✅ **Error-Handling**: Einzelne Pakete werden mit Try-Catch installiert
2. ✅ **Flexible Pfade**: Auto-Detection des Projektverzeichnisses
3. ✅ **Debian Trixie**: Korrekte Paketnamen (`libgl1`, `libglib2.0-0t64`)
4. ✅ **Optional Redis**: Funktioniert mit Memory-Backend
5. ✅ **User-Input**: Interaktive Model-Auswahl
6. ✅ **Korrekte Berechtigungen**: venv als User erstellt (nicht root)

---

## 🚀 Nutzung des korrigierten Scripts

```bash
# 1. Zum Projektverzeichnis wechseln
cd ~/Autodocumentsorganizer

# 2. Ausführbar machen
chmod +x install.sh

# 3. Als Root ausführen
sudo ./install.sh

# Das Script wird:
# - Auto-Detection durchführen
# - Fehlende Pakete überspringen
# - User/Pfade automatisch erkennen
# - Nach Model-Präferenz fragen
```

---

## 📋 Manuelle Fixes (falls benötigt)

### Falls Redis nachträglich benötigt wird:

```bash
# Versuche Redis manuell zu installieren
sudo apt-get install redis-server

# Falls nicht verfügbar, Redis aus Quellen kompilieren:
cd /tmp
wget http://download.redis.io/releases/redis-7.2.4.tar.gz
tar xzf redis-7.2.4.tar.gz
cd redis-7.2.4
make
sudo make install
```

### Falls OpenGL-Probleme auftreten:

```bash
# Installiere alle Mesa-Pakete
sudo apt-get install -y \
    libgl1 \
    libgl1-mesa-dri \
    libglx-mesa0 \
    libgles2-mesa
```

### Falls Scanner-Gruppe fehlt:

```bash
# Erstelle Scanner-Gruppe manuell
sudo groupadd scanner
sudo usermod -a -G scanner oliver
```

---

## 🔍 Verifikation

Nach Installation prüfen:

```bash
# Python Packages
source venv/bin/activate
pip list | grep -E 'Flask|Werkzeug|APScheduler|opencv'

# System-Pakete
dpkg -l | grep -E 'tesseract|sane|ollama'

# Services
systemctl status document-manager
systemctl status ollama

# Ollama Models
ollama list

# Scanner
scanimage -L
```

---

## 📝 Zusammenfassung

**Hauptprobleme:**
1. ❌ Veraltete Paketnamen (Debian Trixie)
2. ❌ Hartkodierte Pfade
3. ❌ Fehlende Error-Handling

**Lösungen:**
1. ✅ Aktualisierte Paketnamen + Fallbacks
2. ✅ Auto-Detection von User & Pfaden
3. ✅ Graceful Degradation (Redis optional)

Das System funktioniert jetzt **auch ohne Redis** mit dem Memory-Backend von Flask-Limiter!
