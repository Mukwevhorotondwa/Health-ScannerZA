# database.py

import sqlite3
import os

# --- Database Configuration ---
DB_NAME = 'healthscanner.db'

# Column indices for easy access (used in load_sample_data)
BARCODE = 0
NAME = 1
BRAND = 2
CATEGORY = 3
SUGAR = 4
SALT = 5
FAT = 6
SAT_FAT = 7
PROTEIN = 8
FIBER = 9
CALORIES = 10
ADDITIVES = 11

# --- Sample Data (104 Products) ---
# Format: (Barcode, Name, Brand, Category, Sugar, Salt, Fat, Sat_Fat, Protein, Fiber, Calories (kcal), Additives)
# Nutritional values are per 100g/100ml
SAMPLE_PRODUCTS = [
    # --- 1. Original 14 Products ---
    ("6009900000001", "Full Cream Milk", "Clover", "Dairy", 4.7, 0.10, 3.3, 2.0, 3.4, 0.0, 61, ""),
    ("6009900000002", "White Rice (Cooked)", "Tastic", "Staple", 0.0, 0.00, 0.0, 0.0, 2.7, 0.4, 130, ""),
    ("6009900000003", "Coke Original", "Coca-Cola", "Soda", 10.6, 0.00, 0.0, 0.0, 0.0, 0.0, 42, "E150d,E338"),
    ("6009900000004", "Baked Beans in Tomato Sauce", "Koo", "Canned", 5.0, 0.50, 0.5, 0.1, 4.0, 5.0, 100, "E1422"),
    ("6009900000005", "Biltong (Lean Beef)", "Generic Butcher", "Protein", 1.0, 2.50, 5.0, 2.0, 50.0, 0.0, 260, "E250,E301"),
    ("6009900000006", "Wholewheat Bread", "Albany", "Bakery", 3.0, 0.45, 2.0, 0.4, 9.0, 5.0, 230, "E282"),
    ("6009900000007", "Salted Butter", "Anchor", "Dairy", 0.1, 1.80, 81.0, 51.0, 0.5, 0.0, 740, ""),
    ("6009900000008", "Cheddar Cheese", "Lactalis", "Dairy", 0.1, 1.80, 33.0, 20.0, 25.0, 0.0, 400, ""),
    ("6009900000009", "Potato Chips (Salted)", "Lay's", "Snack", 0.5, 1.00, 35.0, 4.0, 6.0, 3.0, 550, "E621"),
    ("6009900000010", "100% Orange Juice", "Ceres", "Juice", 10.0, 0.00, 0.0, 0.0, 0.5, 0.5, 45, ""),
    ("6009900000011", "Sweet Biscuits (Cream Filled)", "Bakers", "Snack", 30.0, 0.40, 25.0, 15.0, 4.0, 1.0, 520, "E471,E450"),
    ("6009900000012", "Polony (Red)", "Eskort", "Processed Meat", 1.0, 2.50, 20.0, 8.0, 10.0, 0.0, 240, "E250,E316,E407"),
    ("6009900000013", "Olive Oil (Extra Virgin)", "B-Well", "Oil", 0.0, 0.00, 100.0, 14.0, 0.0, 0.0, 900, ""),
    ("6009900000014", "Instant Noodles (Chicken)", "Noodle King", "Pasta", 2.0, 1.20, 8.0, 4.0, 7.0, 2.0, 420, "E621,E150a"),

    # --- 2. New 90 Common SA Products for Demo ---
    # B01: Dairy & Alternatives
    ("6000000000101", "Danone Plain Yoghurt", "Danone", "Dairy", 4.5, 0.15, 3.5, 2.0, 5.0, 0.0, 65, ""),
    ("6000000000102", "Clover Bliss Chocolate", "Clover", "Dairy", 14.0, 0.20, 2.5, 1.5, 3.0, 0.0, 95, "E1422,E407"),
    ("6000000000103", "Parmalat Cheddar Cheese", "Parmalat", "Dairy", 0.1, 1.80, 33.0, 20.0, 25.0, 0.0, 400, ""),
    ("6000000000104", "Rama Original Margarine", "Rama", "Spreads", 0.5, 0.70, 70.0, 25.0, 0.0, 0.0, 630, "E471,E160a"),
    ("6000000000105", "Clover Fresh Cream", "Clover", "Dairy", 3.5, 0.10, 35.0, 22.0, 2.0, 0.0, 330, ""),
    ("6000000000106", "Oatly Oat Drink Original", "Oatly", "Alt. Dairy", 4.0, 0.10, 1.5, 0.2, 1.0, 0.8, 45, ""),
    
    # B02: Snacks & Treats
    ("6000000000201", "Bakers Tennis Biscuits", "Bakers", "Snack", 22.0, 0.50, 20.0, 11.0, 5.0, 1.0, 480, "E450,E500"),
    ("6000000000202", "Pringles Original", "Pringles", "Snack", 0.5, 0.80, 32.0, 3.0, 6.0, 3.0, 530, "E621,E635"),
    ("6000000000203", "Cadbury Dairy Milk", "Cadbury", "Chocolate", 56.0, 0.20, 30.0, 18.0, 8.0, 0.5, 550, "E476"),
    ("6000000000204", "Beacon Heavenly Hash", "Beacon", "Sweets", 70.0, 0.10, 1.0, 0.5, 0.5, 0.0, 320, "E129,E133"),
    ("6000000000205", "Willards Big Korn Bites", "Willards", "Snack", 1.0, 1.30, 25.0, 3.0, 7.0, 2.0, 500, "E621,E631,E627"),
    ("6000000000206", "Safari Mixed Dried Fruit", "Safari", "Dried Fruit", 45.0, 0.10, 1.0, 0.5, 3.0, 7.0, 300, "E220"),
    ("6000000000207", "ProNutro Power Bar", "ProNutro", "Bar", 20.0, 0.50, 15.0, 5.0, 18.0, 5.0, 450, "E320"),
    ("6000000000208", "Five Roses Tea Bags (No milk/sugar)", "Five Roses", "Beverage", 0.0, 0.00, 0.0, 0.0, 0.0, 0.0, 0, ""),
    ("6000000000209", "Ricoffy Instant Coffee", "Ricoffy", "Beverage", 0.0, 0.00, 0.0, 0.0, 0.0, 0.0, 2, ""),
    ("6000000000210", "Lay's Salted Chips", "Lay's", "Snack", 0.5, 1.00, 35.0, 4.0, 6.0, 3.0, 550, ""),

    # B03: Staples & Grains
    ("6000000000301", "White Star Maize Meal", "White Star", "Staple", 1.0, 0.00, 1.0, 0.2, 8.0, 4.0, 350, ""),
    ("6000000000302", "Sasko Brown Bread", "Sasko", "Bakery", 3.5, 0.40, 2.5, 0.5, 9.5, 5.5, 240, "E282"),
    ("6000000000303", "Kellogg's Corn Flakes", "Kellogg's", "Cereal", 8.0, 0.80, 0.5, 0.1, 7.0, 1.5, 370, ""),
    ("6000000000304", "Pioneer Ready-to-Eat Oats", "Pioneer", "Cereal", 1.0, 0.05, 7.0, 1.0, 13.0, 10.0, 380, ""),
    ("6000000000305", "Jungle Oats Original", "Jungle", "Cereal", 1.5, 0.05, 8.0, 1.5, 14.0, 11.0, 390, ""),
    ("6000000000306", "Spekko Blue Rice", "Spekko", "Grain", 0.2, 0.00, 0.0, 0.0, 7.0, 0.8, 360, ""),
    ("6000000000307", "Noodle King Noodles Chicken", "Noodle King", "Pasta", 2.0, 1.20, 8.0, 4.0, 7.0, 2.0, 420, "E621,E150a"),
    ("6000000000308", "Bokomo Weet-Bix", "Bokomo", "Cereal", 4.0, 0.40, 1.5, 0.3, 12.0, 10.0, 370, ""),
    ("6000000000309", "Iwisa Maize Meal", "Iwisa", "Staple", 1.0, 0.00, 1.0, 0.2, 8.0, 4.0, 350, ""),

    # B04: Sauces, Condiments & Spreads
    ("6000000000401", "Knorr Brown Onion Soup", "Knorr", "Soup", 15.0, 4.00, 1.0, 0.5, 4.0, 0.5, 100, "E621,E631"),
    ("6000000000402", "All Gold Tomato Sauce", "All Gold", "Sauce", 20.0, 1.20, 0.1, 0.0, 0.5, 1.0, 85, "E211"),
    ("6000000000403", "Black Cat Smooth Peanut Butter", "Black Cat", "Spread", 8.0, 0.50, 48.0, 8.0, 25.0, 5.0, 600, "E471"),
    ("6000000000404", "Wellington's Sweet Chili Sauce", "Wellington's", "Sauce", 30.0, 1.50, 0.1, 0.0, 0.5, 0.5, 130, "E202,E211"),
    ("6000000000405", "Robertsons Spices (Mixed Herbs)", "Robertsons", "Spice", 0.0, 0.00, 0.0, 0.0, 0.0, 0.0, 0, ""),
    ("6000000000406", "Crosse & Blackwell Mayonnaise", "C&B", "Condiment", 5.0, 0.80, 70.0, 10.0, 1.0, 0.0, 650, "E385,E412"),
    ("6000000000407", "Rajah Curry Powder Mild", "Rajah", "Spice", 0.0, 0.00, 10.0, 1.0, 10.0, 30.0, 350, "E102,E110"),
    ("6000000000408", "Mrs Ball's Original Chutney", "Mrs Ball's", "Condiment", 25.0, 1.00, 0.1, 0.0, 0.1, 0.5, 80, "E330,E415"),

    # B05: Beverages & Juices
    ("6000000000501", "Fanta Orange Soda", "Fanta", "Soda", 11.0, 0.00, 0.0, 0.0, 0.0, 0.0, 44, "E110,E129"),
    ("6000000000502", "Valpre Still Water", "Valpre", "Water", 0.0, 0.00, 0.0, 0.0, 0.0, 0.0, 0, ""),
    ("6000000000503", "Ceres 100% Orange Juice", "Ceres", "Juice", 10.0, 0.00, 0.0, 0.0, 0.5, 0.5, 45, ""),
    ("6000000000504", "Nestea Peach Iced Tea", "Nestea", "Iced Tea", 5.0, 0.05, 0.0, 0.0, 0.0, 0.0, 20, "E211,E330"),
    ("6000000000505", "Appletiser Sparkling Juice", "Appletiser", "Juice", 10.0, 0.00, 0.0, 0.0, 0.0, 0.0, 42, ""),
    ("6000000000506", "BOS Ice Tea Lemon", "BOS", "Iced Tea", 3.0, 0.00, 0.0, 0.0, 0.0, 0.0, 12, ""),

    # B06: Tinned & Canned Goods
    ("6000000000601", "Lucky Star Pilchards (Tomato Sauce)", "Lucky Star", "Canned Fish", 4.0, 1.00, 10.0, 3.0, 18.0, 1.0, 170, "E1422"),
    ("6000000000602", "Koo Peaches in Syrup", "Koo", "Canned Fruit", 18.0, 0.05, 0.1, 0.0, 0.5, 1.0, 75, "E330"),
    ("6000000000603", "Rhodes Tomato Puree", "Rhodes", "Canned Veg", 3.0, 0.50, 0.1, 0.0, 1.5, 2.0, 30, "E330"),
    ("6000000000604", "Rajah Tinned Beans (Chili)", "Rajah", "Canned Legumes", 4.0, 0.60, 1.0, 0.2, 5.0, 5.0, 120, "E150a"),
    ("6000000000605", "Koo Baked Beans (Sweetened)", "Koo", "Canned Legumes", 5.0, 0.50, 0.5, 0.1, 4.0, 5.0, 100, "E1422"),

    # B07: Ready Meals & Frozen
    ("6000000000701", "Fry's Chicken-Style Strips", "Fry's", "Frozen Veggie", 0.5, 1.00, 3.0, 0.5, 20.0, 5.0, 130, "E621"),
    ("6000000000702", "McCain French Fries", "McCain", "Frozen Veg", 0.5, 0.10, 5.0, 1.0, 2.0, 3.0, 150, "E450"),
    ("6000000000703", "Eskimo Pies", "Eskimo", "Ice Cream", 28.0, 0.10, 18.0, 12.0, 4.0, 0.0, 300, "E471,E412"),
    ("6000000000704", "I&J Crumbed Hake Fillets", "I&J", "Frozen Fish", 1.0, 0.80, 8.0, 2.0, 14.0, 1.0, 180, "E450"),
    ("6000000000705", "Dr. Oetker Pizza Margherita", "Dr. Oetker", "Frozen Pizza", 2.5, 1.20, 12.0, 6.0, 10.0, 2.0, 280, "E472e"),

    # B08: Baking & Cooking
    ("6000000000801", "Selati White Sugar", "Selati", "Baking", 100.0, 0.00, 0.0, 0.0, 0.0, 0.0, 400, ""),
    ("6000000000802", "Snowflake Cake Flour", "Snowflake", "Baking", 0.5, 0.00, 1.0, 0.2, 10.0, 3.0, 360, ""),
    ("6000000000803", "B-Well Canola Oil", "B-Well", "Oil", 0.0, 0.00, 100.0, 8.0, 0.0, 0.0, 900, ""),
    ("6000000000804", "Huletts Brown Sugar", "Huletts", "Baking", 98.0, 0.00, 0.0, 0.0, 0.0, 0.0, 390, ""),
    ("6000000000805", "Safari Yeast", "Safari", "Baking", 0.0, 0.00, 1.0, 0.2, 40.0, 20.0, 300, ""),

    # B09: Cereals & Breakfast
    ("6000000000901", "Nestlé Milo", "Nestlé", "Cereal", 50.0, 0.30, 8.0, 4.0, 12.0, 3.0, 420, "E341"),
    ("6000000000902", "Clover Tropika Fruit Nectar", "Clover", "Beverage", 8.0, 0.05, 0.0, 0.0, 0.0, 0.0, 35, "E102,E110,E122"),
    ("6000000000903", "Kellogg's Coco Pops", "Kellogg's", "Cereal", 35.0, 0.50, 2.0, 1.0, 5.0, 1.0, 390, "E320"),
    ("6000000000904", "Liqui-Fruit Guava 100% Juice", "Liqui-Fruit", "Juice", 9.0, 0.00, 0.0, 0.0, 0.1, 0.0, 40, ""),
    ("6000000000905", "Nescafé Instant Coffee (Pure)", "Nescafé", "Beverage", 0.0, 0.00, 0.0, 0.0, 0.0, 0.0, 2, ""),

    # B10: Meats & Processed
    ("6000000001001", "Eskort Polony Red", "Eskort", "Processed Meat", 1.0, 2.50, 20.0, 8.0, 10.0, 0.0, 240, "E250,E316,E407"),
    ("6000000001002", "Rainbow Chicken Frozen Drumsticks", "Rainbow", "Frozen Meat", 0.0, 0.50, 15.0, 5.0, 20.0, 0.0, 220, ""),
    ("6000000001003", "Enterprise Beef Boerewors", "Enterprise", "Processed Meat", 1.0, 1.50, 30.0, 15.0, 15.0, 0.0, 350, "E223,E300"),
    ("6000000001004", "Sea Harvest Hake Medallions", "Sea Harvest", "Frozen Fish", 0.0, 0.50, 2.0, 0.5, 18.0, 0.0, 90, ""),

    # B11: General Household & Snacks
    ("6000000001101", "Sunlight Dishwashing Liquid", "Sunlight", "Household", 0.0, 0.00, 0.0, 0.0, 0.0, 0.0, 0, ""), # Non-food item for demo of "not found" or category filtering
    ("6000000001102", "Koo Green Beans (Salted)", "Koo", "Canned Veg", 3.0, 0.40, 0.1, 0.0, 1.5, 3.0, 30, ""),
    ("6000000001103", "Oros Orange Squash", "Oros", "Drink Mix", 35.0, 0.05, 0.0, 0.0, 0.0, 0.0, 140, "E104,E110,E211"),
    ("6000000001104", "Selati Icing Sugar", "Selati", "Baking", 100.0, 0.00, 0.0, 0.0, 0.0, 0.0, 400, ""),
    ("6000000001105", "Albany Low GI White Bread", "Albany", "Bakery", 4.0, 0.45, 2.5, 0.5, 9.0, 5.0, 250, "E282"),
    ("6000000001106", "Kellogg's Special K", "Kellogg's", "Cereal", 15.0, 0.80, 1.0, 0.2, 10.0, 1.0, 380, "E320"),
    ("6000000001107", "Black Cat Crunchy Peanut Butter", "Black Cat", "Spread", 8.0, 0.50, 48.0, 8.0, 25.0, 5.0, 600, "E471"),
    ("6000000001108", "Knorr Aromat Seasoning", "Knorr", "Seasoning", 1.0, 15.0, 0.1, 0.0, 1.0, 0.0, 50, "E621,E631"),
    ("6000000001109", "Bakers Eet-Sum-Mor Biscuits", "Bakers", "Snack", 20.0, 0.60, 22.0, 12.0, 6.0, 1.0, 500, "E450,E500"),
    ("6000000001110", "Simba NikNaks Cheese", "Simba", "Snack", 1.0, 1.50, 28.0, 4.0, 6.0, 2.0, 510, "E621,E635,E110"),

    # B12: Additional Staples
    ("6000000001201", "Sasko Self-Raising Flour", "Sasko", "Baking", 0.5, 0.10, 1.0, 0.2, 10.0, 3.0, 360, "E500,E450"),
    ("6000000001202", "Nulaid Large Eggs", "Nulaid", "Protein", 0.0, 0.40, 10.0, 3.0, 13.0, 0.0, 140, ""),
    ("6000000001203", "Robertsons Rajah Hot Curry Powder", "Robertsons", "Spice", 0.0, 0.00, 10.0, 1.0, 10.0, 30.0, 350, "E102,E110"),
    ("6000000001204", "Huletts Caster Sugar", "Huletts", "Baking", 100.0, 0.00, 0.0, 0.0, 0.0, 0.0, 400, ""),
    ("6000000001205", "Sasko Sam's Cake Mix Vanilla", "Sasko", "Baking", 35.0, 0.50, 12.0, 6.0, 4.0, 1.0, 400, "E471,E150"),
    ("6000000001206", "Clover Medium Fat Cottage Cheese", "Clover", "Dairy", 3.0, 0.60, 4.0, 2.5, 10.0, 0.0, 90, ""),
    ("6000000001207", "Lipton Black Tea", "Lipton", "Beverage", 0.0, 0.00, 0.0, 0.0, 0.0, 0.0, 0, ""),
    ("6000000001208", "Five Roses Rooibos Tea", "Five Roses", "Beverage", 0.0, 0.00, 0.0, 0.0, 0.0, 0.0, 0, ""),
    ("6000000001209", "Kelloggs All-Bran Flakes", "Kellogg's", "Cereal", 20.0, 0.50, 1.5, 0.3, 10.0, 15.0, 340, ""),
    ("6000000001210", "Albany White Sliced Bread", "Albany", "Bakery", 4.5, 0.50, 2.5, 0.5, 8.0, 2.5, 260, "E282"),

    # B13: Frozen & Ice Cream
    ("6000000001301", "Ola Rich 'n Creamy Vanilla", "Ola", "Ice Cream", 22.0, 0.10, 12.0, 8.0, 4.0, 0.0, 240, "E471,E412,E160a"),
    ("6000000001302", "Natures Garden Mixed Veg", "Natures Garden", "Frozen Veg", 4.0, 0.10, 0.1, 0.0, 2.0, 4.0, 40, ""),
    ("6000000001303", "Nando's Peri-Peri Sauce (Medium)", "Nando's", "Sauce", 4.0, 2.50, 5.0, 1.0, 1.0, 1.0, 80, "E415"),
    ("6000000001304", "Beacon Sparkles", "Beacon", "Sweets", 65.0, 0.10, 5.0, 3.0, 1.0, 0.0, 350, "E102,E129,E133"),
    ("6000000001305", "Bakers Salticrax", "Bakers", "Snack", 1.0, 1.50, 20.0, 5.0, 8.0, 3.0, 450, "E503"),
    ("6000000001306", "Willards Crinkle Cut Chips", "Willards", "Snack", 0.5, 1.40, 30.0, 4.0, 6.0, 3.0, 530, "E621,E631"),

    # B14: Spreads & Fats
    ("6000000001401", "Golden Cloud Cake Flour", "Golden Cloud", "Baking", 0.5, 0.00, 1.0, 0.2, 10.0, 3.0, 360, ""),
    ("6000000001402", "Sunfoil Sunflower Oil", "Sunfoil", "Oil", 0.0, 0.00, 100.0, 10.0, 0.0, 0.0, 900, ""),
    ("6000000001403", "Liqui-Fruit Cranberry 100% (Dummy)", "Liqui-Fruit", "Juice", 9.0, 0.00, 0.0, 0.0, 0.1, 0.0, 40, ""),
    ("6000000001404", "Clover Full Cream Yoghurt Strawberry", "Clover", "Dairy", 12.0, 0.20, 3.0, 2.0, 4.0, 0.0, 90, "E120"),
    ("6000000001405", "Tastic Parboiled Rice", "Tastic", "Grain", 0.2, 0.00, 0.0, 0.0, 7.0, 0.8, 360, ""),

    # B15: Last 5 for 104 Total
    ("6000000001501", "Albany Low GI Seeded Bread", "Albany", "Bakery", 3.0, 0.35, 4.0, 0.8, 10.0, 8.0, 270, "E282,E300"),
    ("6000000001502", "Woolworths Full Cream Milk", "Woolworths", "Dairy", 4.7, 0.10, 3.3, 2.1, 3.4, 0.0, 61, ""),
    ("6000000001503", "Kellogg's Rice Krispies", "Kellogg's", "Cereal", 10.0, 0.70, 0.5, 0.1, 6.0, 0.5, 380, ""),
    ("6000000001504", "All Gold Smooth Apricot Jam", "All Gold", "Jam", 60.0, 0.05, 0.1, 0.0, 0.1, 0.5, 250, "E202,E211"),
    ("6000000001505", "Simba Chippies Salt & Vinegar", "Simba", "Snack", 0.5, 1.40, 30.0, 4.0, 6.0, 3.0, 530, "E621,E631"),
]


