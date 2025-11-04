"""
chatbot.py
Interactive chatbot interface for iPhone price prediction
Uses llm.py for ML and LLM functionality
"""

import pandas as pd
from datetime import datetime
import re

# Import all functions from llm.py
from model.llm import (
    initialize_all,
    safe_predict_iphone_price,
    safe_get_gemini_price,
    safe_get_gemini_analysis,
    safe_get_optimal_price,
    get_latest_current_price
)


# ============================================================================
# DASHBOARD MANAGEMENT
# ============================================================================

# Initialize dashboard
dashboard = pd.DataFrame(columns=[
    'DateTime', 'Model', 'Source', 'ML_Predicted', 'Gemini_Predicted',
    'Current_Price', 'Current_Timestamp', 'Current_Rating', 'Optimal_Price', 'Analysis', 'Review'
])

all_predictions = []


def update_dashboard_batch(model_name, predictions_list):
    """Update dashboard with batch predictions"""
    global dashboard

    for pred in predictions_list:
        source = pred['source']
        dashboard = dashboard[~((dashboard['Model'] == model_name) & (dashboard['Source'] == source))]

        new_row = pd.DataFrame({
            'DateTime': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            'Model': [model_name],
            'Source': [source],
            'ML_Predicted': [f"₹{pred['ml_pred']:,.0f}"],
            'Gemini_Predicted': [f"₹{pred['gemini_pred']:,.0f}" if pred['gemini_pred'] else "N/A"],
            'Current_Price': [f"₹{pred['current_price']:,.0f}"],
            'Current_Timestamp': [pred['current_timestamp'].strftime('%Y-%m-%d %H:%M:%S')],
            'Current_Rating': [f"{pred['current_rating']}"],
            'Optimal_Price': [f"₹{pred['optimal_price']:,.0f}"],
            'Analysis': [pred['analysis'][:80]],
            'Review': [pred['review'][:40]]
        })

        dashboard = pd.concat([dashboard, new_row], ignore_index=True)

    return dashboard


# ============================================================================
# INPUT PARSING FUNCTIONS
# ============================================================================

def parse_model_name(user_input):
    """Extract iPhone model from user input"""
    user_lower = user_input.lower()

    if 'iphone 17' in user_lower or 'iphone17' in user_lower or 'model 17' in user_lower or '17' in user_lower.split():
        return 'iPhone 17'
    elif 'iphone 16' in user_lower or 'iphone16' in user_lower or 'model 16' in user_lower or '16' in user_lower.split():
        return 'iPhone 16'
    elif 'iphone 15' in user_lower or 'iphone15' in user_lower or 'model 15' in user_lower or '15' in user_lower.split():
        return 'iPhone 15'

    return None


def parse_sources(user_input):
    """Extract source platforms from user input"""
    user_lower = user_input.lower()
    sources = []

    if 'both' in user_lower or ('amazon' in user_lower and 'flipkart' in user_lower):
        sources = ['Amazon', 'Flipkart']
    elif 'amazon' in user_lower:
        sources = ['Amazon']
    elif 'flipkart' in user_lower:
        sources = ['Flipkart']

    return sources


