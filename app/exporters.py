"""
Data Exporter Module
Exportiert Daten als Excel, PDF oder CSV
"""

import logging
import pandas as pd
import io
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# ReportLab für PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

logger = logging.getLogger(__name__)

class DataExporter:
    """Exportiert Daten in verschiedene Formate"""
    
    # Wichtige Felder für den Export
    EXPORT_FIELDS = [
        'date_document', 'datum', 'filename', 'category', 
        'amount', 'betrag', 'company', 'firma', 'from_email', 'subject'
    ]
    
    def __init__(self):
        pass

    def export_to_excel(self, data: List[Dict], filename: str = "export.xlsx") -> io.BytesIO:
        """
        Exportiert Daten nach Excel
        Returns: BytesIO Object
        """
        output = io.BytesIO()
        
        try:
            df = pd.DataFrame(data)
            
            # Excel Writer
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Dokumente', index=False)
                
                # Auto-adjust columns
                worksheet = writer.sheets['Dokumente']
                for i, col in enumerate(df.columns):
                    max_len = max(
                        df[col].astype(str).map(len).max(),
                        len(str(col))
                    ) + 2
                    worksheet.set_column(i, i, max_len)
                    
            output.seek(0)
            return output
            
        except Exception as e:
            logger.error(f"Excel Export Fehler: {e}")
            raise

    def export_to_pdf(self, data: List[Dict], title: str = "Dokumenten-Bericht") -> io.BytesIO:
        """
        Exportiert Daten als PDF Tabelle
        Returns: BytesIO Object
        """
        output = io.BytesIO()
        
        try:
            doc = SimpleDocTemplate(output, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()
            
            # Titel
            elements.append(Paragraph(title, styles['Title']))
            elements.append(Paragraph(f"Erstellt am: {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles['Normal']))
            elements.append(Spacer(1, 20))
            
            if not data:
                elements.append(Paragraph("Keine Daten vorhanden.", styles['Normal']))
                doc.build(elements)
                output.seek(0)
                return output
                
            # Tabelle vorbereiten
            # Wir nehmen nur wichtige Spalten für PDF, sonst passt es nicht
            headers = ['Datum', 'Kategorie', 'Betrag', 'Firma/Betreff']
            table_data = [headers]
            
            for item in data:
                row = [
                    item.get('date_document', '') or item.get('datum', ''),
                    item.get('category', ''),
                    f"{item.get('amount', 0):.2f} €" if item.get('amount') else "",
                    item.get('company', '') or item.get('firma', '') or item.get('filename', '')[:30]
                ]
                table_data.append(row)
                
            # Tabelle erstellen
            t = Table(table_data)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(t)
            doc.build(elements)
            
            output.seek(0)
            return output
            
        except Exception as e:
            logger.error(f"PDF Export Fehler: {e}")
            raise

    def export_to_csv(self, data: List[Dict], filename: str = "export.csv") -> io.BytesIO:
        """
        Exportiert Daten als CSV (für Knowledge-Base)
        
        Args:
            data: Liste von Dokumenten
            filename: Ausgabedateiname
            
        Returns:
            BytesIO Object mit CSV-Daten
        """
        output = io.BytesIO()
        
        try:
            # Wenn keine Daten, leere CSV zurückgeben
            if not data:
                return output
            
            # Bestimme Spalten aus Daten
            all_keys = set()
            for item in data:
                all_keys.update(item.keys())
            
            # Sortiere Spalten (wichtige zuerst)
            fieldnames = []
            for field in self.EXPORT_FIELDS:
                if field in all_keys:
                    fieldnames.append(field)
            
            # Restliche Spalten
            for field in sorted(all_keys):
                if field not in fieldnames:
                    fieldnames.append(field)
            
            # Schreibe CSV
            text_wrapper = io.TextIOWrapper(output, encoding='utf-8', newline='')
            writer = csv.DictWriter(text_wrapper, fieldnames=fieldnames)
            
            writer.writeheader()
            for item in data:
                # Konvertiere komplexe Datentypen zu Strings
                row = {}
                for key in fieldnames:
                    value = item.get(key, '')
                    if isinstance(value, (list, dict)):
                        value = str(value)
                    row[key] = value
                writer.writerow(row)
            
            text_wrapper.flush()
            output.seek(0)
            
            logger.info(f"✅ CSV Export erfolgreich: {len(data)} Zeilen")
            return output
            
        except Exception as e:
            logger.error(f"CSV Export Fehler: {e}")
            raise
    
    def extract_knowledge(self, data: List[Dict]) -> Dict[str, Any]:
        """
        Extrahiert Wissensinformationen aus Dokumenten
        
        Args:
            data: Liste von Dokumenten
            
        Returns:
            Dict mit extrahierten Wissenselementen
        """
        try:
            knowledge = {
                'total_documents': len(data),
                'categories': {},
                'companies': {},
                'total_amount': 0,
                'date_range': {
                    'earliest': None,
                    'latest': None,
                },
                'subjects': [],
                'extracted_at': datetime.now().isoformat(),
            }
            
            for item in data:
                # Kategorien zählen
                category = item.get('category', 'Unbekannt')
                knowledge['categories'][category] = knowledge['categories'].get(category, 0) + 1
                
                # Firmen/Kontakte sammeln
                company = item.get('company') or item.get('firma', '')
                if company:
                    knowledge['companies'][company] = knowledge['companies'].get(company, 0) + 1
                
                # Beträge summieren
                amount = item.get('amount') or item.get('betrag', 0)
                if isinstance(amount, (int, float)):
                    knowledge['total_amount'] += amount
                
                # Datum tracking
                date_str = item.get('date_document') or item.get('datum', '')
                if date_str:
                    if not knowledge['date_range']['earliest'] or date_str < knowledge['date_range']['earliest']:
                        knowledge['date_range']['earliest'] = date_str
                    if not knowledge['date_range']['latest'] or date_str > knowledge['date_range']['latest']:
                        knowledge['date_range']['latest'] = date_str
                
                # Subjekte sammeln
                subject = item.get('subject') or item.get('betreff', '')
                if subject:
                    knowledge['subjects'].append(subject)
            
            # Top Kategorien
            knowledge['top_categories'] = sorted(
                knowledge['categories'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            # Top Firmen
            knowledge['top_companies'] = sorted(
                knowledge['companies'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            logger.info(f"✅ Wissen extrahiert: {knowledge['total_documents']} Dokumente, {len(knowledge['companies'])} Firmen")
            return knowledge
            
        except Exception as e:
            logger.error(f"Knowledge Extraction Fehler: {e}")
            return {'error': str(e)}
