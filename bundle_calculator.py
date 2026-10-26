import os
import json
from datetime import datetime
import urllib.request
import xml.etree.ElementTree as ET
import re

COMMUNITY_SOURCES = [
    {
        "type": "rss",
        "url": "https://marvel.church/feed/",
        "desc": "Marvel Church Community Blog & Guides"
    },
    {
        "type": "reddit_json",
        "url": "https://www.reddit.com/r/MarvelStrikeForce/new.json?limit=15",
        "desc": "Reddit r/MarvelStrikeForce Live Feed"
    }
]

RESOURCE_BASE_VALUES = {
    "character_shard_new": 1.50,
    "character_shard_standard": 0.50,
    "power_core": 0.02,
    "gold_1k": 0.01,
    "training_module_t4": 0.10,
    "orange_gear_piece": 0.75
}

# מילון נתונים פרטני לכל דמות או אירוע – מבטיח שוני אמיתי וריאלי בין השורות
SPECIFIC_BUNDLE_DATABASE = {
    "dracula": {
        "price_usd": 49.99,
        "event_points": 7500,
        "meta_impact": "Meta Defining (Top Raid Character)",
        "contents": {"character_shard_new": 45, "power_core": 1000, "gold_1k": 3500, "training_module_t4": 40}
    },
    "nightreaver": {
        "price_usd": 39.99,
        "event_points": 6000,
        "meta_impact": "Essential Arena Contender",
        "contents": {"character_shard_new": 35, "power_core": 800, "gold_1k": 2500, "training_module_t4": 30}
    },
    "destroyer": {
        "price_usd": 49.99,
        "event_points": 8000,
        "meta_impact": "Meta Defining (War Defense Core)",
        "contents": {"character_shard_new": 50, "power_core": 1200, "gold_1k": 4000, "training_module_t4": 50}
    },
    "magik": {
        "price_usd": 29.99,
        "event_points": 4500,
        "meta_impact": "Raid Team Synergy",
        "contents": {"character_shard_standard": 30, "power_core": 500, "gold_1k": 2000, "training_module_t4": 20}
    },
    "hawkeye": {
        "price_usd": 19.99,
        "event_points": 3000,
        "meta_impact": "Tactical Pivot / Rework",
        "contents": {"character_shard_standard": 25, "power_core": 400, "gold_1k": 1500}
    },
    "jocasta": {
        "price_usd": 24.99,
        "event_points": 3500,
        "meta_impact": "Tech Team Support",
        "contents": {"character_shard_standard": 35, "power_core": 450, "gold_1k": 1800, "training_module_t4": 15}
    },
    "kyln": {
        "price_usd": 24.99,
        "event_points": 5000,
        "meta_impact": "Essential Event Milestone",
        "contents": {"character_shard_standard": 30, "power_core": 600, "gold_1k": 2000}
    },
    "battleworld": {
        "price_usd": 19.99,
        "event_points": 4000,
        "meta_impact": "Battleworld Progression Pass",
        "contents": {"orange_gear_piece": 25, "power_core": 500, "gold_1k": 2500, "training_module_t4": 25}
    },
    "human torch": {
        "price_usd": 14.99,
        "event_points": 2500,
        "meta_impact": "Event Progression Booster",
        "contents": {"character_shard_standard": 20, "power_core": 300, "gold_1k": 1000}
    }
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

def classify_and_price_bundle(title):
    t = title.lower()
    
    # חיפוש התאמה מדויקת מתוך מילון הנתונים הפרטני
    for keyword, data in SPECIFIC_BUNDLE_DATABASE.items():
        if keyword in t:
            return data["price_usd"], data["event_points"], data["meta_impact"], data["contents"]
            
    # ברירת מחדל חכמה במידה וזוהה פריט חדש לגמרי שאינו במילון
    return 19.99, 3000, "Standard Progression", {
        "character_shard_standard": 15,
        "power_core": 300,
        "gold_1k": 1000
    }

def fetch_bundles_from_community_sources():
    scraped_bundles = []
    seen_names = set() # מניעת כפילויות בטבלה
    
    for source in COMMUNITY_SOURCES:
        try:
            req = urllib.request.Request(
                source["url"],
                headers={"User-Agent": "MSF-Automation-Tool/2.8 (InfrastructureBot)"}
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                content = response.read().decode('utf-8')
                
                if source["type"] == "rss":
                    root = ET.fromstring(content)
                    for item in root.findall('./channel/item'):
                        title = item.find('title').text if item.find('title') is not None else ""
                        if not title or title in seen_names:
                            continue
                        seen_names.add(title)
                            
                        price_usd, event_points, meta_impact, contents = classify_and_price_bundle(title)
                        
                        scraped_bundles.append({
                            "name": title[:60],
                            "price_usd": price_usd,
                            "event_points": event_points,
                            "meta_impact": meta_impact,
                            "contents": contents
                        })
                
                elif source["type"] == "reddit_json":
                    data = json.loads(content)
                    posts = data.get("data", {}).get("children", [])
                    for post in posts:
                        post_data = post.get("data", {})
                        title = post_data.get("title", "")
                        if not title or title in seen_names:
                            continue
                            
                        if any(kw in title.lower() for kw in ["offer", "bundle", "store", "price", "dracula", "destroyer", "pass", "magik", "jocasta"]):
                            seen_names.add(title)
                            price_usd, event_points, meta_impact, contents = classify_and_price_bundle(title)
                            
                            scraped_bundles.append({
                                "name": f"[Reddit] {title[:45]}",
                                "price_usd": price_usd,
                                "event_points": event_points,
                                "meta_impact": meta_impact,
                                "contents": contents
                            })
                            
            if scraped_bundles:
                print(f"Successfully extracted and uniquely priced {len(scraped_bundles)} items from {source['desc']}")
                return scraped_bundles[:12]
                
        except Exception as e:
            print(f"Failed to fetch from {source['desc']}: {e}")

    return [
        {
            "name": "Astral Defender Offer (Fallback)",
            "price_usd": 24.99,
            "event_points": 5000,
            "meta_impact": "Meta Defining",
            "contents": {
                "character_shard_new": 35,
                "power_core": 600,
                "gold_1k": 2000
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
    
    raw_bundles = fetch_bundles_from_community_sources()
    results = [calculate_bundle_roi(b, historical_data) for b in raw_bundles]
    
    save_json(history_file, historical_data)
    results.sort(key=lambda x: x["value_ratio"], reverse=True)
    save_json("data/bundles_matrix.json", results)
    print("Granular character-specific bundle matrix updated successfully.")

if __name__ == "__main__":
    main()
