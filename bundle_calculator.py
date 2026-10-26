import os
import json
from datetime import datetime

# 1. מחירון בסיס (Baseline Valuation) למשאבים במשחק
# מייצג את השווי הדולרי האמיתי או השקול של כל יחידת מששאב על בסיס רכישות סטנדרטיות
RESOURCE_BASE_VALUES = {
    "character_shard_new": 1.50,  # שארד של דמות חדשה/מבוקשת
    "character_shard_standard": 0.50, # שארד רגיל
    "power_core": 0.02,           # שווי פאוור קור
    "gold_1k": 0.01,              # שווי לכל 1,000 זהב
    "training_module_t4": 0.10,   # מודול אימון מתקדם
    "orange_gear_piece": 0.75     # חלק ציוד כתום
}

def calculate_bundle_roi(bundle):
    """
    מחשב את השווי הכולל של הבאנדל מול המחיר שלו ומחזיר ציון ROI
    """
    total_value = 0.0
    
    # חישוב השווי של כל רכיב בבאנדל
    for item, quantity in bundle["contents"].items():
        unit_value = RESOURCE_BASE_VALUES.get(item, 0.0)
        total_value += quantity * unit_value
        
    price = bundle["price_usd"]
    
    # חישוב יחס ערך למחיר (Value Ratio) וציון תשואה (ROI %)
    value_ratio = (total_value / price) if price > 0 else 0.0
    roi_percentage = ((total_value - price) / price) * 100 if price > 0 else 0.0
    
    return {
        "bundle_name": bundle["name"],
        "price_usd": price,
        "calculated_value_usd": round(total_value, 2),
        "value_ratio": round(value_ratio, 2),
        "roi_percentage": round(roi_percentage, 1),
        "verdict": get_verdict(value_ratio),
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def get_verdict(ratio):
    """
    מחזיר דירוג חסד (Verdict) לחבילה בהתאם ליחס הערך
    """
    if ratio >= 4.0:
        return "🔥 Must Buy (ערך יוצא דופן)"
    elif ratio >= 2.5:
        return "✅ Good Value (שווה קנייה)"
    elif ratio >= 1.5:
        return "⚖️ Fair (גבולי / תלוי צורך)"
    else:
        return "❌ Trap Offer (מלכודת תקציב)"

def process_store_offers():
    # רשימת חבילות לדוגמה (שבשלב מתקדם אפשר למשוך אוטומטית או מקובץ JSON חיצוני)
    raw_bundles = [
        {
            "name": "Mega Character Shard Blitz Pack",
            "price_usd": 19.99,
            "contents": {
                "character_shard_new": 30,
                "power_core": 500,
                "gold_1k": 1500
            }
        },
        {
            "name": "Starter Gear Booster",
            "price_usd": 4.99,
            "contents": {
                "orange_gear_piece": 5,
                "training_module_t4": 20,
                "gold_1k": 200
            }
        },
        {
            "name": "Overpriced Whale Trap Bundle",
            "price_usd": 49.99,
            "contents": {
                "character_shard_standard": 10,
                "power_core": 100
            }
        }
    ]
    
    results = [calculate_bundle_roi(b) for b in raw_bundles]
    
    # מיון החבילות מהמשתלמת ביותר לגרועה ביותר לפי יחס הערך
    results.sort(key=lambda x: x["value_ratio"], reverse=True)
    
    return results

def save_matrix_data(data):
    os.makedirs("data", exist_ok=True)
    file_path = "data/bundles_matrix.json"
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Bundle ROI Matrix successfully generated and saved to {file_path}")

if __name__ == "__main__":
    matrix_data = process_store_offers()
    save_matrix_data(matrix_data)
