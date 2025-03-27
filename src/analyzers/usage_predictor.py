from typing import List, Dict
import numpy as np
from sklearn.linear_model import LinearRegression

class UsagePredictor:
    """Predicts future usage based on historical data."""
    
    @staticmethod
    def predict(monthly_data: List[int]) -> Dict:
        """Predict future usage based on historical data."""
        if not monthly_data:
            return {'monthly': 0, 'annual': 0}
        
        X = np.array(range(len(monthly_data))).reshape(-1, 1)
        y = np.array(monthly_data)
        
        model = LinearRegression()
        model.fit(X, y)
        
        next_month = len(monthly_data)
        predicted_monthly = max(0, model.predict([[next_month]])[0])
        
        return {
            'monthly': round(predicted_monthly),
            'annual': round(predicted_monthly * 12)
        } 