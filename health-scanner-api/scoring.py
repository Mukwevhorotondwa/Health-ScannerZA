# --- Scoring Constants ---
BASE_SCORE = 100
MAX_DEDUCTION_ADDITIVES = 15
DEDUCTION_PER_ADDITIVE = 3

def calculate_health_score(product_data, additives_list):
    """
    Calculates the Health Score (0-100) based on nutritional data (per 100g) and additives.
    
    Args:
        product_data (dict): Product nutrition (sugar, salt, sat_fat, protein, fiber) per 100g.
        additives_list (list): List of additive E-numbers/names.
        
    Returns:
        int: The final health score clamped between 0 and 100.
    """
    score = BASE_SCORE
    sugar = product_data.get('sugar', 0.0)
    salt = product_data.get('salt', 0.0)
    saturated_fat = product_data.get('saturated_fat', 0.0)
    fiber = product_data.get('fiber', 0.0)
    protein = product_data.get('protein', 0.0)
    num_additives = len(additives_list)
    
    # --- Deductions ---
    
    # Sugar Content (Thresholds: >15g, 5-15g)
    if sugar > 15.0:
        score -= 30
    elif sugar >= 5.0:
        score -= 15
        
    # Salt Content (Thresholds: >1.5g, 0.5-1.5g)
    if salt > 1.5:
        score -= 25
    elif salt >= 0.5:
        score -= 10
        
    # Saturated Fat (Thresholds: >5g, 2-5g)
    if saturated_fat > 5.0:
        score -= 20
    elif saturated_fat >= 2.0:
        score -= 10
        
    # Additives (Deduction: -3 points each, max -15)
    additive_deduction = min(num_additives * DEDUCTION_PER_ADDITIVE, MAX_DEDUCTION_ADDITIVES)
    score -= additive_deduction
    
    # --- Bonuses ---
    
    # Fiber (Thresholds: ≥6g, 3-6g)
    if fiber >= 6.0:
        score += 5
    elif fiber >= 3.0:
        score += 2
        
    # Protein (Thresholds: ≥10g, 5-10g)
    if protein >= 10.0:
        score += 5
    elif protein >= 5.0:
        score += 2
        
    # --- Final Score Clamping ---
    # Max(0, Min(100, calculated_score))
    final_score = max(0, min(100, int(round(score))))
    
    return final_score