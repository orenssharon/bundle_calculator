import os
import json
from datetime import datetime
import requests

# 1. מחירון בסיס (Baseline Valuation) למשאבים במשחק
RESOURCE_BASE_VALUES = {
    "character_shard_new": 1.50,
    "character_shard_standard": 0.50,
    "power_core": 0.02,
    "gold_1k": 0.01,
    "training_module_t4": 0.10,
    "orange_gear_piece": 0.75
}

def load_json(filepath, default_value):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default_value
    return default_value

def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def send_discord_webhook(bundle_name, verdict, price, roi):
    """
    שולח התראה אוטומטית לערוץ דיסקורד אם הבאנדל משתלם במיוחד
    """
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return
    
    payload = {
        "content": f"🚨 **התראת באנדל משתלם ב-MSF!**\n"
                   f"📦 **שם הבאנדל:** {bundle_name}\n"
                   f"💵 **מחיר:** ${price}\n"
                   f"📈 **ROI:** {roi}%\n"
                   f"🏷️ **דירוג:** {verdict}"
    }
    try:
        requests.post(webhook_url, json=payload)
    except Exception as e:
        print(f"Failed to send webhook: {e}")

def calculate_bundle_roi(bundle, historical_data):
    total_value = 0.0
    
    # חישוב השווי מתוך תוכן הבאנדל
    for item, quantity in bundle.get("contents", {}).items():
        unit_value = RESOURCE_BASE_VALUES.get(item, 0.0)
        total_value += quantity * unit_value
        
    price = bundle["price_usd"]
    value_ratio = (total_value / price) if price > 0 else 0.0
    roi_percentage = ((total_value - price) / price) * 100 if price > 0 else 0.0
    
    bundle_name = bundle["name"]
    
    # בדיקת שפל היסטורי מול מסד הנתונים
    past_low = historical_data.get(bundle_name, price)
    is_atl = price <= past_low
    new_historical_low = min(price, past_low)
    historical_data[bundle_name] = new_historical_low
    
    # נתונים נוספים
    total_points = bundle.get("event_points", 1000)
    points_per_dollar = round(total_points / price, 1) if price > 0 else 0
    cores_saved = int(total_value * 50)
    days_saved = round(total_value / 5.0, 1)
    meta_impact = bundle.get("meta_impact", "Standard Progression")
    
    verdict = get_verdict(value_ratio, is_atl)
    
    # הפעלת התראה במידה ומדובר במציאה חמה
    if "Great Value" in verdict:
        send_discord_webhook(bundle_name, verdict, price, round(roi_percentage, 1))

    return {
        "bundle_name": bundle_name,
        "price_usd": price,
        "historical_low_usd": new_historical_low,
        "is_all_time_low": is_atl,
        "calculated_value_usd": round(total_value, 2),
        "value_ratio": round(value_ratio, 2),
        "roi_percentage": round(roi_percentage, 1),
        "event_milestone": {
            "total_points": total_points,
            "points_per_dollar": points_per_dollar
        },
        "farming_equivalency": {
            "estimated_power_cores_saved": cores_saved,
            "estimated_farming_days_saved": days_saved
        },
        "meta_impact": meta_impact,
        "verdict": verdict,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def get_verdict(ratio, is_atl):
    if ratio >= 3.0:
        base = "⭐ Great Value (משתלם מאוד לאירועים)"
    elif ratio >= 1.8:
        base = "✅ Good Value (שווה קנייה)"
    elif ratio >= 1.2:
        base = "⚖️ Fair (גבולי / תלוי צורך אישי)"
    else:
        base = "❌ Trap Offer (מלכודת תקציב)"
        
    if is_atl:
        base += " [📉 שפל היסטורי!]"
    return base

def process_store_offers():
    input_file = "data/bundles_input.json"
    history_file = "data/bundles_history.json"
    
    # קובץ קלט לדוגמה אם אינו קיים
    default_input = [
        {
            "name": "Mega Character Shard Blitz Pack",
            "price_usd": 19.99,
            "event_points": 4500,
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
            "event_points": 800,
            "meta_impact": "Standard Progression",
            "contents": {
                "orange_gear_piece": 5,
                "training_module_t4": 20,
                "gold_1k": 200
            }
        }
    ]
    
    raw_bundles = load_json(input_file, default_input)
    if not os.path.exists(input_file):
        save_json(input_file, default_input)
        
    historical_data = load_json(history_file, {})
    
    results = []
    for b in raw_bundles:
        results.append(calculate_bundle_roi(b, historical_data))
        
    # שמירת נתוני ההשגחה ההיסטורית מעודכנים
    save_json(history_file, historical_data)
    
    # מיון מהמשתלם ביותר לגרוע ביותר
    results.sort(key=lambda x: x["value_ratio"], reverse=True)
    
    # שמירת התוצאה הסופית לשימוש הטבלה/אתר
    save_json("data/bundles_matrix.json", results)
    print("Bundle ROI Matrix successfully updated with history tracking and external inputs.")

if __name__ == "__main__":
    process_store_offers()
