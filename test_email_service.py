"""
Test Script für Email Receiver
Testet die Email-Integration ohne Server zu starten
"""

import sys
from pathlib import Path

# Add app to path
sys.path.append(str(Path(__file__).parent))

from app.email_receiver import EmailReceiver
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_email_receiver():
    """Testet EmailReceiver Konfiguration und Verbindung"""
    
    print("=" * 60)
    print("Email Receiver Test")
    print("=" * 60)
    
    try:
        # 1. Initialisierung
        print("\n1. Initialisiere EmailReceiver...")
        receiver = EmailReceiver()
        print("   ✅ EmailReceiver erfolgreich initialisiert")
        
        # 2. Config-Check
        print("\n2. Prüfe Konfiguration...")
        enabled = receiver.email_config.get('enabled', False)
        host = receiver.email_config.get('host')
        user = receiver.email_config.get('user')
        
        print(f"   Email-Integration: {'✅ Aktiviert' if enabled else '❌ Deaktiviert'}")
        print(f"   IMAP Host: {host}")
        print(f"   IMAP User: {user}")
        print(f"   Upload Folder: {receiver.upload_folder}")
        
        if not enabled:
            print("\n⚠️  Email-Integration ist deaktiviert!")
            print("   Setze 'enabled: true' in config.yaml unter 'email'")
            return False
            
        # 3. Verbindungstest (nur wenn konfiguriert)
        if all([host, user, receiver.email_config.get('password')]):
            print("\n3. Teste IMAP-Verbindung...")
            if receiver.connect():
                print("   ✅ IMAP-Verbindung erfolgreich!")
                receiver.disconnect()
                print("   ✅ Disconnect erfolgreich")
                
                print("\n" + "=" * 60)
                print("✅ Email Service ist voll funktionsfähig!")
                print("=" * 60)
                return True
            else:
                print("   ❌ IMAP-Verbindung fehlgeschlagen")
                print("   Prüfe Host, Port, Username und Passwort in config.yaml")
                return False
        else:
            print("\n⚠️  IMAP-Credentials unvollständig in config.yaml")
            print("   Benötigt: host, user, password")
            return False
            
    except Exception as e:
        print(f"\n❌ Fehler beim Test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_email_receiver()
    sys.exit(0 if success else 1)
