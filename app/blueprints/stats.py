"""
Statistics Blueprint
API-Endpoints für Statistiken und Analytics
"""
from flask import Blueprint, jsonify, request
import logging
from typing import Dict, Any

stats_bp = Blueprint('stats', __name__, url_prefix='/api/stats')
logger = logging.getLogger(__name__)


@stats_bp.route('/overview', methods=['GET'])
def get_overview_stats() -> tuple[Dict[str, Any], int]:
    """
    GET /api/stats/overview
    Übersichts-Statistiken
    
    Returns:
        JSON mit Gesamt-Statistiken
    """
    try:
        from app.database import Database
        from app.statistics_engine import StatisticsEngine
        
        db = Database()
        stats_engine = StatisticsEngine()
        
        stats = {
            'overview': db.get_overview_stats(),
            'trends': stats_engine.get_monthly_trends()
        }
        
        db.close()
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error getting overview stats: {e}")
        return jsonify({'error': str(e)}), 500


@stats_bp.route('/year/<int:year>', methods=['GET'])
def get_year_stats(year: int) -> tuple[Dict[str, Any], int]:
    """
    GET /api/stats/year/<year>
    Jahres-Statistiken
    
    Args:
        year: Jahr
    
    Returns:
        JSON mit Jahres-Statistiken
    """
    try:
        from app.database import Database
        from app.statistics_engine import StatisticsEngine
        
        db = Database()
        stats_engine = StatisticsEngine()
        
        stats = {
            'year': year,
            'documents': db.get_year_stats(year),
            'monthly': stats_engine.get_monthly_breakdown(year)
        }
        
        db.close()
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error getting year stats: {e}")
        return jsonify({'error': str(e)}), 500


@stats_bp.route('/expenses', methods=['GET'])
def get_expenses_analysis() -> tuple[Dict[str, Any], int]:
    """
    GET /api/stats/expenses
    Ausgaben-Analyse
    
    Query Parameters:
        year: Jahr (optional)
        category: Kategorie (optional)
    
    Returns:
        JSON mit Ausgaben-Analyse
    """
    try:
        from app.data_extractor import DataExtractor
        
        extractor = DataExtractor()
        
        year = request.args.get('year')
        category = request.args.get('category', 'Rechnung')
        
        if year:
            data = extractor.get_year_data(category, int(year))
        else:
            data = extractor.get_all_years_data(category)
        
        # Analyze data
        analysis = {
            'category': category,
            'year': year,
            'total_amount': 0,
            'count': 0
        }
        
        if data is not None:
            import pandas as pd
            if isinstance(data, pd.DataFrame):
                analysis['total_amount'] = float(data['amount'].sum()) if 'amount' in data.columns else 0
                analysis['count'] = len(data)
        
        return jsonify(analysis), 200
        
    except Exception as e:
        logger.error(f"Error getting expenses: {e}")
        return jsonify({'error': str(e)}), 500


@stats_bp.route('/trends/<int:year>', methods=['GET'])
def get_monthly_trends(year: int) -> tuple[Dict[str, Any], int]:
    """
    GET /api/stats/trends/<year>
    Monatliche Trends
    
    Args:
        year: Jahr
    
    Returns:
        JSON mit monatlichen Trends
    """
    try:
        from app.statistics_engine import StatisticsEngine
        
        stats_engine = StatisticsEngine()
        trends = stats_engine.get_monthly_trends(year)
        
        return jsonify(trends), 200
        
    except Exception as e:
        logger.error(f"Error getting trends: {e}")
        return jsonify({'error': str(e)}), 500
