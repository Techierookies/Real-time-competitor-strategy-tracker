****iPhone Price Prediction ML Model****
**1. Overview**

This project details the development of a machine learning model to predict iPhone prices based on synthetic e-commerce data. The model leverages time-series features to capture market dynamics and pricing fluctuations from various retailers.

The primary notebook, iPhone_Price_Prediction_ML.ipynb, walks through the entire process from data loading and feature engineering to model training, evaluation, and finally, deployment in an interactive chatbot.

**2. Data Source**

Database: synthetic_competitor_tracker.db

Description: This database contains 2,500 synthetic records of iPhone 15, 16, and 17 models scraped from 'Amazon' and 'Flipkart'.

Key Column: Scraped_At (timestamp) is the most critical column, providing the time-series component for modeling.

**3. Feature Engineering**

To capture the time-dependent nature of pricing, several features were engineered:

Categorical Features: Model and Source (Amazon/Flipkart) were label-encoded.

Time-Series Features:

Time Elapsed: Number of days passed since the earliest record in the dataset. This was the most important feature.

Month, Day, DayOfWeek: Extracted from the Scraped_At timestamp.

**4. Modeling and Ensemble**

A sophisticated ensemble approach was used to achieve high accuracy. Four different regressor models were trained:

LightGBM

XGBoost

Gradient Boosting

Random Forest

These models were combined into a VotingRegressor (ensemble) to leverage their diverse strengths and produce a more stable and accurate prediction.

**5. Results**

The final ensemble model demonstrated strong predictive power, effectively capturing the complex, non-linear patterns in the pricing data.

Final $\text{R}^2$ Score: 0.7997

The trained model was saved to disk for future use.

Model File: iphone_price_predictor.joblib

**6. How to Use: Interactive Chatbot**
Run advanced_iphone_chatbot() to start the interactive session. Ask natural language queries like "price for iPhone 16 on Amazon" or "compare iPhone 17 on both" to get ML + Gemini LLM predictions with market analysis. Type 'update' to save predictions to a real-time dashboard, 'dashboard' to view all tracked predictions, or 'quit' to exit.

