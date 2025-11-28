"""
Statistics Engine - Erweiterte Statistiken
Monatliche Trends, Budget-Tracking, Prognosen
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import yaml
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import json

logger = logging.getLogger(__name__)


class StatisticsEngine:
    """Engine für erweiterte Statistiken"""
    
    def __init__(self, config_path: str = 'config.yaml', db=None):
        """
        Initialisiert Statistics Engine
        
        Args:
            config_path: Pfad zur Konfiguration
            db: Database-Instanz
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.db = db
        self.data_path = Path(self.config['system']['storage']['data_path'])
    
    def get_monthly_trends(self, year: int) -> Dict:
        """
        Analysiert monatliche Ausgaben-Trends
        
        Args:
            year: Jahr
            
        Returns:
            Dictionary mit monatlichen Daten
        """
        csv_path = self.data_path / str(year) / 'rechnungen_data.csv'
        
        if not csv_path.exists():
            return {
                'year': year,
                'months': [],
                'total_by_month': {},
                'categories_by_month': {}
            }
        
        try:
            df = pd.read_csv(csv_path)
            
            # Parse Datumsangaben
            df['datum'] = pd.to_datetime(df['datum'], errors='coerce')
            df['month'] = df['datum'].dt.month
            
            # Gruppiere nach Monat
            monthly_totals = df.groupby('month')['betrag'].sum().to_dict()
            
            # Gruppiere nach Monat und Kategorie
            monthly_categories = {}
            for month in range(1, 13):
                month_data = df[df['month'] == month]
                category_sums = month_data.groupby('kategorie')['betrag'].sum().to_dict()
                monthly_categories[month] = category_sums
            
            return {
                'year': year,
                'months': list(range(1, 13)),
                'total_by_month': monthly_totals,
                'categories_by_month': monthly_categories
            }
            
        except Exception as e:
            logger.error(f"Fehler bei monatlichen Trends: {e}")
            return {
                'year': year,
                'months': [],
                'total_by_month': {},
                'categories_by_month': {}
            }
    
    def calculate_budget_status(self, category: str, year: int, month: int) -> Dict:
        """
        Vergleicht Budget mit tatsächlichen Ausgaben
        
        Args:
            category: Kategorie
            year: Jahr
            month: Monat (1-12)
            
        Returns:
            Budget-Status
        """
        # Hole Budget aus DB
        budget_amount = self.db.get_budget(category, f"{year}-{month:02d}") if self.db else None
        
        # Hole tatsächliche Ausgaben
        csv_path = self.data_path / str(year) / 'rechnungen_data.csv'
        
        actual_amount = 0
        if csv_path.exists():
            try:
                df = pd.read_csv(csv_path)
                df['datum'] = pd.to_datetime(df['datum'], errors='coerce')
                
                # Filter nach Monat und Kategorie
                month_data = df[
                    (df['datum'].dt.month == month) & 
                    (df['kategorie'] == category)
                ]
                
                actual_amount = month_data['betrag'].sum()
                
            except Exception as e:
                logger.error(f"Fehler beim Lesen der Ausgaben: {e}")
        
        # Berechne Status
        if budget_amount:
            difference = budget_amount - actual_amount
            percentage = (actual_amount / budget_amount * 100) if budget_amount > 0 else 0
            status = 'ok' if actual_amount <= budget_amount else 'over'
        else:
            difference = None
            percentage = None
            status = 'no_budget'
        
        return {
            'category': category,
            'year': year,
            'month': month,
            'budget': budget_amount,
            'actual': float(actual_amount),
            'difference': float(difference) if difference is not None else None,
            'percentage': float(percentage) if percentage is not None else None,
            'status': status
        }
    
    def predict_expenses(self, category: str, months_ahead: int = 3) -> Dict:
        """
        Prognostiziert zukünftige Ausgaben mit linearer Regression
        
        Args:
            category: Kategorie
            months_ahead: Anzahl Monate in die Zukunft
            
        Returns:
            Prognose-Daten
        """
        # Sammle historische Daten (letzte 12 Monate)
        historical_data = []
        current_date = datetime.now()
        
        for i in range(12, 0, -1):
            target_date = current_date - timedelta(days=30 * i)
            year = target_date.year
            month = target_date.month
            
            csv_path = self.data_path / str(year) / 'rechnungen_data.csv'
            
            if csv_path.exists():
                try:
                    df = pd.read_csv(csv_path)
                    df['datum'] = pd.to_datetime(df['datum'], errors='coerce')
                    
                    month_data = df[
                        (df['datum'].dt.month == month) & 
                        (df['kategorie'] == category)
                    ]
                    
                    amount = month_data['betrag'].sum()
                    historical_data.append({
                        'month_index': 12 - i,
                        'amount': float(amount)
                    })
                    
                except Exception as e:
                    logger.warning(f"Fehler beim Lesen von {csv_path}: {e}")
        
        if len(historical_data) < 3:
            return {
                'category': category,
                'error': 'Nicht genügend historische Daten für Prognose'
            }
        
        # Bereite Daten für Regression vor
        X = np.array([d['month_index'] for d in historical_data]).reshape(-1, 1)
        y = np.array([d['amount'] for d in historical_data])
        
        # Trainiere lineares Regressionsmodell
        model = LinearRegression()
        model.fit(X, y)
        
        # Mache Prognosen
        last_index = X[-1][0]
        future_X = np.array([last_index + i for i in range(1, months_ahead + 1)]).reshape(-1, 1)
        predictions = model.predict(future_X)
        
        # Berechne Konfidenzintervall (vereinfacht)
        residuals = y - model.predict(X)
        std_error = np.std(residuals)
        
        prediction_results = []
        for i, pred in enumerate(predictions):
            future_date = current_date + timedelta(days=30 * (i + 1))
            prediction_results.append({
                'month': future_date.month,
                'year': future_date.year,
                'predicted_amount': max(0, float(pred)),  # Keine negativen Prognosen
                'confidence_lower': max(0, float(pred - 1.96 * std_error)),
                'confidence_upper': float(pred + 1.96 * std_error)
            })
        
        return {
            'category': category,
            'historical_data': historical_data,
            'predictions': prediction_results,
            'model_score': float(model.score(X, y))
        }
    
    def get_category_breakdown(self, year: int, month: Optional[int] = None) -> Dict:
        """
        Detaillierte Kategorie-Analyse
        
        Args:
            year: Jahr
            month: Monat (optional, None = ganzes Jahr)
            
        Returns:
            Kategorie-Breakdown
        """
        csv_path = self.data_path / str(year) / 'rechnungen_data.csv'
        
        if not csv_path.exists():
            return {
                'year': year,
                'month': month,
                'categories': {},
                'total': 0
            }
        
        try:
            df = pd.read_csv(csv_path)
            df['datum'] = pd.to_datetime(df['datum'], errors='coerce')
            
            # Filter nach Monat wenn angegeben
            if month:
                df = df[df['datum'].dt.month == month]
            
            # Gruppiere nach Kategorie
            category_data = {}
            for category in df['kategorie'].unique():
                cat_data = df[df['kategorie'] == category]
                category_data[category] = {
                    'total': float(cat_data['betrag'].sum()),
                    'count': int(len(cat_data)),
                    'average': float(cat_data['betrag'].mean()),
                    'min': float(cat_data['betrag'].min()),
                    'max': float(cat_data['betrag'].max())
                }
            
            total = float(df['betrag'].sum())
            
            return {
                'year': year,
                'month': month,
                'categories': category_data,
                'total': total
            }
            
        except Exception as e:
            logger.error(f"Fehler bei Kategorie-Breakdown: {e}")
            return {
                'year': year,
                'month': month,
                'categories': {},
                'total': 0
            }


def main():
    """Test"""
    logging.basicConfig(level=logging.INFO)
    
    from app.database import Database
    db = Database()
    
    engine = StatisticsEngine(db=db)
    
    # Test monatliche Trends
    trends = engine.get_monthly_trends(2024)
    print(f"Monatliche Trends: {json.dumps(trends, indent=2)}")
    
    # Test Prognose
    prediction = engine.predict_expenses('Strom', months_ahead=3)
    print(f"Prognose: {json.dumps(prediction, indent=2)}")


if __name__ == "__main__":
    main()
