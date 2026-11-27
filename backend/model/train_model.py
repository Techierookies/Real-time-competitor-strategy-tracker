# # backend/model/train_model.py

# import pandas as pd
# import numpy as np
# import joblib
# from sklearn.preprocessing import LabelEncoder
# from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor, VotingRegressor
# from xgboost import XGBRegressor
# from lightgbm import LGBMRegressor
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import r2_score
# import os

# # ----------------------------
# # Load dataset
# # ----------------------------
# DATA_PATH = "backend/model/enhanced_synthetic_dataset_with_timestamps.csv"

# print("📥 Loading dataset...")
# df = pd.read_csv(DATA_PATH)

# # ----------------------------
# # Encode categorical columns
# # ----------------------------
# le_model = LabelEncoder()
# le_source = LabelEncoder()

# df["Model_enc"] = le_model.fit_transform(df["Model"])
# df["Source_enc"] = le_source.fit_transform(df["Source"])

# # ----------------------------
# # Define features and target
# # ----------------------------
# # Only numeric columns used for prediction
# X = df[["storage", "ram", "battery", "refresh_rate", "chipset_score", "release_year"]]
# y = df["Price"]

# # ----------------------------
# # Train/Test Split
# # ----------------------------
# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# # ----------------------------
# # Train Ensemble Models
# # ----------------------------
# print("🧠 Training ensemble model...")

# models = [
#     ("xgb", XGBRegressor(n_estimators=100, random_state=42, verbosity=0)),
#     ("lgbm", LGBMRegressor(n_estimators=100, random_state=42)),
#     ("gbr", GradientBoostingRegressor(n_estimators=100, random_state=42)),
#     ("rf", RandomForestRegressor(n_estimators=100, random_state=42)),
# ]

# voting_model = VotingRegressor(estimators=models)
# voting_model.fit(X_train, y_train)

# # ----------------------------
# # Evaluate Model
# # ----------------------------
# y_pred = voting_model.predict(X_test)
# r2 = r2_score(y_test, y_pred)
# print(f"✅ Model trained successfully with R² Score: {r2:.4f}")

# # ----------------------------
# # Save Model + Encoders
# # ----------------------------
# SAVE_PATH = "backend/model/iphone_price_predictor.joblib"

# joblib.dump({
#     "model": voting_model,
#     "le_model": le_model,
#     "le_source": le_source
# }, SAVE_PATH)

# print(f"💾 Model and encoders saved at '{SAVE_PATH}'")

# # ----------------------------
# # Optional: Generate sample prediction data (for Admin Dashboard preview)
# # ----------------------------
# sample_preds = []

# for i in range(5):  # generate few example rows
#     sample_data = X.sample(1).values[0]
#     ml_pred = voting_model.predict([sample_data])[0]
#     gemini_pred = round(ml_pred * 0.85, 2)
#     optimal_price = round((ml_pred + gemini_pred) / 2, 2)

#     sample_preds.append({
#         "DateTime": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
#         "Model": df.iloc[i]["Model"],
#         "Source": df.iloc[i]["Source"],
#         "ML_Predicted": f"₹{round(ml_pred, 2)}",
#         "Gemini_Predicted": f"₹{gemini_pred}",
#         "Current_Price": f"₹{round(ml_pred * 0.95, 2)}",
#         "Current_Timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
#         "Current_Rating": 4.3,
#         "Optimal_Price": f"₹{optimal_price}",
#         "Analysis": "📊 Market: Neutral. 📈 Technical: Stable",
#         "Review": "Smooth performance and great display."
#     })

# # Save sample predictions for admin dashboard mock
# pd.DataFrame(sample_preds).to_csv("backend/model/price_prediction_results.csv", index=False)
# print("📊 Sample results saved to 'backend/model/price_prediction_results.csv'")
