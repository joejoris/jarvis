"""Free web tools: DuckDuckGo search (no key), Open-Meteo weather (no key), RSS news."""
import requests
import xml.etree.ElementTree as ET

UA = {"User-Agent": "Mozilla/5.0 (Jarvis personal assistant)"}


def web_search(query: str, max_results: int = 5) -> str:
    """Live web search: Bing RSS, then Wikipedia opensearch as fallback (no keys)."""
    try:
        r = requests.get("https://www.bing.com/search",
                         params={"q": query, "format": "rss"},
                         headers=UA, timeout=10)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        out = []
        for i, item in enumerate(root.iter("item")):
            if i >= max_results:
                break
            title = (item.findtext("title") or "").strip()
            desc = (item.findtext("description") or "").strip()
            link = (item.findtext("link") or "").strip()
            out.append(f"{i+1}. {title} — {desc} ({link})")
        if out:
            return "\n".join(out)
    except Exception:
        pass
    # Fallback: Wikipedia opensearch (encyclopedic facts only)
    try:
        r = requests.get("https://en.wikipedia.org/w/api.php",
                         params={"action": "opensearch", "search": query,
                                 "limit": max_results, "format": "json"},
                         headers=UA, timeout=10)
        r.raise_for_status()
        d = r.json()
        titles, descs, links = d[1], d[2], d[3]
        if titles:
            return "Wikipedia matches:\n" + "\n".join(
                f"{i+1}. {t} — {desc} ({link})" for i, (t, desc, link) in
                enumerate(zip(titles, descs, links)))
        return "No results found on Bing RSS or Wikipedia."
    except Exception as e:
        return f"Search failed: {e}"


def google_news(topic: str, max_items: int = 5) -> str:
    """Live news search via Google News RSS (no key required)."""
    for attempt in range(2):
        try:
            r = requests.get("https://news.google.com/rss/search",
                             params={"q": topic, "hl": "en-US", "gl": "US", "ceid": "US:en"},
                             headers=UA, timeout=10)
            if r.status_code == 429 and attempt == 0:
                import time
                time.sleep(2)
                continue
            r.raise_for_status()
            root = ET.fromstring(r.content)
            out = []
            for i, item in enumerate(root.iter("item")):
                if i >= max_items:
                    break
                out.append(f"- {item.findtext('title')}")
            if out:
                return f"Latest headlines on '{topic}':\n" + "\n".join(out)
            return f"No headlines found for '{topic}' right now."
        except Exception as e:
            if attempt == 1:
                return (f"Live news search is rate-limited or unavailable ({e}). "
                        f"Try again shortly, or ask for 'top news headlines' for BBC RSS.")


def weather(latitude: float, longitude: float, city: str = "") -> str:
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": latitude, "longitude": longitude,
                    "current_weather": "true",
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                    "timezone": "auto", "forecast_days": 1},
            timeout=10)
        r.raise_for_status()
        d = r.json()
        cur = d["current_weather"]
        day = d["daily"]
        return (f"Weather{f' in {city}' if city else ''}: {cur['temperature']}°C, "
                f"wind {cur['windspeed']} km/h. Today: high {day['temperature_2m_max'][0]}°C, "
                f"low {day['temperature_2m_min'][0]}°C, rain chance {day['precipitation_probability_max'][0]}%.")
    except Exception as e:
        return f"Weather unavailable: {e}"


def news(topic: str = "", max_items: int = 5) -> str:
    if topic:
        return google_news(topic, max_items)
    try:
        r = requests.get("https://feeds.bbci.co.uk/news/rss.xml", headers=UA, timeout=10)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        out = []
        for i, item in enumerate(root.iter("item")):
            if i >= max_items:
                break
            out.append(f"- {item.findtext('title')}")
        return "Top headlines:\n" + "\n".join(out)
    except Exception as e:
        return f"News unavailable: {e}"
