"""
Email Receiver Module
Ruft E-Mails via IMAP ab und extrahiert Anhänge (PDF/Bilder)
"""

import logging
import imaplib
import email
import os
from email.header import decode_header
from email.message import Message
from pathlib import Path
from typing import List, Optional, Tuple
import yaml
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailReceiver:
    """
    IMAP Email Receiver für automatischen Dokumenten-Import
    
    Verbindet sich mit einem IMAP-Server, ruft ungelesene E-Mails ab
    und extrahiert PDF- und Bild-Anhänge für die weitere Verarbeitung.
    """
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        Initialisiert Email Receiver
        
        Args:
            config_path: Pfad zur YAML-Konfigurationsdatei
        """
        self.config_path = config_path
        self._load_config()
        self.connection: Optional[imaplib.IMAP4_SSL] = None
        
    def _load_config(self) -> None:
        """Lädt Konfiguration aus YAML-Datei"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            self.email_config = config.get('email', {})
            self.upload_folder = config['system']['storage']['upload_folder']
            
    def connect(self) -> bool:
        """
        Verbindet zum IMAP Server
        
        Returns:
            True wenn Verbindung erfolgreich, sonst False
        """
        try:
            if not self.email_config.get('enabled', False):
                logger.debug("Email-Integration deaktiviert")
                return False
                
            host = self.email_config.get('host')
            port = self.email_config.get('port', 993)
            user = self.email_config.get('user')
            password = self.email_config.get('password')
            
            if not all([host, user, password]):
                logger.error("Email-Konfiguration unvollständig")
                return False
                
            self.connection = imaplib.IMAP4_SSL(host, port)
            self.connection.login(user, password)
            logger.info(f"✅ Verbunden mit IMAP: {host} als {user}")
            return True
            
        except imaplib.IMAP4.error as e:
            logger.error(f"❌ IMAP Authentifizierungsfehler: {e}")
            return False
        except (OSError, TimeoutError) as e:
            logger.error(f"❌ IMAP Verbindungsfehler: {e}")
            return False
            
    def disconnect(self) -> None:
        """Trennt IMAP-Verbindung sauber"""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
            except (imaplib.IMAP4.error, OSError) as e:
                logger.debug(f"IMAP Disconnect-Warnung: {e}")
            finally:
                self.connection = None

    def fetch_attachments(self) -> List[str]:
        """
        Ruft neue E-Mails ab und speichert Anhänge
        
        Returns:
            Liste der gespeicherten Dateipfade
        """
        saved_files: List[str] = []
        
        if not self.connect():
            return []
            
        try:
            self.connection.select('INBOX')
            
            # Suche nach ungelesenen Mails
            status, messages = self.connection.search(None, 'UNSEEN')
            
            if status != 'OK' or not messages[0]:
                logger.debug("Keine ungelesenen E-Mails gefunden")
                return []
                
            for msg_id in messages[0].split():
                try:
                    files = self._process_email(msg_id)
                    saved_files.extend(files)
                except Exception as e:
                    logger.error(f"Fehler bei Email {msg_id.decode()}: {e}")
                    
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP Fehler beim Abrufen der Mails: {e}")
        except Exception as e:
            logger.error(f"Unerwarteter Fehler beim Abrufen der Mails: {e}")
        finally:
            self.disconnect()
            
        return saved_files
    
    def _process_email(self, msg_id: bytes) -> List[str]:
        """
        Verarbeitet eine einzelne E-Mail und extrahiert Anhänge
        
        Args:
            msg_id: IMAP Message ID
            
        Returns:
            Liste gespeicherter Dateipfade
        """
        saved_files: List[str] = []
        
        res, msg_data = self.connection.fetch(msg_id, '(RFC822)')
        if res != 'OK':
            return []
            
        email_body = msg_data[0][1]
        mail = email.message_from_bytes(email_body)
        
        subject = self._decode_subject(mail.get("Subject", ""))
        sender = mail.get("From", "Unknown")
        
        logger.info(f"📧 Prüfe Email: '{subject}' von {sender}")
        
        # Anhänge verarbeiten
        for part in mail.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
                
            filename = part.get_filename()
            if not filename:
                continue
                
            filename = self._decode_filename(filename)
            
            # Nur PDF und Bilder akzeptieren
            ext = Path(filename).suffix.lower()
            if ext not in ['.pdf', '.jpg', '.jpeg', '.png']:
                logger.debug(f"Überspringe Anhang mit Extension: {ext}")
                continue
                
            # Speichern
            try:
                save_path = self._save_attachment(part, filename)
                if save_path:
                    saved_files.append(save_path)
                    logger.info(f"✅ Anhang gespeichert: {save_path}")
            except Exception as e:
                logger.error(f"Fehler beim Speichern von '{filename}': {e}")
                
        return saved_files
    
    def _save_attachment(self, part: Message, filename: str) -> Optional[str]:
        """
        Speichert einen E-Mail-Anhang
        
        Args:
            part: Email-Part mit Anhang
            filename: Original-Dateiname
            
        Returns:
            Pfad zur gespeicherten Datei oder None bei Fehler
        """
        # Sicherer Dateiname mit Zeitstempel
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"email_{timestamp}_{filename}"
        save_path = os.path.join(self.upload_folder, safe_filename)
        
        # Stelle sicher, dass Upload-Folder existiert
        os.makedirs(self.upload_folder, exist_ok=True)
        
        # Speichere Datei
        with open(save_path, 'wb') as f:
            payload = part.get_payload(decode=True)
            if payload:
                f.write(payload)
                return save_path
        
        return None

    def _decode_subject(self, subject: str) -> str:
        """
        Dekodiert Email-Betreff (RFC 2047)
        
        Args:
            subject: Kodierter Betreff
            
        Returns:
            Dekodierter Betreff als String
        """
        if not subject:
            return "(Kein Betreff)"
            
        decoded_list = decode_header(subject)
        subject_str = ""
        
        for text, charset in decoded_list:
            if isinstance(text, bytes):
                if charset:
                    try:
                        text = text.decode(charset)
                    except (UnicodeDecodeError, LookupError):
                        text = text.decode('utf-8', errors='ignore')
                else:
                    text = text.decode('utf-8', errors='ignore')
            subject_str += str(text)
            
        return subject_str

    def _decode_filename(self, filename: str) -> str:
        """
        Dekodiert Dateinamen (RFC 2047)
        
        Args:
            filename: Kodierter Dateiname
            
        Returns:
            Dekodierter Dateiname
        """
        return self._decode_subject(filename)
