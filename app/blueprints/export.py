"""
Export Blueprint
API-Endpoints für Daten-Export (Excel, PDF)
Async & Pydantic Modernized
"""
from flask import Blueprint, jsonify, request, send_file
from pathlib import Path
import logging
import asyncio
from typing import Dict, Any, Tuple

export_bp = Blueprint('export', __name__, url_prefix='/api/export')
logger = logging.getLogger(__name__)


@export_bp.route('/excel', methods=['POST'])
async def export_excel() -> Any:
    """
    POST /api/export/excel
    Daten als Excel exportieren
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
        
        # Run export logic in thread
        def run_export():
            # Get data
            extractor = DataExtractor()
            df = extractor.get_year_data(category, int(year))
            
            if df is None or df.empty:
                return None
            
            # Filter by month if specified
            if month and 'date' in df.columns:
                df = df[df['date'].dt.month == int(month)]
            
            # Export
            exporter = DataExporter()
            export_path = exporter.export_to_excel(
                df,
                filename=f"{category}_{year}_{month if month else 'all'}.xlsx"
            )
            return export_path

        export_path = await asyncio.to_thread(run_export)
        
        if export_path is None:
             return jsonify({'error': 'No data found'}), 404
        
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
async def export_pdf() -> Any:
    """
    POST /api/export/pdf
    Daten als PDF exportieren
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
        
        def run_export():
            # Get data
            extractor = DataExtractor()
            df = extractor.get_year_data(category, int(year))
            
            if df is None or df.empty:
                return None
            
            # Export
            exporter = DataExporter()
            export_path = exporter.export_to_pdf(
                df,
                filename=f"{category}_{year}.pdf",
                title=title
            )
            return export_path

        export_path = await asyncio.to_thread(run_export)
        
        if export_path is None:
            return jsonify({'error': 'No data found'}), 404
        
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
async def export_csv() -> Any:
    """
    POST /api/export/csv
    Daten als CSV exportieren
    """
    try:
        from app.data_extractor import DataExtractor
        from io import BytesIO
        
        data = request.json or {}
        category = data.get('category', 'Rechnung')
        year = data.get('year')
        
        if not year:
            return jsonify({'error': 'Year required'}), 400
        
        def run_export():
            # Get data
            extractor = DataExtractor()
            df = extractor.get_year_data(category, int(year))
            
            if df is None or df.empty:
                return None
            
            # Export
            output = BytesIO()
            df.to_csv(output, index=False, encoding='utf-8-sig')
            output.seek(0)
            return output

        output = await asyncio.to_thread(run_export)
        
        if output is None:
            return jsonify({'error': 'No data found'}), 404
        
        return send_file(
            output,
            as_attachment=True,
            download_name=f"{category}_{year}.csv",
            mimetype='text/csv'
        )
        
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        return jsonify({'error': str(e)}), 500
