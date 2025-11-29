"""
Export Blueprint
API-Endpoints für Daten-Export (Excel, PDF)
"""
from flask import Blueprint, jsonify, request, send_file
from pathlib import Path
import logging
from typing import Dict, Any

export_bp = Blueprint('export', __name__, url_prefix='/api/export')
logger = logging.getLogger(__name__)


@export_bp.route('/excel', methods=['POST'])
def export_excel() -> tuple:
    """
    POST /api/export/excel
    Daten als Excel exportieren
    
    Request Body:
        category: Kategorie
        year: Jahr
        month: Monat (optional)
    
    Returns:
        Excel-Datei
    """
    try:
        from app.exporters import DataExporter
        from app.data_extractor import DataExtractor
        
        data = request.json or {}
        category = data.get('category', 'Rechnung')
        year = data.get('year')
        month = data.get('month')
        
        if not year:
            return jsonify({'error': 'Year required'}), 400
        
        # Get data
        extractor = DataExtractor()
        df = extractor.get_year_data(category, int(year))
        
        if df is None or df.empty:
            return jsonify({'error': 'No data found'}), 404
        
        # Filter by month if specified
        if month and 'date' in df.columns:
            df = df[df['date'].dt.month == int(month)]
        
        # Export
        exporter = DataExporter()
        export_path = exporter.export_to_excel(
            df,
            filename=f"{category}_{year}_{month if month else 'all'}.xlsx"
        )
        
        if not export_path or not Path(export_path).exists():
            return jsonify({'error': 'Export failed'}), 500
        
        return send_file(
            export_path,
            as_attachment=True,
            download_name=f"{category}_{year}.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logger.error(f"Error exporting Excel: {e}")
        return jsonify({'error': str(e)}), 500


@export_bp.route('/pdf', methods=['POST'])
def export_pdf() -> tuple:
    """
    POST /api/export/pdf
    Daten als PDF exportieren
    
    Request Body:
        category: Kategorie
        year: Jahr
        title: Titel (optional)
    
    Returns:
        PDF-Datei
    """
    try:
        from app.exporters import DataExporter
        from app.data_extractor import DataExtractor
        
        data = request.json or {}
        category = data.get('category', 'Rechnung')
        year = data.get('year')
        title = data.get('title', f'{category} Report {year}')
        
        if not year:
            return jsonify({'error': 'Year required'}), 400
        
        # Get data
        extractor = DataExtractor()
        df = extractor.get_year_data(category, int(year))
        
        if df is None or df.empty:
            return jsonify({'error': 'No data found'}), 404
        
        # Export
        exporter = DataExporter()
        export_path = exporter.export_to_pdf(
            df,
            filename=f"{category}_{year}.pdf",
            title=title
        )
        
        if not export_path or not Path(export_path).exists():
            return jsonify({'error': 'Export failed'}), 500
        
        return send_file(
            export_path,
            as_attachment=True,
            download_name=f"{category}_{year}.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Error exporting PDF: {e}")
        return jsonify({'error': str(e)}), 500


@export_bp.route('/csv', methods=['POST'])
def export_csv() -> tuple:
    """
    POST /api/export/csv
    Daten als CSV exportieren
    
    Request Body:
        category: Kategorie
        year: Jahr
    
    Returns:
        CSV-Datei
    """
    try:
        from app.data_extractor import DataExtractor
        
        data = request.json or {}
        category = data.get('category', 'Rechnung')
        year = data.get('year')
        
        if not year:
            return jsonify({'error': 'Year required'}), 400
        
        # Get data
        extractor = DataExtractor()
        df = extractor.get_year_data(category, int(year))
        
        if df is None or df.empty:
            return jsonify({'error': 'No data found'}), 404
        
        # Export
        from io import BytesIO
        output = BytesIO()
        df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)
        
        return send_file(
            output,
            as_attachment=True,
            download_name=f"{category}_{year}.csv",
            mimetype='text/csv'
        )
        
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        return jsonify({'error': str(e)}), 500
