from flask import Flask, request, jsonify, g
from flask_cors import CORS
from database import create_connection, check_db_exists, DB_NAME
from scoring import calculate_health_score
import sqlite3

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app) 

# --- Database Connection Management ---

# Helper function to get a database connection that returns rows as dict-like objects
def get_db_connection():
    # Use the connection helper from database.py
    conn = create_connection()
    # Crucially, set the row_factory to sqlite3.Row for dictionary-style access (row['name'])
    conn.row_factory = sqlite3.Row 
    return conn

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- API Routes ---

@app.route('/api', methods=['GET'])
def api_info():
    """Provides basic info about the API."""
    return jsonify({
        "status": "OK", 
        "service": "Health Scanner API", 
        "version": "1.0",
        "endpoints": ["/api/product/<barcode>", "/api/product (POST)", "/api/products"]
    })

@app.route('/api/product/<barcode>', methods=['GET'])
def get_product(barcode):
    """
    Retrieves a product by barcode, calculates its health score, and returns the result.
    FIXED: Uses the correct database schema (no 'id' column) and additive structure.
    """
    conn = get_db_connection()
    
    # 1. Fetch Product Data (sqlite3.Row object)
    # The 'products' table uses 'barcode' as the primary key, not a separate 'id'.
    product_row = conn.execute("SELECT * FROM products WHERE barcode = ?", (barcode,)).fetchone()
    
    if product_row is None:
        # Close the connection immediately if not found
        conn.close() 
        return jsonify({"error": "Product not found in the database."}), 404
        
    # sqlite3.Row is dict-like, so we can access columns by name directly.
    # We do NOT need dict(product) if using sqlite3.Row, but if we cast it, it works.
    product_dict = dict(product_row) 
    
    # 2. Extract Additives from the single 'additives' column (comma-separated string)
    additives_str = product_dict.get('additives', '')
    if additives_str:
        # Parse the comma-separated string into a list, cleaning up spaces
        additives_list = [a.strip() for a in additives_str.split(',') if a.strip()]
    else:
        additives_list = []

    # 3. Prepare Nutrition Data for Scoring
    nutrition_data = {
        'sugar': product_dict['sugar'],
        'salt': product_dict['salt'],
        'saturated_fat': product_dict['saturated_fat'],
        'protein': product_dict['protein'],
        'fiber': product_dict['fiber'],
    }
    
    # 4. Calculate Health Score
    health_score = calculate_health_score(nutrition_data, additives_list)

    # 5. Build and Return Response
    response = {
        "barcode": product_dict['barcode'],
        "name": product_dict['name'],
        "brand": product_dict['brand'],
        "category": product_dict['category'],
        "health_score": health_score,
        "nutrition_per_100g": {
            "sugar": product_dict['sugar'],
            "salt": product_dict['salt'],
            "fat": product_dict['fat'],
            "saturated_fat": product_dict['saturated_fat'],
            "protein": product_dict['protein'],
            "fiber": product_dict['fiber'],
            "calories": product_dict['calories'],
        },
        "additives": additives_list
    }
    
    # The teardown function will close the connection if we don't, but explicitly closing is safer here
    conn.close() 
    return jsonify(response)


@app.route('/api/product', methods=['POST'])
def add_product():
    """
    Allows community members to add new products to the database.
    FIXED: Uses the correct 'products' table schema and additive column.
    """
    data = request.get_json()
    required_fields = ['barcode', 'name', 'brand', 'sugar', 'salt', 'fat', 'saturated_fat', 'protein', 'fiber', 'calories']

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required nutritional fields."}), 400

    conn = get_db_connection()
    
    # Data extraction
    barcode = data.get('barcode')
    additives_str = data.get('additives', '') # Stored as a single string
    
    # Basic data integrity check
    if conn.execute("SELECT barcode FROM products WHERE barcode = ?", (barcode,)).fetchone():
        conn.close()
        return jsonify({"error": f"Product with barcode {barcode} already exists."}), 409

    try:
        # Insert product
        cursor = conn.execute("""
            INSERT INTO products 
            (barcode, name, brand, category, sugar, salt, fat, saturated_fat, protein, fiber, calories, additives) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            barcode, 
            data.get('name'), 
            data.get('brand'), 
            data.get('category', 'General'), 
            data.get('sugar', 0.0), 
            data.get('salt', 0.0), 
            data.get('fat', 0.0), 
            data.get('saturated_fat', 0.0), 
            data.get('protein', 0.0), 
            data.get('fiber', 0.0), 
            data.get('calories', 0.0),
            additives_str # Insert the raw string into the 'additives' column
        ))
        
        # NOTE: product_id is not needed since the additives are stored in the same table row.
        # The line 'product_id = cursor.lastrowid' and the loop for additives is REMOVED.
        
        conn.commit()
        conn.close()
        
        return jsonify({"message": "Product added successfully.", "barcode": barcode}), 201

    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": "Database error during product insertion.", "details": str(e)}), 500


# --- Server Run ---

if __name__ == '__main__':
    # Initialize DB before running the app
    # FIXED: check_db_exists does not take 'app' as an argument.
    check_db_exists()

    print("\n--- Starting Health Scanner API ---")
    # Use a product that actually exists in the large sample data
    print("Test URL: http://127.0.0.1:5000/api/product/6009900000003 (Coke Original)")
    app.run(debug=True)