"""
llm.py
Core ML Model and LLM functionality for iPhone price prediction
Contains: Model loading, prediction functions, Gemini LLM integration
"""

import warnings
warnings.filterwarnings('ignore')

import joblib
import pickle
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
import os
import google.generativeai as genai


# ============================================================================
# CONFIGURATION
# ============================================================================
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LATEST_MODEL = 'models/gemini-2.5-flash'


# ============================================================================
# GLOBAL VARIABLES
# ============================================================================

model = None
scaler = None
encoders = None
le_model = None
le_source = None
le_day_name = None
le_month_name = None
le_time_of_day = None
feature_info = None
all_features = None
numerical_features = None
df = None
df_github = None
llm = None


# ============================================================================
# INITIALIZATION FUNCTIONS
# ============================================================================

def initialize_gemini():
    """Initialize Gemini LLM"""
    global llm

    genai.configure(api_key=GEMINI_API_KEY)

    try:
        llm = genai.GenerativeModel(LATEST_MODEL)
        test = llm.generate_content("Say hi")
        print(f"✅ Gemini LLM ready: {LATEST_MODEL}")
        return True
    except Exception as e:
        print(f"❌ LLM failed: {e}")
        llm = None
        return False


def load_ml_models():
    """Load ML model artifacts"""
    global model, scaler, encoders, le_model, le_source, feature_info
    global all_features, numerical_features, le_day_name, le_month_name, le_time_of_day

    print("📦 Loading ML model artifacts...")

    try:
        model = joblib.load('model/iphone_price_prediction_model_random_forest.pkl')
        scaler = joblib.load('model/price_prediction_scaler.pkl')

        with open('model/price_prediction_encoders.pkl', 'rb') as f:
            encoders = pickle.load(f)
        le_model = encoders['model_encoder']
        le_source = encoders['source_encoder']

        # Try loading additional encoders if they exist
        try:
            le_day_name = encoders.get('day_name_encoder', None)
            le_month_name = encoders.get('month_name_encoder', None)
            le_time_of_day = encoders.get('time_of_day_encoder', None)
        except:
            le_day_name = None
            le_month_name = None
            le_time_of_day = None

        with open('model/price_prediction_features.pkl', 'rb') as f:
            feature_info = pickle.load(f)
        all_features = feature_info['all_features']
        numerical_features = feature_info['numerical_features']

        print(f"✅ ML model loaded: {len(all_features)} features")
        print(f"✅ Encoders loaded")
        print(f"✅ Scaler loaded")
        return True
    except Exception as e:
        print(f"❌ Failed to load ML models: {e}")
        return False


def load_data():
    """Load synthetic and real data"""
    global df, df_github

    print("📊 Loading data...")

    try:
        # Load synthetic data
        df = pd.read_csv('model/enhanced_synthetic_dataset_with_timestamps.csv')
        df['Scraped_At'] = pd.to_datetime(df['Scraped_At'])
        print(f"✅ Loaded synthetic data: {len(df)} records")

        # Try to load real data from GitHub
        try:
            base_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
            db_path = os.path.join(base_dir, "competitor_tracker.db")

            if not os.path.exists(db_path):
                db_path = os.path.join(os.getcwd(), "competitor_tracker.db")
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                df_github = pd.read_sql_query("""
                    SELECT * FROM dynamic_info
                    WHERE model IN ('iPhone 15', 'iPhone 16', 'iPhone 17')
                """, conn)
                conn.close()

                if len(df_github) > 0:
                    real_df = df_github.rename(columns={
                        'model': 'Model',
                        'site': 'Source',
                        'price': 'Price',
                        'review_count': 'Review_Count',
                        'rating': 'Rating',
                        'url': 'URL'
                    })
                    if 'Scraped_At' not in real_df.columns:
                        real_df['Scraped_At'] = datetime.now()
                    else:
                        real_df['Scraped_At'] = pd.to_datetime(df_github['extracted_at'])

                    required_cols = ['Model', 'Source', 'Price', 'Rating', 'Review_Count', 'Scraped_At']
                    real_df = real_df[required_cols]

                    df = pd.concat([df, real_df], ignore_index=True)
                    print("🧾 df_github columns:", list(df_github.columns))

                    print(f"✅ Loaded real data: {len(df_github)} records")
                    print(f"✅ Combined dataset: {len(df)} total records")
                else:
                    print("⚠️ No real data found, using synthetic only")
            else:
                print(f"⚠️ Database file not found at {db_path}")
        except Exception as e:
            print(f"⚠️ Error loading real data: {e}")

        # Data cleanup
        cleanup_data()

        print(f"📊 Final dataset: {len(df)} records from {df['Model'].nunique()} models")
        return True
    except Exception as e:
        print(f"❌ Failed to load data: {e}")
        return False


