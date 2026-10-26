import os
import json
from datetime import datetime

# מחירון בסיס (Baseline Valuation) למשאבים במשחק
RESOURCE_BASE_VALUES = {
    "character_shard_new": 1.50,
    "character_shard_standard": 0.50,
    "power_core": 0.02,
    "gold_1k": 0.01,
    "training_module_t4": 0.10,
    "orange_gear_piece": 0.75
}

def calculate_bundle_roi(bundle):
    """
    מחשב את השווי הכולל של הבאנדל, משקלל נקודות אירוע, שפל היסטורי ומטה
    """
    total_value = 0.0
    
    # חישוב השווי של כל רכיב בבאנדל
    for item, quantity in bundle["contents"].items():
        unit_value = RESOURCE_BASE_VALUES.get(item, 0.0)
        total_value += quantity * unit_value
        
    price = bundle["price_usd"]
    value_ratio = (total_value / price) if price > 0 else 0.0
    roi_percentage = ((total_value - price) / price) * 100 if price > 0 else 0.0
    
    # 1. מעקב שפל היסטורי (Historical Low & Price Tracking)
    historical_low = bundle.get("historical_low_usd", price)
    is_all_time_low = price <= historical_low
    
    # 2. שווי תרגום לאנרגיית קמפיין ופאוור קורס (Farming Equivalency)
    power_cores_saved = int(total_value / 0.02)
    farming_days_saved = round(power_cores_saved / 250, 1) # הערכה יומית ממוצעת
    
    # 3. ציון נקודות לאירוע חיים לכל דולר (Event Milestone Points-per-Dollar)
    event_points = bundle.get("event_milestone_points", 0)
    points_per_dollar = round(event_points / price, 1) if price > 0 else 0
    
    # 4. השפעה על המטה במשחק (Meta Impact)
    meta_impact = bundle.get("meta_impact", "Standard Progression")
    verdict = get_advanced_verdict(value_ratio, is_all_time_low, meta_impact)
    
    return {
        "bundle_name": bundle["name"],
        "price_usd": price,
        "historical_low_usd": historical_low,
        "is_all_time_low": is_all_time_low,
        "calculated_value_usd": round(total_value, 2),
        "value_ratio": round(value_ratio, 2),
        "roi_percentage": round(roi_percentage, 1),
        "event_milestone": {
            "total_points": event_points,
            "points_per_dollar": points_per_dollar
        },
        "farming_equivalency": {
            "estimated_power_cores_saved": power_cores_saved,
            "estimated_farming_days_saved": farming_days_saved
        },
        "meta_impact": meta_impact,
        "verdict": verdict,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def get_advanced_verdict(ratio, is_atl, meta):
    """
    מחזיר דירוג חסד מתקדם המשלב ערך מתמטי, היסטוריית מחיר ורלוונטיות למטה
    """
    if "Obsolete" in meta or "Out of Meta" in meta:
        return "⚠️ High Value, But Obsolete (זהירות: דמות מיושנת במטה)"
    elif ratio >= 4.0 and is_atl:
        return "🔥 Ultimate Buy (ערך שיא + שפל היסטורי נדיר)"
    elif ratio >= 3.0:
        return "⭐ Great Value (משתלם מאוד לאירועים)"
    elif ratio >= 2.0:
        return "✅ Good Value (שווה קנייה)"
    elif ratio >= 1.2:
        return "⚖️ Fair (גבולי / תלוי צורך אישי)"
    else:
        return "❌ Trap Offer (מלכודת תקציב - להימנע)"

def process_store_offers():
    # רשימת חבילות מעודכנת הכוללת את כל המדדים החדשים
    raw_bundles = [
        {
            "name": "Mega Character Shard Blitz Pack",
            "price_usd": 19.99,
            "historical_low_usd": 19.99,
            "event_milestone_points": 4500,
            "meta_impact": "Meta Defining (Essential for Raids/CC)",
            "contents": {
                "character_shard_new": 30,
                "power_core": 500,
                "gold_1k": 1500
            }
        },
        {
            "name": "Starter Gear Booster",
            "price_usd": 4.99,
            "historical_low_usd": 3.99, # נמכר בעבר בזול יותר
            "event_milestone_points": 800,
            "meta_impact": "Standard Progression",
            "contents": {
                "orange_gear_piece": 5,
                "training_module_t4": 20,
                "gold_1k": 200
            }
        },
        {
            "name": "Legacy Outdated Character Offer",
            "price_usd": 24.99,
            "historical_low_usd": 24.99,
            "event_milestone_points": 200,
            "meta_impact": "Obsolete / Out of Meta",
            "contents": {
                "character_shard_standard": 50,
                "gold_1k": 500
            }
        }
    ]
    
    results = [calculate_bundle_roi(b) for b in raw_bundles]
    results.sort(key=lambda x: x["value_ratio"], reverse=True)
    
    return results

def save_matrix_data(data):
    os.makedirs("data", exist_ok=True)
    file_path = "data/bundles_matrix.json"
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Advanced Bundle ROI Matrix successfully generated and saved to {file_path}")

if __name__ == "__main__":
    matrix_data = process_store_offers()
    save_matrix_data(matrix_data)
