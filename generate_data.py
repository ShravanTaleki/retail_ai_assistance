"""Generate synthetic general-retail data for the AI Agent demo."""
import json, random
from datetime import date, timedelta
from faker import Faker
import pandas as pd
from config import DATA_DIR

fake = Faker()
DATA_DIR.mkdir(exist_ok=True)

# ── Locations ──────────────────────────────────────────────────────────────────
LOCATIONS = ["New York", "Austin", "Seattle", "Chicago", "Miami",
             "San Francisco", "Denver", "Boston", "Los Angeles", "Dallas"]

# ── Brands ─────────────────────────────────────────────────────────────────────
BRANDS = ["Apple", "Sony", "Samsung", "Dyson", "Nike", "Adidas",
          "AmazonBasics", "Bose", "Philips", "Instant Pot"]

# ── Colors / finishes ─────────────────────────────────────────────────────────
COLORS = ["Black", "White", "Silver", "Navy", "Charcoal", "Forest Green"]

# ── Category → item‑type map (general retail) ─────────────────────────────────
CATEGORY_ITEMS: dict[str, list[str]] = {
    "Electronics":     ["Wireless Headphones", "Bluetooth Speaker", "Smartwatch",
                        "Phone Case", "Laptop Sleeve"],
    "Home & Kitchen":  ["Air Fryer", "Ceramic Mug", "Throw Blanket",
                        "Scented Candle", "Coffee Maker"],
    "Fitness":         ["Resistance Bands", "Non-slip Yoga Mat",
                        "Adjustable Dumbbells", "Foam Roller", "Jump Rope"],
    "Beauty":          ["Hydrating Face Serum", "Mineral Sunscreen",
                        "Organic Lip Balm", "Nourishing Hair Oil",
                        "Daily Moisturizer"],
    "Apparel":         ["Cotton T-Shirt", "Denim Jeans", "Zip Hoodie",
                        "Walking Sneakers", "Winter Jacket"],
}

CATEGORIES = list(CATEGORY_ITEMS.keys())

# ── Primary interest options (replaces Menswear / Womenswear) ─────────────────
INTERESTS = ["Electronics", "Home & Kitchen", "Fitness", "Beauty", "Apparel"]

# ── Age helpers ────────────────────────────────────────────────────────────────
def _age_group(age: int) -> str:
    if age < 18:  return "Teen (13-17)"
    if age <= 35: return "Young Adult (18-35)"
    if age <= 55: return "Adult (36-55)"
    return "Senior (55+)"


# ═══════════════════════════════════════════════════════════════════════════════
# 1️⃣  Users
# ═══════════════════════════════════════════════════════════════════════════════
users = []
for i in range(1, 201):
    age = random.randint(16, 70)
    users.append({
        "user_id": i,
        "name": fake.name(),
        "age": age,
        "age_group": _age_group(age),
        "primary_interest": random.choice(INTERESTS),
        "location": random.choice(LOCATIONS),
        "budget": random.randint(30, 500),
        "brand_affinity": random.choice(BRANDS),
        "favorite_colors": ", ".join(random.sample(COLORS, 2)),
    })

# ═══════════════════════════════════════════════════════════════════════════════
# 2️⃣  Products  (~300 items across all categories)
# ═══════════════════════════════════════════════════════════════════════════════
products = []
pid = 1
for _ in range(300):
    cat = random.choice(CATEGORIES)
    item = random.choice(CATEGORY_ITEMS[cat])
    brand = random.choice(BRANDS)
    color = random.choice(COLORS)
    price = random.randint(10, 450)
    products.append({
        "product_id": pid,
        "category": cat,
        "brand": brand,
        "color": color,
        "price": price,
        "product": f"{brand} {color} {item}",
    })
    pid += 1

# ═══════════════════════════════════════════════════════════════════════════════
# 3️⃣  Purchase history
# ═══════════════════════════════════════════════════════════════════════════════
purchases = [
    {"user_id": u["user_id"], "product_id": p["product_id"],
     "product": p["product"], "days_ago": random.randint(1, 90)}
    for u in users
    for p in random.sample(products, random.randint(2, 5))
]

# ═══════════════════════════════════════════════════════════════════════════════
# 4️⃣  Trends  (full product names so trend_tool can display them directly)
# ═══════════════════════════════════════════════════════════════════════════════
trends = []
for loc in LOCATIONS:
    for _ in range(3):
        p = random.choice(products)
        trends.append({"location": loc, "trend": p["product"],
                       "score": random.randint(60, 99)})

# ═══════════════════════════════════════════════════════════════════════════════
# 5️⃣  Social network
# ═══════════════════════════════════════════════════════════════════════════════
social = [
    {"user_id": u["user_id"], "peer_id": peer["user_id"]}
    for u in users
    for peer in random.sample([x for x in users if x["user_id"] != u["user_id"]], 3)
]

# ═══════════════════════════════════════════════════════════════════════════════
# 6️⃣  Events calendar
# ═══════════════════════════════════════════════════════════════════════════════
EVENT_NAMES = ["Summer Sale", "Tech Expo", "Fitness Fair", "Home Show",
               "Beauty Fest", "Back to School", "Holiday Blowout",
               "Flash Deal Day", "Founders Day Sale", "Spring Clearance"]
events = [
    {"name": f"{random.choice(EVENT_NAMES)} {i}",
     "location": random.choice(LOCATIONS),
     "date": str(date.today() + timedelta(days=random.randint(1, 45))),
     "theme": random.choice(["deals", "new arrivals", "seasonal", "clearance"])}
    for i in range(1, 21)
]

# ═══════════════════════════════════════════════════════════════════════════════
# 💾  Write everything
# ═══════════════════════════════════════════════════════════════════════════════
for name, rows in {"users": users, "products": products,
                    "past_purchases": purchases, "trends": trends,
                    "social_networks": social}.items():
    pd.DataFrame(rows).to_csv(DATA_DIR / f"{name}.csv", index=False)

(DATA_DIR / "events.json").write_text(json.dumps(events, indent=2), encoding="utf-8")
print(f"✅  Generated {len(users)} users, {len(products)} products, "
      f"{len(purchases)} purchases, {len(trends)} trends, "
      f"{len(social)} social edges, {len(events)} events.")
