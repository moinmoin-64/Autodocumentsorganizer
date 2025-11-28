#!/bin/bash
#
# Setup Cron Job für automatische Backups
# Führt täglich um 3 Uhr morgens ein Backup aus
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKUP_SCRIPT="$SCRIPT_DIR/backup.py"
PYTHON_PATH="$SCRIPT_DIR/venv/bin/python3"

# Erstelle Cron-Job
CRON_JOB="0 3 * * * $PYTHON_PATH $BACKUP_SCRIPT create --no-docs >> /var/log/document-manager/backup.log 2>&1"

# Prüfe ob schon existiert
if crontab -l 2>/dev/null | grep -q "$BACKUP_SCRIPT"; then
    echo "Backup Cron-Job existiert bereits"
    exit 0
fi

# Füge hinzu
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "✓ Backup Cron-Job eingerichtet"
echo "  Schedule: Täglich um 3:00 Uhr"
echo "  Backup nur DB/CSV (keine Dokumente)"
echo "  Logs: /var/log/document-manager/backup.log"
echo ""
echo "Manuelles Backup: python backup.py create"
echo "Backup mit Dokumenten: python backup.py create"
echo "Liste Backups: python backup.py list"
