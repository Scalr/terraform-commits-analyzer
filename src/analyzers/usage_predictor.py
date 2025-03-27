from typing import List, Dict
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta

class UsagePredictor:
    """Predicts future usage based on historical data and growth factors."""
    
    def __init__(self, growth_rate: float = 0.1):
        """
        Initialize the predictor with a growth rate.
        
        Args:
            growth_rate: Expected monthly growth rate (default: 10%)
        """
        self.growth_rate = growth_rate
    
    def predict_usage(self, monthly_data: List[int], months_ahead: int = 1) -> Dict:
        """
        Predict future usage based on historical data and growth factors.
        
        Args:
            monthly_data: List of monthly commit counts
            months_ahead: Number of months to predict ahead
            
        Returns:
            Dictionary containing predictions and confidence metrics
        """
        if not monthly_data:
            return {
                'monthly': 0,
                'annual': 0,
                'confidence': 'low',
                'factors': {
                    'historical_trend': 0,
                    'growth_rate': 0,
                    'variance': 0
                }
            }
        
        # Calculate historical trend
        X = np.array(range(len(monthly_data))).reshape(-1, 1)
        y = np.array(monthly_data)
        
        model = LinearRegression()
        model.fit(X, y)
        historical_trend = model.coef_[0]
        
        # Calculate variance in historical data
        variance = np.var(y)
        
        # Calculate base prediction
        last_month = monthly_data[-1]
        base_prediction = last_month * (1 + self.growth_rate)
        
        # Adjust prediction based on historical trend
        trend_adjustment = historical_trend * months_ahead
        
        # Calculate confidence level
        confidence = self._calculate_confidence(variance, len(monthly_data))
        
        # Calculate final prediction with growth
        final_prediction = max(0, base_prediction + trend_adjustment)
        
        return {
            'monthly': round(final_prediction),
            'annual': round(final_prediction * 12),
            'confidence': confidence,
            'factors': {
                'historical_trend': round(historical_trend, 2),
                'growth_rate': self.growth_rate,
                'variance': round(variance, 2)
            }
        }
    
    @staticmethod
    def _calculate_confidence(variance: float, data_points: int) -> str:
        """Calculate confidence level based on data variance and sample size."""
        if data_points < 3:
            return 'low'
        
        # Normalize variance relative to mean
        normalized_variance = variance / (data_points ** 2)
        
        if normalized_variance < 0.1:
            return 'high'
        elif normalized_variance < 0.3:
            return 'medium'
        else:
            return 'low'
    
    @staticmethod
    def get_prediction_disclaimer() -> str:
        """Get a disclaimer about prediction accuracy and factors affecting usage."""
        return """
        Usage Prediction Disclaimer:
        ---------------------------
        The predicted usage is based on historical commit data and may not accurately reflect actual Terraform runs due to several factors:

        1. Multiple Workspaces:
           - One folder may be used by different workspaces
           - Each workspace may execute multiple runs
           - Some workspaces may be more active than others

        2. Various Trigger Methods:
           - Runs can be triggered by VCS commits
           - Manual runs via UI/API/CLI
           - Scheduled runs
           - External integrations

        3. Growth Factors:
           - Usage may start small and grow as more workspaces are added
           - New repositories may be onboarded
           - Team size and adoption may increase
           - Infrastructure complexity may change

        The prediction includes a growth rate assumption and confidence level based on historical data variance.
        Please use these predictions as a rough estimate and adjust based on your specific circumstances.
        """ 