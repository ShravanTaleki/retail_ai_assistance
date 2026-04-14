import json, random
from datetime import date, timedelta
from faker import Faker
import pandas as pd
from config import DATA_DIR

fake = Faker()
DATA_DIR.mkdir(exist_ok=True)
locs = ["New York", "Austin", "Seattle", "Chicago", "Miami"]
brands = ["Nike", "Adidas", "Zara", "H&M", "Uniqlo", "Puma"]
colors = ["Black", "Blue", "White", "Green", "Beige", "Red"]
cats = ["Sneakers", "Jacket", "Jeans", "T-Shirt", "Dress", "Bag"]

def get_age_group(age):
    if age < 18: return "Teen (13-17)"
    if age <= 35: return "Young Adult (18-35)"
    if age <= 55: return "Adult (36-55)"
    return "Senior (55+)"

users = []
for i in range(1, 181):
    age = random.randint(13, 65)
    u = {
        "user_id": i, 
        "name": fake.name(), 
        "age": age,
        "age_group": get_age_group(age),
        "gender": random.choice(["Menswear", "Womenswear", "Unisex/Neutral"]),
        "location": random.choice(locs), 
        "budget": random.randint(50, 400), 
        "brand_affinity": random.choice(brands), 
        "favorite_colors": ", ".join(random.sample(colors, 2))
    }
    users.append(u)
products = []
for i in range(1, 241):
    row = {"product_id": i, "category": random.choice(cats), "brand": random.choice(brands), "color": random.choice(colors), "price": random.randint(25, 250)}
    row["product"] = f"{row['brand']} {row['color']} {row['category']}"
    products.append(row)
purchases = [{"user_id": u["user_id"], "product_id": p["product_id"], "product": p["product"], "days_ago": random.randint(1, 90)} for u in users for p in random.sample(products, random.randint(2, 5))]
trends = [{"location": loc, "trend": f"{random.choice(colors)} {random.choice(cats)}", "score": random.randint(60, 99)} for loc in locs for _ in range(6)]
social = [{"user_id": u["user_id"], "peer_id": peer["user_id"]} for u in users for peer in random.sample([x for x in users if x["user_id"] != u["user_id"]], 3)]
events = [{"name": f"{random.choice(['Summer Sale', 'Music Fest', 'Office Meetup', 'Wedding Expo', 'Street Fair'])} {i}", "location": random.choice(locs), "date": str(date.today() + timedelta(days=random.randint(1, 45))), "theme": random.choice(["casual", "formal", "sporty", "travel"])} for i in range(1, 21)]

for name, rows in {"users": users, "products": products, "past_purchases": purchases, "trends": trends, "social_networks": social}.items():
    pd.DataFrame(rows).to_csv(DATA_DIR / f"{name}.csv", index=False)
(DATA_DIR / "events.json").write_text(json.dumps(events, indent=2), encoding="utf-8")
print("Synthetic retail data created.")