def cleanup_data():
    """Clean and validate data"""
    global df

    print("🧹 Cleaning data...")

    # Clean Price column
    df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
    initial_rows = len(df)
    df = df.dropna(subset=['Price'])
    df = df[df['Price'] > 0]
    print(f" Removed {initial_rows - len(df)} invalid price records")

    # Ensure required columns
    required_cols = ['Model', 'Source', 'Price', 'Rating', 'Review_Count', 'Scraped_At']
    for col in required_cols:
        if col not in df.columns:
            if col == 'Rating':
                df[col] = 4.2
            elif col == 'Review_Count':
                df[col] = "Good product"
            else:
                df[col] = ""

    # Convert types
    df['Price'] = df['Price'].astype(float)
    df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce').fillna(4.2)
    df['Review_Count'] = df['Review_Count'].astype(str)
    df['Scraped_At'] = pd.to_datetime(df['Scraped_At'], errors='coerce')
    df = df.dropna(subset=['Scraped_At'])

    print("✅ Data cleanup complete")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

# def get_latest_current_price(model_name, source):
#     """
#     Get the LATEST price for a model on a specific source
#     Based on the most recent timestamp from GitHub database
#     """
#     global df_github

#     if df_github is None or len(df_github) == 0:
#         return None, None, None, None

#     # Filter for model and source
#     data = df_github[(df_github['model'] == model_name) & (df_github['site'] == source)].copy()

#     if len(data) == 0:
#         return None, None, None, None

#     # Sort by timestamp descending (most recent first)
#     data['extracted_at'] = pd.to_datetime(data['extracted_at'])
#     data = data.sort_values('extracted_at', ascending=False)

#     # Get the LATEST record
#     latest_record = data.iloc[0]

#     # Extract price as string, convert to float
#     price_str = str(latest_record['price']).replace(',', '').replace('₹', '')
#     price = float(price_str) if price_str else 0

#     timestamp = latest_record['extracted_at']
#     review = latest_record['Review_Count'][:50] if pd.notna(latest_record['Review_Count']) else ""
#     rating = float(latest_record['rating']) if pd.notna(latest_record['rating']) else 4.0

#     return price, timestamp, review, rating

def get_latest_current_price(model_name, source):
    """
    Get the LATEST price for a model on a specific source
    Based on the most recent timestamp from database
    """
    global df_github

    if df_github is None or len(df_github) == 0:
        return None, None, None, None

    # Filter data
    data = df_github[(df_github['model'] == model_name) & (df_github['site'] == source)].copy()
    if len(data) == 0:
        return None, None, None, None

    # 🧩 Fix: normalize timestamp column
    if 'extracted_at' in data.columns:
        data['timestamp'] = pd.to_datetime(data['extracted_at'])
    elif 'extracted_at' in data.columns:
        data['timestamp'] = pd.to_datetime(data['extracted_at'])
    else:
        print("⚠️ No timestamp column found in df_github!")
        return None, None, None, None

    # Sort by latest timestamp
    data = data.sort_values('timestamp', ascending=False)

    latest = data.iloc[0]
    price_str = str(latest['price']).replace(',', '').replace('₹', '')
    price = float(price_str) if price_str else 0

    timestamp = latest['timestamp']
    review_col = 'review_count' if 'review_count' in latest else None
    rating_col = 'rating' if 'rating' in latest else None

    review = (
        str(latest[review_col]) + " reviews"
        if review_col and pd.notna(latest[review_col])
        else "No reviews"
    )
    rating = float(latest['rating']) if pd.notna(latest['rating']) else 4.0
    print(f"🧩 [DEBUG] Current price loaded from DB → {model_name} | {source} | ₹{price} | {timestamp}")
    return price, timestamp, review, rating


