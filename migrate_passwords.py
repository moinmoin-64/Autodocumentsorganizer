"""
Migration Script: Hash existing passwords in config.yaml
Dieses Script hasht alle Klartext-Passwörter in config.yaml
"""

import yaml
from werkzeug.security import generate_password_hash
from pathlib import Path
import shutil
from datetime import datetime

def migrate_passwords(config_path='config.yaml'):
    """Migriert Klartext-Passwörter zu Hashes"""
    
    # Backup erstellen
    backup_path = f"{config_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy(config_path, backup_path)
    print(f"✅ Backup erstellt: {backup_path}")
    
    # Lade Config
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Checke ob Migration nötig
    users = config.get('auth', {}).get('users', {})
    
    if not users:
        print("⚠️  Keine User gefunden")
        return
    
    migrated_count = 0
    
    for username, password in users.items():
        # Wenn Passwort noch nicht gehasht ist
        if not password.startswith(('pbkdf2:', 'scrypt:', 'bcrypt:')):
            hashed = generate_password_hash(password)
            config['auth']['users'][username] = hashed
            print(f"✅ Migriert: {username}")
            migrated_count += 1
        else:
            print(f"⏩ Bereits gehasht: {username}")
    
    if migrated_count > 0:
        # Speichere aktualisierte Config
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        print(f"\n✅ Migration abgeschlossen! {migrated_count} Passwörter gehasht.")
        print(f"📁 Backup: {backup_path}")
    else:
        print("\n⏩ Keine Migration nötig - alle Passwörter bereits gehasht")

if __name__ == '__main__':
    migrate_passwords()
