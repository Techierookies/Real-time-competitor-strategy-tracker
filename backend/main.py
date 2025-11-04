import sqlite3
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import hashlib
import joblib
import pandas as pd
import numpy as np
from database import conn, cursor
from dotenv import load_dotenv
load_dotenv()
from model.llm import (
    initialize_all,
    safe_predict_iphone_price,
    safe_get_gemini_price,
    safe_get_gemini_analysis,
    safe_get_optimal_price,
    get_latest_current_price
)
from datetime import datetime
from admin_routes import router as admin_router
# ----------------------------
# FASTAPI App
# ----------------------------
app = FastAPI()
app.include_router(admin_router)
# ----------------------------
# CORS setup
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # your React frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Load ML Model + Preprocessors
# ----------------------------
try:
    MODEL_PATH = "model/iphone_price_prediction_model_random_forest.pkl"
    ENCODER_PATH = "model/price_prediction_encoders.pkl"
    SCALER_PATH = "model/price_prediction_scaler.pkl"
    FEATURES_PATH = "model/price_prediction_features.pkl"

    print("📦 Loading model and preprocessors...")

    model = joblib.load(MODEL_PATH)
    encoders = joblib.load(ENCODER_PATH)
    scaler = joblib.load(SCALER_PATH)
    feature_order = joblib.load(FEATURES_PATH)

    print("✅ Model and encoders loaded successfully!")

except Exception as e:
    print("❌ Error loading model or preprocessors:", e)
    model = None

# ----------------------------
# Pydantic Models
# ----------------------------
class SignupUser(BaseModel):
    name: str
    email: str
    password: str
    role: str = "user"

class LoginUser(BaseModel):
    email: str
    password: str
    isAdmin: bool = False

class iPhoneSpecs(BaseModel):
    storage: int
    ram: int
    battery: int
    refresh_rate: int
    chipset_score: float
    release_year: int

# ----------------------------
# User Signup Endpoint
# ----------------------------
@app.post("/signup")
def signup(user: SignupUser):
    hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
    role = user.role
    try:
        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            (user.name, user.email, hashed_password, role)
        )
        conn.commit()
        return {"status": "Signup successful", "role": role}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already exists")

