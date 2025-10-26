import sqlite3 
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import hashlib
from database import conn, cursor  

app = FastAPI()
# CORS setup (frontend URL allow)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class SignupUser(BaseModel):
    name: str
    email: str
    password: str
    role: str = "user"   

class LoginUser(BaseModel):
    email: str
    password: str
    isAdmin: bool = False

# -------------------
# Signup endpoint
# -------------------
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

# -------------------
# Login endpoint
# -------------------
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