# --- Database Functions ---

def create_connection():
    """Create a database connection to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
    return conn

def create_table(conn):
    """Create the products table in the database."""
    sql_create_products_table = """
    CREATE TABLE IF NOT EXISTS products (
        barcode TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        brand TEXT,
        category TEXT,
        sugar REAL,
        salt REAL,
        fat REAL,
        saturated_fat REAL,
        protein REAL,
        fiber REAL,
        calories INTEGER,
        additives TEXT
    );
    """
    try:
        c = conn.cursor()
        c.execute(sql_create_products_table)
    except sqlite3.Error as e:
        print(f"Error creating table: {e}")

def load_sample_data(conn):
    """Load sample data into the products table."""
    sql_insert_product = """
    INSERT INTO products (barcode, name, brand, category, sugar, salt, fat, saturated_fat, protein, fiber, calories, additives)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    try:
        c = conn.cursor()
        c.executemany(sql_insert_product, SAMPLE_PRODUCTS)
        conn.commit()
    except sqlite3.IntegrityError as e:
        # This prevents the app from crashing if it tries to insert the same data twice
        print("Warning: Sample data already exists or duplicate barcodes found.")
    except sqlite3.Error as e:
        print(f"Error loading sample data: {e}")

def get_product_by_barcode(conn, barcode):
    """Retrieve a product by its barcode."""
    sql = "SELECT * FROM products WHERE barcode=?"
    try:
        c = conn.cursor()
        c.execute(sql, (barcode,))
        row = c.fetchone()
        if row:
            # Map the database row to a dictionary for easier API consumption
            return {
                "barcode": row[BARCODE],
                "name": row[NAME],
                "brand": row[BRAND],
                "category": row[CATEGORY],
                "nutrition_per_100g": {
                    "sugar": row[SUGAR],
                    "salt": row[SALT],
                    "fat": row[FAT],
                    "saturated_fat": row[SAT_FAT],
                    "protein": row[PROTEIN],
                    "fiber": row[FIBER],
                    "calories": row[CALORIES],
                },
                "additives_raw": row[ADDITIVES] # Raw string (e.g., "E621,E631")
            }
        return None
    except sqlite3.Error as e:
        print(f"Database error during lookup: {e}")
        return None

def initialize_database():
    """Connects to or creates the DB, and ensures tables and data are loaded."""
    conn = create_connection()
    if conn is not None:
        create_table(conn)
        load_sample_data(conn)
        conn.close()
        print(f"Database initialized and {len(SAMPLE_PRODUCTS)} sample products loaded successfully.")
    else:
        print("Error! Cannot create the database connection.")

def check_db_exists():
    """Checks if the database file exists and initializes it if not."""
    if not os.path.exists(DB_NAME):
        print(f"Database file not found. Initializing database...")
        initialize_database()
    else:
        print("Database file found. Ready to use.")

if __name__ == '__main__':
    # Test function to run directly
    check_db_exists()
    conn = create_connection()
    if conn:
        product = get_product_by_barcode(conn, "6009900000001")
        if product:
            print("\nTest Product Lookup (Clover Milk):")
            print(f"Name: {product['name']}, Sugar: {product['nutrition_per_100g']['sugar']}g")
        conn.close()