"""
Advanced Email Parser
Erweiterte Email-Verarbeitung mit Metadaten-Extraktion und Anhang-Verarbeitung
"""

import logging
import email
from email.header import decode_header
from email.message import Message
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class EmailMetadataExtractor:
    """Extrahiert Metadaten aus Emails"""
    
    @staticmethod
    def extract_metadata(mail: Message) -> Dict:
        """
        Extrahiert alle wichtigen Metadaten aus einer Email
        
        Args:
            mail: Email-Message-Objekt
            
        Returns:
            Dictionary mit Metadaten
        """
        return {
            'subject': EmailMetadataExtractor._get_subject(mail),
            'from': EmailMetadataExtractor._get_from(mail),
            'to': EmailMetadataExtractor._get_to(mail),
            'date': EmailMetadataExtractor._get_date(mail),
            'cc': EmailMetadataExtractor._get_cc(mail),
            'bcc': EmailMetadataExtractor._get_bcc(mail),
            'message_id': mail.get('Message-ID', ''),
            'in_reply_to': mail.get('In-Reply-To', ''),
            'body_text': EmailMetadataExtractor._get_body_text(mail),
            'body_html': EmailMetadataExtractor._get_body_html(mail),
        }
    
    @staticmethod
    def _get_subject(mail: Message) -> str:
        """Get decoded subject"""
        subject = mail.get("Subject", "(No Subject)")
        decoded_list = decode_header(subject)
        
        result = ""
        for text, charset in decoded_list:
            if isinstance(text, bytes):
                try:
                    result += text.decode(charset or 'utf-8')
                except (UnicodeDecodeError, LookupError):
                    result += text.decode('utf-8', errors='ignore')
            else:
                result += str(text)
        
        return result
    
    @staticmethod
    def _get_from(mail: Message) -> str:
        """Get sender email"""
        return mail.get("From", "Unknown")
    
    @staticmethod
    def _get_to(mail: Message) -> List[str]:
        """Get recipient emails"""
        to = mail.get("To", "")
        return [x.strip() for x in to.split(",") if x.strip()]
    
    @staticmethod
    def _get_cc(mail: Message) -> List[str]:
        """Get CC emails"""
        cc = mail.get("Cc", "")
        return [x.strip() for x in cc.split(",") if x.strip()]
    
    @staticmethod
    def _get_bcc(mail: Message) -> List[str]:
        """Get BCC emails"""
        bcc = mail.get("Bcc", "")
        return [x.strip() for x in bcc.split(",") if x.strip()]
    
    @staticmethod
    def _get_date(mail: Message) -> Optional[str]:
        """Get email date"""
        return mail.get("Date")
    
    @staticmethod
    def _get_body_text(mail: Message) -> str:
        """Extract plain text body"""
        for part in mail.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        return payload.decode(charset)
                    except (UnicodeDecodeError, LookupError):
                        return payload.decode('utf-8', errors='ignore')
        return ""
    
    @staticmethod
    def _get_body_html(mail: Message) -> str:
        """Extract HTML body"""
        for part in mail.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        return payload.decode(charset)
                    except (UnicodeDecodeError, LookupError):
                        return payload.decode('utf-8', errors='ignore')
        return ""


class EmailAttachmentProcessor:
    """Verarbeitet und validiert Email-Anhänge"""
    
    # Unterstützte MIME-Typen
    SUPPORTED_TYPES = {
        'application/pdf': '.pdf',
        'image/jpeg': '.jpg',
        'image/png': '.png',
        'image/tiff': '.tiff',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
        'application/msword': '.doc',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
        'application/vnd.ms-excel': '.xls',
    }
    
    @staticmethod
    def extract_attachments(mail: Message) -> List[Dict]:
        """
        Extrahiert alle Anhänge aus einer Email
        
        Args:
            mail: Email-Message-Objekt
            
        Returns:
            Liste von Anhang-Objekten
        """
        attachments = []
        
        for part in mail.walk():
            # Überspringe nicht-Attachment-Parts
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            
            filename = part.get_filename()
            if not filename:
                continue
            
            # Dekodiere Filename
            filename = EmailMetadataExtractor._get_subject(Message())  # Misuse for header decoding
            try:
                decoded = decode_header(filename)
                filename = ""
                for text, charset in decoded:
                    if isinstance(text, bytes):
                        filename += text.decode(charset or 'utf-8', errors='ignore')
                    else:
                        filename += str(text)
            except:
                pass
            
            content_type = part.get_content_type()
            payload = part.get_payload(decode=True)
            
            if not payload:
                continue
            
            attachment = {
                'filename': filename,
                'content_type': content_type,
                'size': len(payload),
                'payload': payload,
                'supported': content_type in EmailAttachmentProcessor.SUPPORTED_TYPES,
            }
            
            # Validiere Dateiname
            if not EmailAttachmentProcessor._is_safe_filename(filename):
                logger.warning(f"Unsicherer Dateiname: {filename}")
                continue
            
            attachments.append(attachment)
        
        return attachments
    
    @staticmethod
    def _is_safe_filename(filename: str) -> bool:
        """Prüft ob Dateiname sicher ist"""
        # Verhindere Path-Traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        
        # Erlaube nur alphanumerisch + Punkte und Striche
        if not re.match(r'^[a-zA-Z0-9._\- äöüßÄÖÜ]+$', filename):
            return False
        
        return True
    
    @staticmethod
    def save_attachment(attachment: Dict, save_dir: str) -> Optional[str]:
        """
        Speichert einen Anhang sicher
        
        Args:
            attachment: Anhang-Dictionary
            save_dir: Zielverzeichnis
            
        Returns:
            Pfad zur gespeicherten Datei oder None
        """
        # Erstelle sichere Dateiname mit Timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"email_{timestamp}_{attachment['filename']}"
        
        # Stelle sicher Directory existiert
        Path(save_dir).mkdir(parents=True, exist_ok=True)
        
        save_path = Path(save_dir) / filename
        
        try:
            with open(save_path, 'wb') as f:
                f.write(attachment['payload'])
            
            logger.info(f"✅ Anhang gespeichert: {save_path} ({attachment['size']} bytes)")
            return str(save_path)
        
        except IOError as e:
            logger.error(f"❌ Fehler beim Speichern von {filename}: {e}")
            return None