# ----------------------------
# User Login Endpoint
# ----------------------------
@app.post("/login")
def login(user: LoginUser):
    hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
    role = "admin" if user.isAdmin else "user"
    cursor.execute(
        "SELECT * FROM users WHERE email=? AND password=? AND role=?",
        (user.email, hashed_password, role)
    )
    result = cursor.fetchone()
    if result:
        return {
            "status": "Login successful",
            "id": result[0],
            "name": result[1],
            "email": result[2],
            "role": result[4]
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid credentials")


# ----------------------------
# Chatbot Endpoint
# ----------------------------
initialize_all()

@app.post("/api/chatbot")
async def chatbot(request: Request):
    data = await request.json()
    user_message = data.get("message", "").lower()
    print("💬 User:", user_message)

    from model.chatbot import (
        get_single_prediction,
        update_dashboard_batch,
        export_dashboard,
        parse_model_name,
        parse_date,
    )

    # ✅ Handle update command
    if "update" in user_message:
        try:
            export_dashboard("price_prediction_dashboard.csv")
            return JSONResponse({"reply": "✅ Dashboard updated successfully and latest predictions saved!"})
        except Exception as e:
            return JSONResponse({"reply": f"⚠️ Failed to update dashboard: {str(e)}"})

    # ✅ Parse model and date
    model_name = parse_model_name(user_message)
    if not model_name:
        return JSONResponse({"reply": "Please mention a valid iPhone model (e.g., iPhone 16, 17)."})
    target_date = parse_date(user_message)

    # ✅ Always predict for BOTH sources
    sources = ["Amazon", "Flipkart"]
    predictions = []
    combined_reply = ""

    for src in sources:
        pred = get_single_prediction(model_name, src, target_date)
        predictions.append(pred)

        combined_reply += f"""
📱 **{model_name} on {src}**
🤖 ML Model Predicted Price: ₹{pred['ml_pred']:,.0f}
🧠 Gemini Predicted Price: ₹{pred['gemini_pred'] or pred['ml_pred']:,.0f}
💰 Current Market Price: ₹{pred['current_price'] or pred['ml_pred']:,.0f}
✅ Optimal Selling Price: ₹{pred['optimal_price']:,.0f}
📊 Analysis: {pred['analysis']}
{"="*80}
"""

    # ✅ Update dashboard automatically
    update_dashboard_batch(model_name, predictions)
    export_dashboard("price_prediction_dashboard.csv")

    return JSONResponse({
        "reply": combined_reply.strip(),
        "note": "✅ Both Amazon & Flipkart prices updated on dashboard."
    })


# ----------------------------
# Admin_dashboard endpoint
# ----------------------------
@app.get("/api/admin_dashboard")
def get_dashboard_data():
    # yahan se tum chatbot.py ya llm.py se latest CSV ya data fetch kar sakti ho
    import pandas as pd
    import numpy as np
    try:
        df = pd.read_csv("price_prediction_dashboard.csv")
        df = df.replace([np.nan, None], "N/A")
        data = df.to_dict(orient="records")
        return {"status": "success", "dashboard_data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
# ----------------------------
# refresh dashboard endpoint
# ----------------------------    

@app.post("/api/refresh_dashboard")
def refresh_dashboard():
    from model.chatbot import export_dashboard  # ya jahan se update hoti hai
    try:
        export_dashboard("price_prediction_dashboard.csv")
        return {"message": "Dashboard refreshed and prices updated!"}
    except Exception as e:
        return {"message": f"Error refreshing: {e}"}

# ============================================================
# 🛒 STORE PRODUCT MANAGEMENT ENDPOINTS (Add + Get + Update + Delete)
# ============================================================

from pydantic import BaseModel
from fastapi import Body

class StoreProduct(BaseModel):
    name: str
    sku: str
    category: str
    price: float
    stock: int
    status: str = "active"

# ✅ 1. Get all store products
@app.get("/api/store-products")
def get_all_store_products():
    try:
        cursor.execute("SELECT id, name, sku, category, price, stock, status FROM store_products")
        rows = cursor.fetchall()
        products = [
            {
                "id": r[0],
                "name": r[1],
                "sku": r[2],
                "category": r[3],
                "price": r[4],
                "stock": r[5],
                "status": r[6],
            }
            for r in rows
        ]
        return {"status": "success", "products": products}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ✅ 2. Add new store product
@app.post("/api/store-products/add")
def add_store_product(product: StoreProduct):
    try:
        cursor.execute(
            """
            INSERT INTO store_products (name, sku, category, price, stock, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (product.name, product.sku, product.category, product.price, product.stock, product.status),
        )
        conn.commit()
        return {"status": "success", "message": "✅ Store product added successfully!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ✅ 3. Update product (price / stock / status)
@app.put("/api/store-products/{product_id}/update")
def update_store_product(product_id: int, data: dict = Body(...)):
    try:
        allowed_fields = {"price", "stock", "status"}
        updates = []
        values = []

        for key, val in data.items():
            if key in allowed_fields:
                updates.append(f"{key} = ?")
                values.append(val)

        if not updates:
            return {"status": "error", "message": "No valid fields to update"}

        query = f"UPDATE store_products SET {', '.join(updates)} WHERE id = ?"
        values.append(product_id)
        cursor.execute(query, tuple(values))
        conn.commit()
        return {"status": "success", "message": "✅ Store product updated successfully!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ✅ 4. Delete store product
@app.delete("/api/store-products/{product_id}")
def delete_store_product(product_id: int):
    try:
        cursor.execute("DELETE FROM store_products WHERE id=?", (product_id,))
        conn.commit()
        return {"status": "success", "message": "🗑️ Store product deleted successfully!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}



# ----------------------------
# Root Endpoint
# ----------------------------
@app.get("/")
def home():
    return {"message": "iPhone Price Prediction API is running "}