def parse_date(user_input):
    """Extract target date from user input"""
    user_lower = user_input.lower()
    target_date = datetime.now()

    date_match = re.search(r'(\d{1,2})\s*(st|nd|rd|th)?\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', user_lower)
    if date_match:
        day = int(date_match.group(1))
        month_str = date_match.group(3)
        month_map = {'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,'jul':7,'aug':8,'sep':9,'oct':10,'nov':11,'dec':12}
        month = month_map.get(month_str, datetime.now().month)
        year = 2025
        try:
            target_date = datetime(year, month, day, 12, 0)
        except:
            target_date = datetime.now()

    return target_date


# ============================================================================
# PREDICTION FUNCTIONS
# ============================================================================

def get_single_prediction(model_name, source, target_date):
    """Get prediction for single model and source"""
    ml_pred = safe_predict_iphone_price(model_name, source, target_date=target_date)
    gemini_pred = safe_get_gemini_price(model_name, source, target_date)
    current_price, current_timestamp, review, current_rating = get_latest_current_price(model_name, source)

    if current_price is None:
        current_price = ml_pred
        current_timestamp = datetime.now()
        review = ""
        current_rating = 4.0

    optimal_price = safe_get_optimal_price(model_name, source, ml_pred, gemini_pred, current_price)
    analysis = safe_get_gemini_analysis(model_name, source, ml_pred, gemini_pred, current_price, target_date)

    return {
        'model': model_name,
        'source': source,
        'ml_pred': ml_pred,
        'gemini_pred': gemini_pred,
        'current_price': current_price,
        'current_timestamp': current_timestamp,
        'current_rating': current_rating,
        'optimal_price': optimal_price,
        'analysis': analysis,
        'review': review
    }


def format_prediction_response(pred, target_date):
    """Format prediction into readable response"""
    response = f"\n{'='*100}\n"
    response += f"🎯 **PRICE ANALYSIS - {pred['model']} on {pred['source']}**\n\n"
    response += f"📅 **Prediction Timestamp:** {target_date.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    response += f"📊 **PREDICTIONS:**\n"
    response += f" 🤖 ML Model: ₹{pred['ml_pred']:,.0f}\n"
    response += f" 🧠 Gemini LLM: ₹{pred['gemini_pred']:,.0f}\n" if pred['gemini_pred'] else ""
    response += f" 💰 Current Market (Latest): ₹{pred['current_price']:,.0f}\n"
    response += f" 📅 As of: {pred['current_timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n"
    response += f" ⭐ Rating: {pred['current_rating']}\n\n"
    response += f"✅ **OPTIMAL PRICE:** ₹{pred['optimal_price']:,.0f}\n\n"
    response += f"📈 **ANALYSIS:** {pred['analysis']}\n"
    response += f"{'='*100}\n"

    return response


def format_comparison_response(model_name, comparisons, target_date):
    """Format comparison across sources"""
    response = f"\n{'='*100}\n"
    response += f"🔄 **PRICE COMPARISON - {model_name}**\n"
    response += f"📅 **Prediction Date:** {target_date.strftime('%B %d, %Y')}\n\n"

    for src, prices in comparisons.items():
        response += f"🛒 **{src}:**\n"
        response += f" 🤖 ML Predicted: ₹{prices['ml']:,.0f}\n"
        response += f" 🧠 Gemini LLM: ₹{prices['gemini']:,.0f}\n" if prices['gemini'] else ""
        response += f" 💰 Current (Latest): ₹{prices['current']:,.0f}\n"
        response += f" 📅 As of: {prices['current_ts'].strftime('%Y-%m-%d %H:%M:%S')}\n"
        response += f" ⭐ Rating: {prices['current_rating']}\n"
        response += f" ✅ Optimal: ₹{prices['optimal']:,.0f}\n\n"

    best_source = min(comparisons, key=lambda x: comparisons[x]['optimal'])
    response += f"🎯 Best deal: {best_source} at ₹{comparisons[best_source]['optimal']:,.0f}\n"
    response += f"💡 Type 'update' to save both to dashboard\n"
    response += f"{'='*100}\n"

    return response


# ============================================================================
# MAIN CHATBOT FUNCTION
# ============================================================================

def advanced_iphone_chatbot():
    """Main chatbot loop"""
    global dashboard, all_predictions

    print("="*100)
    print("🤖 ADVANCED iPHONE PRICE PREDICTION CHATBOT (with LATEST prices)")
    print("="*100)
    print("\n📊 Features:")
    print(" • ML Model + Gemini LLM price predictions")
    print(" • Real data from GitHub (LATEST by timestamp) + synthetic data")
    print(" • Market & technical analysis")
    print(" • Gemini-powered optimal pricing")
    print(" • Real-time dashboard tracking (saves ALL sources)")
    print("\n Commands:")
    print(" • Just ask naturally: 'price for iPhone 16 on Amazon'")
    print(" • 'compare iPhone 15' - Compare both sources")
    print(" • 'update' - Save ALL last predictions to dashboard")
    print(" • 'dashboard' - View all tracked predictions")
    print(" • 'quit' - Exit\n")

    conversation_history = []
    all_predictions = []

    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue

        # Handle quit
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("\n👋 Thank you for using Advanced iPhone Price Predictor!")
            break

        # Handle dashboard view
        if user_input.lower() == 'dashboard':
            if len(dashboard) == 0:
                print("\nAssistant: 📊 Dashboard is empty. Make predictions first!\n")
            else:
                print("\n" + "="*120)
                print("📊 PREDICTION DASHBOARD")
                print("="*120)
                print(dashboard.to_string(index=False))
                print("="*120 + "\n")
            continue

        # Handle update command
        if user_input.lower() == 'update':
            if len(all_predictions) > 0:
                pred_list = all_predictions
                model_name = pred_list[0]['model']

                dashboard_updated = update_dashboard_batch(model_name, pred_list)
                dashboard = dashboard_updated

                sources_saved = ', '.join([p['source'] for p in pred_list])
                print(f"\nAssistant: ✅ Dashboard updated with {len(pred_list)} predictions!")
                print(f" Saved: {sources_saved}\n")

                all_predictions = []
            else:
                print(f"\nAssistant: ⚠️ No predictions to save. Make a prediction first!\n")
            continue

        # Parse user input
        model_name = parse_model_name(user_input)
        sources = parse_sources(user_input)
        target_date = parse_date(user_input)

        # Handle compare command
        if ('compare' in user_input.lower() or 'both' in user_input.lower()) and model_name:
            print("\n⏳ Comparing prices across sources...\n")

            comparisons = {}
            all_predictions = []

            for src in ['Amazon', 'Flipkart']:
                pred = get_single_prediction(model_name, src, target_date)
                comparisons[src] = {
                    'ml': pred['ml_pred'],
                    'gemini': pred['gemini_pred'],
                    'current': pred['current_price'],
                    'current_ts': pred['current_timestamp'],
                    'current_rating': pred['current_rating'],
                    'optimal': pred['optimal_price']
                }
                all_predictions.append(pred)

            response = format_comparison_response(model_name, comparisons, target_date)
            print(f"Assistant: {response}\n")
            continue

        # Handle prediction
        if model_name:
            if len(sources) == 0:
                sources = ['Amazon', 'Flipkart']

            if len(sources) == 2:
                print(f"\n⏳ Analyzing prices for {model_name} on both platforms...\n")

                all_predictions = []

                for source in sources:
                    pred = get_single_prediction(model_name, source, target_date)
                    response = format_prediction_response(pred, target_date)
                    print(f"Assistant: {response}\n")
                    all_predictions.append(pred)

                print("💡 Type 'update' to save BOTH predictions to dashboard\n")

            else:
                source = sources[0]
                print(f"\n⏳ Analyzing {model_name} price on {source}...\n")

                pred = get_single_prediction(model_name, source, target_date)
                response = format_prediction_response(pred, target_date)
                print(f"Assistant: {response}\n")

                all_predictions = [pred]

            conversation_history.append({"role": "User", "content": user_input})
        else:
            print("\nAssistant: I couldn't identify the iPhone model. Please mention:\n")
            print(" - iPhone 15, 16, or 17\n")
            print("Examples:")
            print(" - 'iPhone 16 on Amazon'")
            print(" - 'price for 17 on both'")
            print(" - 'compare iPhone 15'\n")


# ============================================================================
# DASHBOARD EXPORT
# ============================================================================

def export_dashboard(filename='price_prediction_dashboard.csv'):
    """Export dashboard to CSV"""
    global dashboard

    if len(dashboard) > 0:
        dashboard.to_csv(filename, index=False)
        print(f"✅ Dashboard exported to '{filename}'")
        print(f" Records: {len(dashboard)}")
        return True
    else:
        print("Dashboard is empty. Make predictions first!")
        return False


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Initialize all components from llm.py
    print("\n🚀 Starting iPhone Price Prediction Chatbot...\n")

    if initialize_all():
        print("\n✅ Ready to start chatbot\n")

        # Run the chatbot
        advanced_iphone_chatbot()

        # Export dashboard after chatbot ends
        print("\n📊 Exporting final dashboard...\n")
        export_dashboard()
    else:
        print("\n❌ Failed to initialize. Please check your files and dependencies.")