class EmailContentExtractor:
    """Extrahiert Inhalte aus Email-Body"""
    
    @staticmethod
    def extract_dates_and_amounts(body_text: str) -> Dict[str, List]:
        """
        Extrahiert Daten und Geldbeträge aus Email-Text
        
        Args:
            body_text: Email-Body Text
            
        Returns:
            Dictionary mit Daten und Beträgen
        """
        return {
            'dates': EmailContentExtractor._extract_dates(body_text),
            'amounts': EmailContentExtractor._extract_amounts(body_text),
        }
    
    @staticmethod
    def _extract_dates(text: str) -> List[str]:
        """Extrahiert Datumsangaben"""
        patterns = [
            r'\d{1,2}[./-]\d{1,2}[./-]\d{2,4}',  # dd.mm.yyyy
            r'\d{4}[./-]\d{1,2}[./-]\d{1,2}',    # yyyy.mm.dd
            r'\d{1,2}\s+(Jan|Feb|Mär|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez)[a-z]*\s+\d{4}',
        ]
        
        dates = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        return list(set(dates))  # Duplikate entfernen
    
    @staticmethod
    def _extract_amounts(text: str) -> List[str]:
        """Extrahiert Geldbeträge"""
        patterns = [
            r'(\d{1,3}(?:\.\d{3})*,\d{2})\s*€',
            r'€\s*(\d{1,3}(?:\.\d{3})*,\d{2})',
            r'(\d+\.\d{2})\s*(EUR|€)',
        ]
        
        amounts = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            amounts.extend([m[0] if isinstance(m, tuple) else m for m in matches])
        
        return list(set(amounts))  # Duplikate entfernen


class EmailValidator:
    """Validiert und prüft Emails auf Sicherheit"""
    
    @staticmethod
    def validate_email(mail: Message) -> Dict[str, bool]:
        """
        Validiert eine Email auf verschiedene Sicherheitskriterien
        
        Args:
            mail: Email-Message-Objekt
            
        Returns:
            Dictionary mit Validierungsergebnissen
        """
        return {
            'has_subject': bool(mail.get('Subject')),
            'has_from': bool(mail.get('From')),
            'has_date': bool(mail.get('Date')),
            'is_signed': 'dkim-signature' in mail or 'signature' in str(mail).lower(),
            'has_attachments': EmailValidator._has_attachments(mail),
            'body_size_ok': EmailValidator._check_body_size(mail),
            'no_suspicious_content': EmailValidator._check_suspicious_content(mail),
        }
    
    @staticmethod
    def _has_attachments(mail: Message) -> bool:
        """Prüft ob Email Anhänge hat"""
        for part in mail.walk():
            if part.get('Content-Disposition') is not None:
                return True
        return False
    
    @staticmethod
    def _check_body_size(mail: Message, max_size_mb: int = 50) -> bool:
        """Prüft ob Email-Größe im erlaubten Bereich ist"""
        size = len(mail.as_string())
        size_mb = size / (1024 * 1024)
        return size_mb <= max_size_mb
    
    @staticmethod
    def _check_suspicious_content(mail: Message) -> bool:
        """Prüft auf verdächtige Inhalte"""
        suspicious_keywords = [
            'malware',
            'ransomware',
            'virus',
            'phishing',
            'trojan',
        ]
        
        body = EmailMetadataExtractor._get_body_text(mail).lower()
        
        for keyword in suspicious_keywords:
            if keyword in body:
                return False
        
        return True


class EmailParser:
    """Hauptklasse für Email-Verarbeitung"""
    
    def __init__(self):
        """Initialisiert Email Parser"""
        self.metadata_extractor = EmailMetadataExtractor()
        self.attachment_processor = EmailAttachmentProcessor()
        self.content_extractor = EmailContentExtractor()
        self.validator = EmailValidator()
    
    def parse_email(self, email_bytes: bytes, save_dir: Optional[str] = None) -> Dict:
        """
        Parst eine komplette Email
        
        Args:
            email_bytes: Raw Email-Bytes
            save_dir: Optional Directory zum Speichern von Anhängen
            
        Returns:
            Komplettes Email-Dictionary mit allen Infos
        """
        mail = email.message_from_bytes(email_bytes)
        
        # Extrahiere Metadaten
        metadata = self.metadata_extractor.extract_metadata(mail)
        
        # Extrahiere Anhänge
        attachments = self.attachment_processor.extract_attachments(mail)
        saved_files = []
        
        if save_dir:
            for attachment in attachments:
                if attachment['supported']:
                    saved_path = self.attachment_processor.save_attachment(
                        attachment,
                        save_dir
                    )
                    if saved_path:
                        saved_files.append(saved_path)
        
        # Extrahiere Inhalte
        content = self.content_extractor.extract_dates_and_amounts(metadata['body_text'])
        
        # Validiere
        validation = self.validator.validate_email(mail)
        
        return {
            'metadata': metadata,
            'attachments': [
                {
                    'filename': a['filename'],
                    'content_type': a['content_type'],
                    'size': a['size'],
                    'supported': a['supported'],
                }
                for a in attachments
            ],
            'saved_files': saved_files,
            'content': content,
            'validation': validation,
        }
