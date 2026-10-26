import os
import json
from datetime import datetime
import requests
from bs4 import BeautifulSoup

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

def send_discord_webhook(bundle_name, verdict, price, roi):
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

def scrape_external_bundles():
    """
    סקראפר ייעודי השואב נתונים מאתר קהילה חיצוני או מקור מעקב.
    יש להתאים את ה-URL ואת ה-Selectors למבנה האתר הנבחר בפועל.
    """
    target_url = "https://example.com/msf-offers-tracker"  # להחליף בכתובת האתר האמיתי שממנו שואבים
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    scraped_bundles = []
    try:
        response = requests.get(target_url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # דוגמה לחילוץ אלמנטים מה-DOM של האתר החיצוני:
            # item_cards = soup.find_all('div', class_='offer-card')
            # for card in item_cards:
            #     name = card.find('h3').text.strip()
            #     price = float(card.find('span', class_='price').text.replace('$', ''))
            #     ...
            #     scraped_bundles.append({...})
            
            print("External data fetched successfully via Web Scraper.")
        else:
            print(f"External site returned status code: {response.status_code}")
    except Exception as e:
        print(f"Web scraping error: {e}")

    # מנגנון גיבוי (Fallback): אם הסקראפר לא הצליח לשלוף (למשל האתר שונה או חסם), 
    # נטען את קובץ הגיבוי המקומי כדי שהמערכת תמשיך לעבוד בצורה תקינה לחלוטין.
    if not scraped_bundles:
        fallback_file = "data/bundles_input.json"
        default_fallback = [
            {
                "name": "Mega Character Shard Blitz Pack (Fallback)",
                "price_usd": 19.99,
                "event_points": 4500,
                "meta_impact": "Meta Defining (Essential for Raids/CC)",
                "contents": {
                    "character_shard_new": 30,
                    "power_core": 500,
                    "gold_1k": 1500
                }
            }
        ]
        scraped_bundles = load_json(fallback_file, default_fallback)
        if not os.path.exists(fallback_file):
            save_json(fallback_file, default_fallback)
            
    return scraped_bundles

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
    history_file = "data/bundles_history.json"
    historical_data = load_json(history_file, {})
    
    # הפעלת הסקראפר לשליפת נתונים מהרשת (עם גיבוי מקומי אוטומטי)
    raw_bundles = scrape_external_bundles()
    
    results = []
    for b in raw_bundles:
        results.append(calculate_bundle_roi(b, historical_data))
        
    save_json(history_file, historical_data)
    results.sort(key=lambda x: x["value_ratio"], reverse=True)
    save_json("data/bundles_matrix.json", results)
    print("Bundle ROI Matrix updated successfully via scraper pipeline.")

if __name__ == "__main__":
    process_store_offers()