# ============================================================================
# ML PREDICTION FUNCTIONS
# ============================================================================

def predict_iphone_price(model_name, source, rating=4.2, review_text="Good phone", target_date=None):
    """ML model price prediction"""
    if target_date is None:
        target_date = datetime.now()

    pred = pd.DataFrame({
        'Model': [model_name],
        'Source': [source],
        'Rating': [rating],
        'Review_Count': [review_text],
        'Scraped_At': [target_date]
    })

    pred['Year'] = pred['Scraped_At'].dt.year
    pred['Month'] = pred['Scraped_At'].dt.month
    pred['Day'] = pred['Scraped_At'].dt.day
    pred['Hour'] = pred['Scraped_At'].dt.hour
    pred['DayOfWeek'] = pred['Scraped_At'].dt.dayofweek
    pred['DayOfYear'] = pred['Scraped_At'].dt.dayofyear
    pred['WeekOfYear'] = pred['Scraped_At'].dt.isocalendar().week
    pred['Quarter'] = pred['Scraped_At'].dt.quarter
    pred['DaysAgo'] = (df['Scraped_At'].max() - pred['Scraped_At']).dt.days

    pred['IsWeekend'] = pred['DayOfWeek'].isin([5, 6]).astype(int)
    pred['IsHolidaySeason'] = pred['Month'].isin([11, 12]).astype(int)
    pred['IsLaunchSeason'] = pred['Month'].isin([9, 10]).astype(int)
    pred['IsSummerSeason'] = pred['Month'].isin([4, 5, 6]).astype(int)

    pred['ReviewLength'] = pred['Review_Count'].str.len()
    pred['ReviewWordCount'] = pred['Review_Count'].str.split().str.len()
    pred['HasExclamation'] = pred['Review_Count'].str.contains('!').astype(int)
    pred['HasQuestion'] = pred['Review_Count'].str.contains('r\?').astype(int)

    pred['Model_Encoded'] = le_model.transform([model_name])[0]
    pred['Source_Encoded'] = le_source.transform([source])[0]

    day_name = target_date.strftime('%A')
    month_name = target_date.strftime('%B')

    try:
        pred['DayName_Encoded'] = le_day_name.transform([day_name])[0] if le_day_name else 3
    except:
        pred['DayName_Encoded'] = 3

    try:
        pred['MonthName_Encoded'] = le_month_name.transform([month_name])[0] if le_month_name else pred['Month'].iloc[0]
    except:
        pred['MonthName_Encoded'] = pred['Month'].iloc[0]

    hour = pred['Hour'].iloc[0]
    if 6 <= hour < 12: tod = 'Morning'
    elif 12 <= hour < 18: tod = 'Afternoon'
    elif 18 <= hour < 22: tod = 'Evening'
    else: tod = 'Night'

    try:
        pred['TimeOfDay_Encoded'] = le_time_of_day.transform([tod])[0] if le_time_of_day else 1
    except:
        pred['TimeOfDay_Encoded'] = 1

    pred['Model_Source_Interaction'] = pred['Model_Encoded'] * pred['Source_Encoded']
    pred['Rating_Month_Interaction'] = pred['Rating'] * pred['Month']
    pred['Rating_ReviewLength_Interaction'] = pred['Rating'] * pred['ReviewLength']

    model_data = df[df['Model'] == model_name]
    pred['Model_Price_mean'] = model_data['Price'].mean()
    pred['Model_Price_std'] = model_data['Price'].std()
    pred['Model_Price_min'] = model_data['Price'].min()
    pred['Model_Price_max'] = model_data['Price'].max()
    pred['Model_Price_median'] = model_data['Price'].median()

    pred['Price_7Day_MA'] = model_data['Price'].tail(7).mean()
    pred['Price_30Day_MA'] = model_data['Price'].tail(30).mean()

    X_pred = pred[all_features].fillna(0)
    X_pred[numerical_features] = scaler.transform(X_pred[numerical_features])

    return model.predict(X_pred)[0]


# ============================================================================
# GEMINI LLM FUNCTIONS
# ============================================================================

