import json
from datetime import date, datetime, timedelta
from langchain_core.tools import tool
from config import DATA_DIR

@tool
def get_upcoming_events(location: str, days: int = 30):
    """Return one natural-language event insight."""
    items = json.loads((DATA_DIR / "events.json").read_text(encoding="utf-8"))
    end = date.today() + timedelta(days=days)
    rows = [e for e in items if e["location"].lower() == location.lower() and date.today() <= datetime.fromisoformat(e["date"]).date() <= end]
    if not rows:
        return "Insight: No major local events were found in the next 30 days."
    e = sorted(rows, key=lambda x: x["date"])[0]
    return f"Insight: Upcoming local event: {e['name']} on {e['date']} ({e['theme']})."
