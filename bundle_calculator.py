import os
import json
from datetime import datetime
import urllib.request

# כתובת חיצונית אמינה (למשל: קובץ JSON ציבורי או Google Sheets שמוגדר ל-CSV)
EXTERNAL_DATA_URL = "https://raw.githubusercontent.com/username/msf-community-feeds/main/live_bundles.json"

# מחירון בסיס (Baseline Valuation) למשאבים במשחק
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

def fetch_external_bundles():
    """
    מושך נתונים ממקור חיצוני יציב (כגון קובץ JSON ציבורי מרוחק)
    """
    try:
        req = urllib.request.Request(
            EXTERNAL_DATA_URL,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            if isinstance(data, list) and len(data) > 0:
                print("Successfully fetched live data from external source.")
                return data
    except Exception as e:
        print(f"External fetch failed ({e}), falling back to local dataset.")
    
    # מנגנון גיבוי מקומי בטוח (Fallback)
    return [
        {
            "name": "Astral Defender Offer (Live Feed)",
            "price_usd": 24.99,
            "event_points": 5000,
            "meta_impact": "Meta Defining (Essential for Raids/CC)",
            "contents": {
                "character_shard_new": 35,
                "power_core": 600,
                "gold_1k": 2000
            }
        },
        {
            "name": "Alliance War Gear Cache",
            "price_usd": 9.99,
            "event_points": 1500,
            "meta_impact": "Standard Progression",
            "contents": {
                "orange_gear_piece": 10,
                "training_module_t4": 50,
                "gold_1k": 500
            }
        }
    ]

def calculate_bundle_roi(bundle, historical_data):
    total_value = 0.0
    for item, quantity in bundle.get("contents", {}).items():
        unit_value = RESOURCE_BASE_VALUES.get(item, 0.0)
        total_value += quantity * unit_value
        
    price = bundle["price_usd"]
    value_ratio = (total_value / price) if price > 0 else 0.0
    roi_percentage = ((total_value - price) / price) * 100 if price > 0 else 0.0
    
    bundle_name = bundle["name"]
    past_low = historical_data.get(bundle_name, price)
    is_atl = price <= past_low
    new_historical_low = min(price, past_low)
    historical_data[bundle_name] = new_historical_low
    
    total_points = bundle.get("event_points", 1000)
    points_per_dollar = round(total_points / price, 1) if price > 0 else 0
    cores_saved = int(total_value * 50)
    days_saved = round(total_value / 5.0, 1)
    meta_impact = bundle.get("meta_impact", "Standard Progression")
    verdict = get_verdict(value_ratio, is_atl)

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

def main():
    history_file = "data/bundles_history.json"
    historical_data = load_json(history_file, {})
    
    # שליפת הנתונים (ממקור חיצוני עם גיבוי אוטומטי)
    raw_bundles = fetch_external_bundles()
    
    results = [calculate_bundle_roi(b, historical_data) for b in raw_bundles]
    
    save_json(history_file, historical_data)
    results.sort(key=lambda x: x["value_ratio"], reverse=True)
    save_json("data/bundles_matrix.json", results)
    print("Bundle matrix successfully updated via robust external data pipeline.")

if __name__ == "__main__":
    main()
