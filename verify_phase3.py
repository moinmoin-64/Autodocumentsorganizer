"""
Verification Script for Phase 3 Features
"""
import unittest
import os
import sys
from pathlib import Path
import json
from datetime import datetime

# Add app to path
sys.path.append(str(Path(__file__).parent))

from app.auto_tagger import AutoTagger
from app.exporters import DataExporter
from app.database import Database
from app.audit import log_action

class TestPhase3(unittest.TestCase):
    def setUp(self):
        self.db = Database('config.yaml')
        
    def test_auto_tagger(self):
        print("\nTesting Auto-Tagging...")
        tagger = AutoTagger()
        text = "Rechnung vom 01.01.2025 über 50€ für Tankstelle Aral. Bitte zahlen."
        tags = tagger.generate_tags(text, "Rechnungen")
        print(f"Tags: {tags}")
        self.assertIn("cat:rechnungen", tags)
        self.assertIn("auto", tags) # Tankstelle -> auto
        self.assertIn("year:2025", tags)
        
    def test_export(self):
        print("\nTesting Export...")
        exporter = DataExporter()
        data = [{
            'date_document': '2025-01-01',
            'category': 'Test',
            'amount': 123.45,
            'company': 'Test Corp'
        }]
        
        # Excel
        excel = exporter.export_to_excel(data)
        self.assertTrue(excel.getbuffer().nbytes > 0)
        print("Excel export successful")
        
        # PDF
        pdf = exporter.export_to_pdf(data)
        self.assertTrue(pdf.getbuffer().nbytes > 0)
        print("PDF export successful")
        
    def test_audit_log(self):
        print("\nTesting Audit Log...")
        # Log action
        self.db.log_audit_event("test_user", "test_action", "123", {"foo": "bar"})
        
        # Check DB
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audit_log WHERE action = 'test_action' ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(row)
        self.assertEqual(row['user_id'], "test_user")
        print("Audit log entry verified")

if __name__ == '__main__':
    unittest.main()
