"""
Data Exporter Module
Exportiert Daten als Excel oder PDF
"""

import logging
import pandas as pd
import io
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
