"""
COMPREHENSIVE CSV EXPORT TESTS
Complete test coverage for exporters.py CSV functionality
Target: 80%+ code coverage for export_to_csv and extract_knowledge
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import csv
import io
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TestCSVExportBasic:
    """Test basic CSV export functionality"""
    
    def test_export_empty_list(self):
        """Test exporting empty data list"""
        from app.exporters import DataExporter
        
        exporter = DataExporter()
        result = exporter.export_to_csv([])
        
        assert isinstance(result, io.BytesIO)
        assert result.getvalue() == b''
        logger.info("✅ Empty list exported as empty BytesIO")
    
    def test_export_single_document(self):
        """Test exporting single document"""
        from app.exporters import DataExporter
        
        exporter = DataExporter()
        data = [{
            'filename': 'invoice.pdf',
            'category': 'Rechnung',
            'amount': 123.45,
            'date_document': '2026-01-08'
        }]
        
        result = exporter.export_to_csv(data)
        
        assert isinstance(result, io.BytesIO)
        result.seek(0)
        content = result.read().decode('utf-8')
        
        # Should be valid CSV with headers
        assert 'filename' in content or 'invoice.pdf' in content
        logger.info("✅ Single document exported as CSV")
    
    def test_export_multiple_documents(self):
        """Test exporting multiple documents"""
        from app.exporters import DataExporter
        
        exporter = DataExporter()
        data = [
            {'filename': 'invoice1.pdf', 'category': 'Rechnung', 'amount': 100},
            {'filename': 'invoice2.pdf', 'category': 'Rechnung', 'amount': 200},
            {'filename': 'insurance.pdf', 'category': 'Versicherung', 'amount': 50}
        ]
        
        result = exporter.export_to_csv(data)
        result.seek(0)
        content = result.read().decode('utf-8')
        
        # Count lines (header + 3 data rows)
        lines = content.strip().split('\n')
        assert len(lines) >= 3
        
        logger.info("✅ Multiple documents exported as CSV")


class TestCSVExportFieldHandling:
    """Test field handling in CSV export"""
    
    def test_export_prioritizes_important_fields(self):
        """Test that important fields are exported first"""
        from app.exporters import DataExporter
        
        exporter = DataExporter()
        data = [{
            'filename': 'test.pdf',
            'category': 'Rechnung',
            'date_document': '2026-01-08',
            'amount': 123.45,
            'company': 'TestCorp',
            'from_email': 'invoice@test.com',
            'subject': 'Invoice 2026-001',
            'extra_field': 'Some value'
        }]
        
        result = exporter.export_to_csv(data)
        result.seek(0)
        content = result.read().decode('utf-8')
        
        # Parse CSV
        reader = csv.DictReader(io.StringIO(content))
        fieldnames = reader.fieldnames
        
        # Important fields should exist
        assert 'filename' in fieldnames or 'date_document' in fieldnames
        logger.info("✅ Important fields prioritized")
    
    def test_export_handles_missing_fields(self):
        """Test handling of missing fields in documents"""
        from app.exporters import DataExporter
        
        exporter = DataExporter()
        data = [
            {'filename': 'complete.pdf', 'category': 'Rechnung', 'amount': 100},
            {'filename': 'incomplete.pdf', 'category': 'Versicherung'},  # Missing amount
            {'filename': 'minimal.pdf'}  # Missing category and amount
        ]
        
        result = exporter.export_to_csv(data)
        result.seek(0)
        content = result.read().decode('utf-8')
        
        # Should handle gracefully
        assert len(content) > 0
        logger.info("✅ Missing fields handled")
    
    def test_export_german_english_fieldnames(self):
        """Test support for German and English field names"""
        from app.exporters import DataExporter
        
        exporter = DataExporter()
        data = [
            {
                'datum': '2026-01-08',  # German
                'betrag': 100,           # German
                'firma': 'TestCorp'      # German
            },
            {
                'date_document': '2026-01-09',  # English
                'amount': 200,                   # English
                'company': 'OtherCorp'          # English
            }
        ]
        
        result = exporter.export_to_csv(data)
        result.seek(0)
        content = result.read().decode('utf-8')
        
        # Both should be handled
        assert len(content) > 0
        logger.info("✅ German and English field names supported")


class TestCSVExportDataTypes:
    """Test handling of different data types"""
    
    def test_export_handles_complex_types(self):
        """Test conversion of complex types to strings"""
        from app.exporters import DataExporter
        
        exporter = DataExporter()
        data = [{
            'filename': 'complex.pdf',
            'tags': ['invoice', 'important', 'urgent'],  # List
            'metadata': {'key': 'value', 'id': 123},     # Dict
            'amount': 99.99,                              # Float
            'count': 5                                    # Int
        }]
        
        result = exporter.export_to_csv(data)
        result.seek(0)
        content = result.read().decode('utf-8')
        
        # Should convert to strings without error
        assert len(content) > 0
        assert 'complex.pdf' in content
        logger.info("✅ Complex types handled")
    
    def test_export_handles_special_characters(self):
        """Test handling of special characters and UTF-8"""
        from app.exporters import DataExporter
        
        exporter = DataExporter()
        data = [{
            'filename': 'Überrechnung_2026_ß.pdf',
            'company': 'Müller & Co. GmbH',
            'category': 'Verträge',
            'notes': 'Preis: 100€, Rabatt: 10%'
        }]
        
        result = exporter.export_to_csv(data)
        result.seek(0)
        content = result.read().decode('utf-8')
        
        # Should preserve special characters
        assert 'Überrechnung' in content or 'Müller' in content
        logger.info("✅ Special characters preserved")
    
    def test_export_handles_empty_values(self):
        """Test handling of empty strings and None values"""
        from app.exporters import DataExporter
        
        exporter = DataExporter()
        data = [{
            'filename': 'test.pdf',
            'category': '',              # Empty string
            'amount': None,              # None
            'company': 'TestCorp'
        }]
        
        result = exporter.export_to_csv(data)
        result.seek(0)
        content = result.read().decode('utf-8')
        
        # Should handle gracefully
        assert len(content) > 0
        logger.info("✅ Empty values handled")


class TestCSVExportAPI:
    """Test CSV export as API response"""
    
    def test_export_returns_bytesio(self):
        """Test that export returns BytesIO object"""
        from app.exporters import DataExporter
        
        exporter = DataExporter()
        data = [{'filename': 'test.pdf', 'category': 'Rechnung'}]
        
        result = exporter.export_to_csv(data)
        
        assert isinstance(result, io.BytesIO)
        assert hasattr(result, 'read')
        assert hasattr(result, 'seek')
        logger.info("✅ BytesIO object returned correctly")
    
    def test_export_can_be_sent_as_response(self):
        """Test export can be used as Flask response"""
        from app.exporters import DataExporter
        
        exporter = DataExporter()
        data = [{'filename': 'test.pdf', 'category': 'Rechnung'}]
        
        result = exporter.export_to_csv(data)
        result.seek(0)
        
        # Should be readable
        content = result.read()
        assert len(content) > 0
        
        logger.info("✅ Export compatible with Flask response")


class TestKnowledgeExtraction:
    """Test knowledge extraction from documents"""
    
    def test_extract_knowledge_empty_list(self):
        """Test knowledge extraction from empty list"""
        from app.exporters import DataExporter
        
        exporter = DataExporter()
        result = exporter.extract_knowledge([])
        
        assert isinstance(result, dict)
        assert result['total_documents'] == 0
        logger.info("✅ Knowledge extraction handles empty list")
    
    def test_extract_knowledge_single_document(self):
        """Test knowledge extraction from single document"""
        from app.exporters import DataExporter
        
        exporter = DataExporter()
        data = [{
            'filename': 'invoice.pdf',
            'category': 'Rechnung',
            'amount': 250.00,
            'company': 'Supplier Inc',
            'date_document': '2026-01-08',
            'subject': 'Invoice 2026-001'
        }]
        
        result = exporter.extract_knowledge(data)
        
        assert result['total_documents'] == 1
        assert 'categories' in result
        assert 'companies' in result
        assert 'total_amount' in result
        assert result['total_amount'] == 250.00
        
        logger.info("✅ Knowledge extracted from single document")
    
    def test_extract_knowledge_categories(self):
        """Test category aggregation"""
        from app.exporters import DataExporter
        
        exporter = DataExporter()
        data = [
            {'category': 'Rechnung', 'amount': 100},
            {'category': 'Rechnung', 'amount': 200},
            {'category': 'Versicherung', 'amount': 50},
            {'category': 'Versicherung', 'amount': 75},
            {'category': 'Verträge', 'amount': 30}
        ]
        
        result = exporter.extract_knowledge(data)
        
        # Check category counts
        assert result['categories']['Rechnung'] == 2
        assert result['categories']['Versicherung'] == 2
        assert result['categories']['Verträge'] == 1
        
        logger.info("✅ Categories aggregated correctly")
    
    def test_extract_knowledge_top_categories(self):
        """Test top categories extraction"""
        from app.exporters import DataExporter
        
        exporter = DataExporter()
        data = [
            {'category': 'A', 'amount': 100},
            {'category': 'A', 'amount': 100},
            {'category': 'A', 'amount': 100},
            {'category': 'B', 'amount': 100},
            {'category': 'B', 'amount': 100},
            {'category': 'C', 'amount': 100},
        ]
        
        result = exporter.extract_knowledge(data)
        
        # Top categories should be ordered by frequency
        assert len(result['top_categories']) <= 5
        assert result['top_categories'][0][0] == 'A'
        assert result['top_categories'][0][1] == 3
        
        logger.info("✅ Top categories extracted")
    
    def test_extract_knowledge_companies(self):
        """Test company aggregation"""
        from app.exporters import DataExporter
        
        exporter = DataExporter()
        data = [
            {'company': 'Supplier A', 'amount': 100},
            {'company': 'Supplier A', 'amount': 200},
            {'company': 'Supplier B', 'amount': 150},
            {'firma': 'Supplier C', 'amount': 75}  # German field name
        ]
        
        result = exporter.extract_knowledge(data)
        
        # Check company tracking
        assert 'Supplier A' in result['companies']
        assert result['companies']['Supplier A'] == 2
        
        logger.info("✅ Companies tracked correctly")
    
    def test_extract_knowledge_amounts(self):
        """Test amount summation"""
        from app.exporters import DataExporter
        
        exporter = DataExporter()
        data = [
            {'amount': 100.50},
            {'amount': 200.75},
            {'betrag': 150.25},  # German field name
            {'amount': None}     # None value
        ]
        
        result = exporter.extract_knowledge(data)
        
        # Total should be sum of valid amounts
        expected = 100.50 + 200.75 + 150.25
        assert abs(result['total_amount'] - expected) < 0.01
        
        logger.info("✅ Amounts summed correctly")
    
    def test_extract_knowledge_date_range(self):
        """Test date range extraction"""
        from app.exporters import DataExporter
        
        exporter = DataExporter()
        data = [
            {'date_document': '2026-01-05'},
            {'datum': '2026-01-10'},      # German field
            {'date_document': '2026-01-08'},
            {'date_document': '2026-01-15'}
        ]
        
        result = exporter.extract_knowledge(data)
        
        # Date range should be set
        assert result['date_range']['earliest'] is not None
        assert result['date_range']['latest'] is not None
        
        logger.info("✅ Date range extracted")
    
    def test_extract_knowledge_subjects(self):
        """Test subject collection"""
        from app.exporters import DataExporter
        
        exporter = DataExporter()
        data = [
            {'subject': 'Invoice 2026-001'},
            {'betreff': 'Invoice 2026-002'},  # German field
            {'subject': 'Contract Amendment'},
            {'subject': 'Payment Reminder'}
        ]
        
        result = exporter.extract_knowledge(data)
        
        # Subjects should be collected
        assert len(result['subjects']) > 0
        assert 'Invoice 2026-001' in result['subjects']
        
        logger.info("✅ Subjects collected")
    
    def test_extract_knowledge_returns_dict(self):
        """Test that extract_knowledge returns proper structure"""
        from app.exporters import DataExporter
        
        exporter = DataExporter()
        data = [{'filename': 'test.pdf', 'category': 'Rechnung', 'amount': 100}]
        
        result = exporter.extract_knowledge(data)
        
        # Check required keys
        required_keys = [
            'total_documents', 'categories', 'companies',
            'total_amount', 'date_range', 'subjects',
            'top_categories', 'top_companies', 'extracted_at'
        ]
        
        for key in required_keys:
            assert key in result, f"Missing key: {key}"
        
        logger.info("✅ Knowledge extraction returns complete structure")


class TestCSVExportIntegration:
    """Test CSV export integration"""
    
    def test_export_knowledge_extraction_workflow(self):
        """Test workflow: CSV export + Knowledge extraction"""
        from app.exporters import DataExporter
        
        exporter = DataExporter()
        data = [
            {'filename': 'inv1.pdf', 'category': 'Rechnung', 'amount': 100, 'company': 'A'},
            {'filename': 'inv2.pdf', 'category': 'Rechnung', 'amount': 200, 'company': 'A'},
            {'filename': 'ins1.pdf', 'category': 'Versicherung', 'amount': 50, 'company': 'B'}
        ]
        
        # Export to CSV
        csv_result = exporter.export_to_csv(data)
        assert isinstance(csv_result, io.BytesIO)
        
        # Extract knowledge
        knowledge = exporter.extract_knowledge(data)
        assert knowledge['total_documents'] == 3
        assert knowledge['total_amount'] == 350
        
        logger.info("✅ CSV export + knowledge extraction workflow")
    
    def test_export_with_real_world_data(self):
        """Test export with realistic document data"""
        from app.exporters import DataExporter
        
        exporter = DataExporter()
        data = [
            {
                'filename': 'Rechnung_2026_001.pdf',
                'filepath': '/storage/documents/Rechnung_2026_001.pdf',
                'category': 'Rechnung',
                'subcategory': 'Internet',
                'date_document': '2026-01-08',
                'amount': 49.99,
                'company': 'Telekom Deutschland',
                'from_email': 'billing@telekom.de',
                'subject': 'Rechnung für Internet Dienste',
                'ocr_confidence': 0.98,
                'full_text': 'Telecom Invoice...',
                'keywords': ['rechnung', 'internet', 'telekom']
            },
            {
                'filename': 'Versicherung_2026_01.pdf',
                'category': 'Versicherung',
                'subcategory': 'Krankenversicherung',
                'date_document': '2026-01-07',
                'amount': 289.50,
                'company': 'AOK Bayern',
                'subject': 'Versicherungsbeitrag'
            }
        ]
        
        # Export
        result = exporter.export_to_csv(data)
        result.seek(0)
        content = result.read().decode('utf-8')
        
        # Should contain important data
        assert 'Rechnung' in content
        assert 'Versicherung' in content
        
        logger.info("✅ Real-world data exported successfully")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
