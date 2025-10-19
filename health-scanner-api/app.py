from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from database import create_connection, check_db_exists
from scoring import calculate_health_score
import sqlite3

# 🔑 SECURITY: Define the allowed origins for CORS
# IMPORTANT: Replace the placeholder below with your final Netlify/Vercel URL!
FRONTEND_URL = [
    "http://127.0.0.1:5000",        # For local testing
    "http://localhost:5000",        # For local testing
    "https://YOUR-NETLIFY-APP-NAME.netlify.app" # 🔑 REPLACE THIS
] 

# --- Flask App Initialization ---
app = Flask(__name__)
# 🔑 SECURITY: Restrict CORS to only allow requests from the defined FRONTEND_URL
CORS(app, resources={r"/api/*": {"origins": FRONTEND_URL}}) 

# 🔑 SECURITY: Rate Limiter Configuration (Uses IP address to track requests)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"] # Global default limits
)

# --- Database Connection Management ---

def get_db_connection():
    # Helper function to get a database connection that returns rows as dict-like objects
    conn = create_connection()
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
        "endpoints": ["/api/product/<barcode>", "/api/product (POST)"]
    })

@app.route('/api/product/<barcode>', methods=['GET'])
@limiter.limit("5 per minute") # 🔑 SECURITY: Limit to 5 requests per minute per IP for scanning
def get_product(barcode):
    """
    Retrieves a product by barcode, calculates its health score, and returns the result.
    """
    
    # 🔑 SECURITY: Basic Input Validation
    if not barcode.isdigit() or len(barcode) < 8 or len(barcode) > 13:
        return jsonify({"error": "Invalid barcode format. Must be an 8-13 digit number."}), 400
        
    conn = get_db_connection()
    
    # 1. Fetch Product Data (Uses prepared statements, preventing SQL Injection)
    product_row = conn.execute("SELECT * FROM products WHERE barcode = ?", (barcode,)).fetchone()
    
    if product_row is None:
        return jsonify({"error": "Product not found in the database."}), 404
        
    product_dict = dict(product_row) 
    
    # 2. Extract Additives
    additives_str = product_dict.get('additives', '')
    additives_list = [a.strip() for a in additives_str.split(',') if a.strip()] if additives_str else []

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
    
    return jsonify(response)

@app.route('/api/product', methods=['POST'])
@limiter.limit("2 per hour") # 🔑 SECURITY: Restrict adding new products to prevent DB spam
def add_product():
    """
    Allows community members to add new products to the database.
    """
    data = request.get_json()
    required_fields = ['barcode', 'name', 'brand', 'sugar', 'salt', 'fat', 'saturated_fat', 'protein', 'fiber', 'calories']

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required nutritional fields."}), 400

    conn = get_db_connection()
    
    barcode = data.get('barcode')
    additives_str = data.get('additives', '')

    # 🔑 SECURITY: Check if barcode is valid and already exists
    if not barcode.isdigit() or len(barcode) < 8 or len(barcode) > 13:
         return jsonify({"error": "Invalid barcode format."}), 400
         
    if conn.execute("SELECT barcode FROM products WHERE barcode = ?", (barcode,)).fetchone():
        return jsonify({"error": f"Product with barcode {barcode} already exists."}), 409

    try:
        # Insert product (Uses prepared statements, preventing SQL Injection)
        conn.execute("""
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
            additives_str
        ))
        
        conn.commit()
        
        return jsonify({"message": "Product added successfully.", "barcode": barcode}), 201

    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({"error": "Database error during product insertion.", "details": str(e)}), 500


# --- Server Run ---

if __name__ == '__main__':
    with app.app_context():
        check_db_exists()

    print("\n--- Starting Health Scanner API ---")
    app.run(debug=True)