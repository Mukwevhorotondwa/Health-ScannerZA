import sqlite3
import os

# --- Configuration ---
DATABASE = 'healthscanner.db'

# Initial Sample Data (14 SA products)
# Format: (barcode, name, brand, category, sugar, salt, fat, saturated_fat, protein, fiber, calories, additives)
# Nutritional values are per 100g/100ml. Additives are comma-separated E-numbers.
SAMPLE_PRODUCTS = [
    # Very Unhealthy Example: High Sugar, High Salt, Additives
    ("6001000000018", "Coca-Cola Original Taste", "Coca-Cola", "Beverage", 10.6, 0.0, 0.0, 0.0, 0.0, 0.0, 42.0, "E150d,E338"),
    
    # Unhealthy Example: High Sugar, High Saturated Fat
    ("6009618580016", "Simba Potato Chips Salt & Vinegar", "Simba", "Snack", 0.7, 1.4, 30.0, 12.0, 5.7, 4.0, 520.0, "E621,E631"),

    # Moderate Example: Some Sugar/Salt, Some Fiber
    ("6001234567890", "Albany Low GI Brown Bread", "Albany", "Bakery", 3.0, 0.4, 2.0, 0.5, 10.0, 6.5, 230.0, "E471,E282"),

    # Healthy Example: Low Sugar/Salt, High Protein, High Fiber
    ("6002000000001", "Clover Full Cream Milk", "Clover", "Dairy", 4.7, 0.1, 3.3, 2.1, 3.4, 0.0, 61.0, ""),

    # More SA Brands/Products for variety
    ("6009173000551", "Ouma Rusks Buttermilk", "Ouma", "Snack", 12.0, 0.6, 12.0, 7.0, 8.0, 2.0, 450.0, "E471,E322"),
    ("6009184100234", "Tastic Rice", "Tastic", "Grain", 0.2, 0.0, 0.0, 0.0, 7.0, 0.8, 360.0, ""),
    ("6009180000100", "Bokomo Pronutro Original", "Bokomo", "Cereal", 14.0, 0.3, 5.0, 1.0, 20.0, 10.0, 390.0, "E320,E321"),
    ("6009210000213", "Fatti's & Moni's Macaroni", "Fatti's & Moni's", "Pasta", 2.0, 0.0, 1.0, 0.3, 12.0, 3.0, 370.0, ""),
    ("6009686000058", "Liqui-Fruit 100% Apple Juice", "Liqui-Fruit", "Beverage", 10.0, 0.0, 0.0, 0.0, 0.2, 0.0, 40.0, ""),
    ("6009178000013", "Koo Baked Beans in Tomato Sauce", "Koo", "Canned Food", 5.0, 0.5, 0.5, 0.1, 4.0, 5.0, 100.0, "E1422,E412"),
    ("6001509000134", "Five Roses Tea Bags", "Five Roses", "Beverage", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, ""),
    ("6009170000200", "Mrs Ball's Chutney Original", "Mrs Ball's", "Condiment", 20.0, 1.0, 0.1, 0.0, 0.1, 0.5, 80.0, "E330,E415"),
    ("6009695000045", "Nola Mayonnaise", "Nola", "Condiment", 4.0, 0.8, 70.0, 10.0, 1.0, 0.0, 650.0, "E385,E412"),
    ("6009121000022", "I&J Fish Fingers", "I&J", "Frozen Food", 2.0, 0.6, 10.0, 2.0, 12.0, 1.0, 250.0, "E160a,E412"),
]

def get_db_connection():
    """Establishes a connection to the database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

def init_db(app):
    """Initializes the database schema and loads sample data."""
    with app.app_context():
        conn = get_db_connection()
        
        # 1. Create Products Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                brand TEXT NOT NULL,
                category TEXT,
                sugar REAL,
                salt REAL,
                fat REAL,
                saturated_fat REAL,
                protein REAL,
                fiber REAL,
                calories REAL
            );
        """)
        
        # 2. Create Additives Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS additives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                additive TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(id)
            );
        """)
        
        # 3. Load Sample Data
        for (barcode, name, brand, category, sugar, salt, fat, saturated_fat, protein, fiber, calories, additives_str) in SAMPLE_PRODUCTS:
            try:
                # Insert product
                cursor = conn.execute("""
                    INSERT INTO products 
                    (barcode, name, brand, category, sugar, salt, fat, saturated_fat, protein, fiber, calories) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (barcode, name, brand, category, sugar, salt, fat, saturated_fat, protein, fiber, calories))
                
                product_id = cursor.lastrowid
                
                # Insert additives
                if additives_str:
                    additives = [a.strip() for a in additives_str.split(',') if a.strip()]
                    for additive in additives:
                        conn.execute("INSERT INTO additives (product_id, additive) VALUES (?, ?)", (product_id, additive))
                
            except sqlite3.IntegrityError:
                # This handles the case where the barcode already exists (i.e., db already initialized)
                pass 
                
        conn.commit()
        conn.close()
        print("Database initialized and sample data loaded successfully.")

# Function to be called before running the Flask app to ensure setup
def check_db_exists(app):
    """Checks if the database file exists, if not, initializes it."""
    if not os.path.exists(DATABASE):
        print("Database file not found. Initializing database...")
        init_db(app)
    else:
        print("Database file found. Skipping initialization.")