def get_gemini_price_prediction(model_name, source, target_date):
    """Get price prediction from Gemini LLM"""
    if not llm:
        return None

    prompt = f"""Based on market trends for iPhone {model_name.split()[-1]},
    predict the most likely market price on {source} for {target_date.strftime('%B %d, %Y')} in Indian Rupees.
    Consider competitor pricing, demand, seasonality.
    Reply with ONLY a number (e.g., 75000)"""

    try:
        result = llm.generate_content(prompt)
        import re
        match = re.search(r'\d+', result.text.replace(',', ''))
        return float(match.group()) if match else None
    except:
        return None


def get_gemini_analysis(model_name, source, ml_price, gemini_price, current_price, target_date):
    """Get market analysis from Gemini LLM"""
    if not llm:
        return "Market analysis unavailable"

    prompt = f"""Analyze iPhone {model_name} pricing on {source} for {target_date.strftime('%B %d, %Y')}:
    - ML Model predicts: ₹{ml_price:,.0f}
    - Gemini market analysis suggests: ₹{gemini_price:,.0f}
    - Current latest market price: ₹{current_price:,.0f}

    Provide BRIEF 2-line analysis on:
    1. Market sentiment (bullish/bearish/neutral)
    2. Technical insight (overpriced/underpriced/fair)

    Format: "📊 Market: [sentiment]. 📈 Technical: [insight]" """

    try:
        result = llm.generate_content(prompt)
        return result.text[:200]
    except:
        return "Market analysis unavailable"


def get_gemini_optimal_price(model_name, source, ml_price, gemini_price, current_price):
    """Get optimal price recommendation from Gemini LLM"""
    if not llm:
        prices = [ml_price, current_price]
        if gemini_price and gemini_price > 0:
            prices.append(gemini_price)
        return float(np.mean(prices))

    prompt = f"""Given three price signals for {model_name} on {source}:
    - ML Model prediction: ₹{ml_price:,.0f}
    - Gemini market analysis: ₹{gemini_price:,.0f}
    - Current latest market price: ₹{current_price:,.0f}

    Recommend ONE optimal selling price that balances competitiveness and profitability.
    Reply ONLY with a single number (INR)."""

    try:
        result = llm.generate_content(prompt)
        import re
        match = re.search(r'\d+', result.text.replace(',', ''))
        if match:
            return float(match.group())
    except:
        pass

    prices = [ml_price, current_price]
    if gemini_price and gemini_price > 0:
        prices.append(gemini_price)
    return float(np.mean(prices))


# ============================================================================
# SAFE WRAPPER FUNCTIONS
# ============================================================================

def safe_predict_iphone_price(model_name, source, rating=4.2, review_text="Good phone", target_date=None):
    """Safe wrapper for ML prediction"""
    try:
        return predict_iphone_price(model_name, source, rating, review_text, target_date)
    except Exception as e:
        model_data = df[df['Model'] == model_name]
        if len(model_data) > 0:
            return float(model_data['Price'].mean())
        return 75000.0


def safe_get_gemini_price(model_name, source, target_date):
    """Safe wrapper for Gemini price prediction"""
    try:
        return get_gemini_price_prediction(model_name, source, target_date)
    except:
        return None


def safe_get_gemini_analysis(model_name, source, ml_price, gemini_price, current_price, target_date):
    """Safe wrapper for Gemini analysis"""
    try:
        return get_gemini_analysis(model_name, source, ml_price, gemini_price, current_price, target_date)
    except:
        return "📊 Market: Neutral. 📈 Technical: Fair value"


def safe_get_optimal_price(model_name, source, ml_price, gemini_price, current_price):
    """Safe wrapper for optimal price calculation"""
    try:
        return get_gemini_optimal_price(model_name, source, ml_price, gemini_price, current_price)
    except:
        prices = [ml_price, current_price]
        if gemini_price and gemini_price > 0:
            prices.append(gemini_price)
        return float(np.mean(prices))



# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_all():
    """Initialize all components"""
    print("="*80)
    print("🚀 INITIALIZING LLM MODULE")
    print("="*80)

    success = True
    success = success and load_ml_models()
    success = success and load_data()
    success = success and initialize_gemini()

    if success:
        print("="*80)
        print("✅ ALL COMPONENTS INITIALIZED SUCCESSFULLY")
        print("="*80)
    else:
        print("="*80)
        print("⚠️ SOME COMPONENTS FAILED TO INITIALIZE")
        print("="*80)

    return success


if __name__ == "__main__":
    initialize_all()