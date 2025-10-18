from flask import Flask, request, jsonify, g
from flask_cors import CORS
from database import get_db_connection, check_db_exists
from scoring import calculate_health_score
import sqlite3

# --- Flask App Initialization ---
app = Flask(__name__)
# Enable CORS for the frontend on the same or different host
CORS(app) 

# --- Database Connection Management ---

# Function to close DB connection after each request
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
    """
    conn = get_db_connection()
    
    # 1. Fetch Product Data
    product = conn.execute("SELECT * FROM products WHERE barcode = ?", (barcode,)).fetchone()
    
    if product is None:
        return jsonify({"error": "Product not found in the database."}), 404
        
    product_dict = dict(product) # Convert Row object to dictionary
    product_id = product_dict['id']
    
    # 2. Fetch Additives
    additives = conn.execute("SELECT additive FROM additives WHERE product_id = ?", (product_id,)).fetchall()
    additives_list = [a['additive'] for a in additives]
    
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
def add_product():
    """
    Allows community members to add new products to the database.
    (Simple validation only)
    """
    data = request.get_json()
    required_fields = ['barcode', 'name', 'brand', 'sugar', 'salt', 'fat', 'saturated_fat', 'protein', 'fiber', 'calories']

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required nutritional fields."}), 400

    conn = get_db_connection()
    
    # Data extraction with defaults for optional/real fields
    barcode = data.get('barcode')
    additives_str = data.get('additives', '')
    
    # Basic data integrity check
    if conn.execute("SELECT barcode FROM products WHERE barcode = ?", (barcode,)).fetchone():
        return jsonify({"error": f"Product with barcode {barcode} already exists."}), 409

    try:
        # Insert product
        cursor = conn.execute("""
            INSERT INTO products 
            (barcode, name, brand, category, sugar, salt, fat, saturated_fat, protein, fiber, calories) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            data.get('calories', 0.0)
        ))
        
        product_id = cursor.lastrowid
        
        # Insert additives
        if additives_str:
            additives = [a.strip() for a in additives_str.split(',') if a.strip()]
            for additive in additives:
                conn.execute("INSERT INTO additives (product_id, additive) VALUES (?, ?)", (product_id, additive))
        
        conn.commit()
        
        return jsonify({"message": "Product added successfully.", "barcode": barcode}), 201

    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({"error": "Database error during product insertion.", "details": str(e)}), 500


# --- Server Run ---

if __name__ == '__main__':
    # Initialize DB before running the app
    with app.app_context():
        check_db_exists(app)

    # Note: Use 'flask run' in a production environment or an environment manager.
    # For quick testing, run this file directly:
    print("\n--- Starting Health Scanner API ---")
    print("Test URL: http://127.0.0.1:5000/api/product/6001000000018 (Coca-Cola)")
    app.run(debug=True)