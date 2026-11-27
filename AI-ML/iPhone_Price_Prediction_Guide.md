
# iPhone Price Prediction Model - Usage Guide

Generated: 2025-10-31 07:02:24
Best Model: Random Forest
Model Accuracy: 79.9%
Average Error: ₹9,508

## Files Generated:
1. iphone_price_prediction_model_random_forest.pkl - Trained model
2. price_prediction_scaler.pkl - Feature scaler
3. price_prediction_encoders.pkl - Label encoders
4. price_prediction_features.pkl - Feature definitions
5. price_prediction_results.pkl - Performance results
6. iphone_price_forecasts_30days.csv - 30-day forecasts
7. price_prediction_scenarios.csv - Prediction scenarios

## Quick Start:

```python
import joblib
import pickle
import pandas as pd
from datetime import datetime

# Load model and components
model = joblib.load('iphone_price_prediction_model_random_forest.pkl')
scaler = joblib.load('price_prediction_scaler.pkl')

with open('price_prediction_encoders.pkl', 'rb') as f:
    encoders = pickle.load(f)

with open('price_prediction_features.pkl', 'rb') as f:
    feature_info = pickle.load(f)

# Make prediction
def predict_iphone_price(model_name, source, rating, review_text, target_date=None):
    if target_date is None:
        target_date = datetime.now()

    # Create feature vector (implement full feature engineering)
    # ... (use the predict_price function from this notebook)

    return predicted_price

# Example usage:
price = predict_iphone_price('iPhone 16', 'Amazon', 4.2, 'Great phone!', datetime.now())
print(f"Predicted price: ₹{price:,.0f}")
```

## Model Features (33 total):
Rating, ReviewLength, ReviewWordCount, Year, Month, Day, Hour, DayOfWeek, DayOfYear, WeekOfYear...

## Change Points Detected:

iPhone 15: 0 change points
iPhone 16: 0 change points
iPhone 17: 0 change points

## Performance Metrics:
- R² Score: 0.7991
- Mean Absolute Error: ₹9,508
- Root Mean Square Error: ₹11,865
- Mean Absolute Percentage Error: 9.27%

## Next Steps:
1. Load the saved model for production use
2. Implement real-time price monitoring
3. Set up automated retraining pipeline
4. Deploy as web service or API
5. Create price alerts based on predictions

Model is ready for production deployment!
