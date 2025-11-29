"""
Unit Tests für EmailReceiver
Tests für Email-Integration und IMAP-Handling
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from app.email_receiver import EmailReceiver
import yaml
from pathlib import Path


@pytest.mark.unit
class TestEmailReceiverInit:
    """Tests für Initialisierung"""
    
    def test_init_with_config(self, test_config):
        """Test Initialisierung mit Konfiguration"""
        receiver = EmailReceiver(test_config)
        assert receiver.connection is None
        assert receiver.email_config is not None
        assert isinstance(receiver.upload_folder, str)
    
    def test_init_loads_config(self, test_config):
        """Test dass Konfiguration geladen wird"""
        receiver = EmailReceiver(test_config)
        assert 'enabled' in receiver.email_config
        assert 'host' in receiver.email_config


@pytest.mark.unit
class TestEmailReceiverConnect:
    """Tests für IMAP-Verbindung"""
    
    def test_connect_when_disabled(self, test_config):
        """Test Connect wenn Email disabled"""
        receiver = EmailReceiver(test_config)
        result = receiver.connect()
        assert result is False
    
    @patch('imaplib.IMAP4_SSL')
    def test_connect_success(self, mock_imap, temp_dir):
        """Test erfolgreiche IMAP-Verbindung"""
        # Erstelle Test-Config mit enabled Email
        config = {
            'system': {'storage': {'upload_folder': str(temp_dir / 'uploads')}},
            'email': {
                'enabled': True,
                'host': 'imap.test.com',
                'port': 993,
                'user': 'test@test.com',
                'password': 'testpass123'
            }
        }
        config_path = temp_dir / 'config.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        # Mock IMAP-Verbindung
        mock_connection = MagicMock()
        mock_imap.return_value = mock_connection
        
        receiver = EmailReceiver(str(config_path))
        result = receiver.connect()
        
        assert result is True
        mock_imap.assert_called_once_with('imap.test.com', 993)
        mock_connection.login.assert_called_once_with('test@test.com', 'testpass123')
    
    @patch('imaplib.IMAP4_SSL')
    def test_connect_auth_failure(self, mock_imap, temp_dir):
        """Test IMAP Auth-Fehler"""
        config = {
            'system': {'storage': {'upload_folder': str(temp_dir)}},
            'email': {
                'enabled': True,
                'host': 'imap.test.com',
                'user': 'test@test.com',
                'password': 'wrong_password'
            }
        }
        config_path = temp_dir / 'config.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        # Mock Auth-Fehler
        import imaplib
        mock_imap.side_effect = imaplib.IMAP4.error("Authentication failed")
        
        receiver = EmailReceiver(str(config_path))
        result = receiver.connect()
        
        assert result is False
    
    def test_connect_missing_credentials(self, temp_dir):
        """Test Connect mit fehlenden Credentials"""
        config = {
            'system': {'storage': {'upload_folder': str(temp_dir)}},
            'email': {
                'enabled': True,
                'host': 'imap.test.com',
                # user und password fehlen
            }
        }
        config_path = temp_dir / 'config.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        receiver = EmailReceiver(str(config_path))
        result = receiver.connect()
        
        assert result is False


@pytest.mark.unit
class TestEmailReceiverDisconnect:
    """Tests für Disconnect"""
    
    def test_disconnect_when_not_connected(self, test_config):
        """Test Disconnect ohne aktive Verbindung"""
        receiver = EmailReceiver(test_config)
        receiver.disconnect()  # Should not raise
        assert receiver.connection is None
    
    @patch('imaplib.IMAP4_SSL')
    def test_disconnect_closes_connection(self, mock_imap, temp_dir):
        """Test dass Disconnect Verbindung schließt"""
        config = {
            'system': {'storage': {'upload_folder': str(temp_dir)}},
            'email': {
                'enabled': True,
                'host': 'imap.test.com',
                'user': 'test@test.com',
                'password': 'test'
            }
        }
        config_path = temp_dir / 'config.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        mock_connection = MagicMock()
        mock_imap.return_value = mock_connection
        
        receiver = EmailReceiver(str(config_path))
        receiver.connect()
        receiver.disconnect()
        
        mock_connection.close.assert_called_once()
        mock_connection.logout.assert_called_once()
        assert receiver.connection is None


@pytest.mark.unit
class TestEmailReceiverFetchAttachments:
    """Tests für Attachment-Abruf"""
    
    def test_fetch_when_disabled(self, test_config):
        """Test Fetch wenn Email disabled"""
        receiver = EmailReceiver(test_config)
        result = receiver.fetch_attachments()
        assert result == []
    
    @patch('imaplib.IMAP4_SSL')
    def test_fetch_no_emails(self, mock_imap, temp_dir):
        """Test Fetch wenn keine Emails vorhanden"""
        config = {
            'system': {'storage': {'upload_folder': str(temp_dir / 'uploads')}},
            'email': {
                'enabled': True,
                'host': 'imap.test.com',
                'user': 'test@test.com',
                'password': 'test'
            }
        }
        (temp_dir / 'uploads').mkdir(parents=True, exist_ok=True)
        config_path = temp_dir / 'config.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        mock_connection = MagicMock()
        mock_connection.search.return_value = ('OK', [b''])
        mock_imap.return_value = mock_connection
        
        receiver = EmailReceiver(str(config_path))
        result = receiver.fetch_attachments()
        
        assert result == []


@pytest.mark.unit
class TestEmailReceiverHelpers:
    """Tests für Helper-Methoden"""
    
    def test_decode_subject_simple(self, test_config):
        """Test einfache Subject-Dekodierung"""
        receiver = EmailReceiver(test_config)
        result = receiver._decode_subject("Test Subject")
        assert result == "Test Subject"
    
    def test_decode_subject_none(self, test_config):
        """Test None Subject"""
        receiver = EmailReceiver(test_config)
        result = receiver._decode_subject(None)
        assert result == "(Kein Betreff)"
    
    def test_decode_subject_empty(self, test_config):
        """Test leerer Subject"""
        receiver = EmailReceiver(test_config)
        result = receiver._decode_subject("")
        assert result == "(Kein Betreff)"
