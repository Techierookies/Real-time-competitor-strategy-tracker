import sqlite3

# Connect to SQLite database (or create it)
conn = sqlite3.connect("competitor_tracker.db", check_same_thread=False)
cursor = conn.cursor()

# Users table (user + admin)
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user'   -- 'user' ya 'admin'
)
""")

conn.commit()

# Check if default admin exists, if not, create one
cursor.execute("SELECT * FROM users WHERE email=?", ("admin@iphone-store.com",))
admin_exists = cursor.fetchone()

if not admin_exists:
    import hashlib
    hashed_password = hashlib.sha256("admin@123".encode()).hexdigest()
    cursor.execute("""
        INSERT INTO users (name, email, password, role)
        VALUES (?, ?, ?, ?)
    """, ("Admin", "admin@iphone-store.com", hashed_password, "admin"))
    conn.commit()
    print("✅ Default admin created successfully!")
else:
    print("✅ Admin already exists.")

# ✅ Create 'products' table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    model TEXT,
    source TEXT,
    ml_predicted REAL,
    gemini_predicted REAL,
    current_price REAL,
    current_timestamp TEXT,
    current_rating REAL,
    optimal_price REAL,
    analysis TEXT,
    review TEXT
)
""")

conn.commit()
print("✅ Products table created (if not exists).")

# ✅ Create 'store_products' table for admin product management
cursor.execute("""
CREATE TABLE IF NOT EXISTS store_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    sku TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'active'
)
""")

conn.commit()
print("✅ Store_Products table created (for dashboard product management).")
