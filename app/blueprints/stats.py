"""
Statistics Blueprint
API-Endpoints für Statistiken und Analytics
Async & Pydantic Modernized
"""
from flask import Blueprint, jsonify, request
import logging
from typing import Dict, Any, Tuple
from datetime import datetime
from pydantic import ValidationError

from app.api_response import APIResponse, ErrorCodes
# We import schemas but might not use them for all complex nested responses yet
# unless we define comprehensive models for everything.
# For now, we focus on async conversion.

stats_bp = Blueprint('stats', __name__, url_prefix='/api/stats')
logger = logging.getLogger(__name__)


@stats_bp.route('/overview', methods=['GET'])
async def get_overview_stats() -> Tuple[Dict[str, Any], int]:
    """
    GET /api/stats/overview
    Übersichts-Statistiken
    """
    try:
        from app.database import Database
        from app.statistics_engine import StatisticsEngine
        from app.redis_client import RedisClient
        
        redis_client = RedisClient()
        cache_key = "stats:overview"
        
        # Try cache
        cached = redis_client.get(cache_key)
        if cached:
            return jsonify(cached), 200
        
        db = Database()
        stats_engine = StatisticsEngine()
        
        # These calls are synchronous, blocking the thread.
        # In a full async app, we'd await them or run in executor.
        stats = {
            'overview': db.get_overview_stats(),
            'trends': stats_engine.get_monthly_trends()
        }
        
        db.close()
        
        # Cache result (5 minutes)
        redis_client.set(cache_key, stats, expire=300)
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error getting overview stats: {e}")
        return jsonify({'error': str(e)}), 500


@stats_bp.route('/year/<int:year>', methods=['GET'])
async def get_year_stats(year: int) -> Tuple[Dict[str, Any], int]:
    """
    GET /api/stats/year/<year>
    Jahres-Statistiken
    """
    try:
        from app.database import Database
        from app.statistics_engine import StatisticsEngine
        from app.redis_client import RedisClient
        
        redis_client = RedisClient()
        cache_key = f"stats:year:{year}"
        
        # Try cache
        cached = redis_client.get(cache_key)
        if cached:
            return jsonify(cached), 200
        
        db = Database()
        stats_engine = StatisticsEngine()
        
        stats = {
            'year': year,
            'documents': db.get_year_stats(year),
            'monthly': stats_engine.get_monthly_breakdown(year)
        }
        
        db.close()
        
        # Cache result (1 hour)
        redis_client.set(cache_key, stats, expire=3600)
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error getting year stats: {e}")
        return jsonify({'error': str(e)}), 500


@stats_bp.route('/expenses', methods=['GET'])
async def get_expenses_analysis() -> Tuple[Dict[str, Any], int]:
    """
    GET /api/stats/expenses
    Ausgaben-Analyse
    """
    try:
        from app.data_extractor import DataExtractor
        from app.redis_client import RedisClient
        
        year = request.args.get('year')
        category = request.args.get('category', 'Rechnung')
        
        redis_client = RedisClient()
        cache_key = f"stats:expenses:{category}:{year or 'all'}"
        
        # Try cache
        cached = redis_client.get(cache_key)
        if cached:
            return jsonify(cached), 200
        
        extractor = DataExtractor()
        
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
        
        # Cache result (1 hour)
        redis_client.set(cache_key, analysis, expire=3600)
        
        return jsonify(analysis), 200
        
    except Exception as e:
        logger.error(f"Error getting expenses: {e}")
        return jsonify({'error': str(e)}), 500


@stats_bp.route('/trends/<int:year>', methods=['GET'])
async def get_monthly_trends(year: int) -> Tuple[Dict[str, Any], int]:
    """
    GET /api/stats/trends/<year>
    Monatliche Trends
    """
    try:
        from app.statistics_engine import StatisticsEngine
        from app.redis_client import RedisClient
        
        redis_client = RedisClient()
        cache_key = f"stats:trends:{year}"
        
        # Try cache
        cached = redis_client.get(cache_key)
        if cached:
            return jsonify(cached), 200
        
        stats_engine = StatisticsEngine()
        trends = stats_engine.get_monthly_trends(year)
        
        # Cache result (1 hour)
        redis_client.set(cache_key, trends, expire=3600)
        
        return jsonify(trends), 200
        
    except Exception as e:
        logger.error(f"Error getting trends: {e}")
        return jsonify({'error': str(e)}), 500


@stats_bp.route('/expenses/compare', methods=['GET'])
async def compare_expenses() -> Tuple[Dict[str, Any], int]:
    """
    GET /api/stats/expenses/compare
    Vergleicht Ausgaben zweier Jahre
    """
    try:
        year1 = int(request.args.get('year1', datetime.now().year - 1))
        year2 = int(request.args.get('year2', datetime.now().year))
        
        from app.statistics_engine import StatisticsEngine
        stats_engine = StatisticsEngine()
        
        comparison = stats_engine.get_expenses_comparison(year1, year2)
        return jsonify(comparison), 200
        
    except Exception as e:
        logger.error(f"Error comparing expenses: {e}")
        return jsonify({'error': str(e)}), 500


@stats_bp.route('/insurance/list', methods=['GET'])
async def list_insurances() -> Tuple[Dict[str, Any], int]:
    """
    GET /api/stats/insurance/list
    Liste aller Versicherungen
    """
    try:
        from app.database import Database
        from app.statistics_engine import StatisticsEngine
        
        db = Database()
        stats_engine = StatisticsEngine(db=db)
        
        insurances = stats_engine.get_insurance_list()
        db.close()
        
        return jsonify({'insurances': insurances}), 200
        
    except Exception as e:
        logger.error(f"Error listing insurances: {e}")
        return jsonify({'error': str(e)}), 500
