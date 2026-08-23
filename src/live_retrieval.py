"""
Live news retrieval via Google News RSS — no API key required.
Returns real, current articles for a query: title, snippet, source, date.
"""
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import re
import html


def _clean_description(raw: str, title: str) -> str:
    """
    Google News RSS descriptions are raw HTML wrapping the title's core
    text + source name (e.g. "<title core>  <source>"), not real snippets.
    Strip HTML; if what's left is just that duplicate wrapper, there's no
    real preview to show.
    """
    text = re.sub(r"<[^>]+>", "", raw)
    text = html.unescape(text).strip()

    title_core = title.split(" - ")[0]
    text_norm = text.lower().replace(" ", "")
    title_norm = title_core.lower().replace(" ", "")

    if text_norm.startswith(title_norm):
        return ""
    return text

def fetch_live_articles(query: str, max_results: int = 15) -> list[dict]:
    """
    Fetches live news articles matching `query` from Google News RSS.
    Returns list of dicts: title, text (snippet), source, link, publish_date (ISO).
    """
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
    except Exception as e:
        print(f"Live fetch failed: {e}")
        return []

    root = ET.fromstring(data)
    items = root.findall(".//item")[:max_results]

    articles = []
    for item in items:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description_raw = (item.findtext("description") or "").strip()
        pub_date_raw = item.findtext("pubDate") or ""

        source_el = item.find("source")
        source = source_el.text.strip() if source_el is not None and source_el.text else "Unknown source"

        try:
            dt = datetime.strptime(pub_date_raw, "%a, %d %b %Y %H:%M:%S %Z")
            publish_date = dt.date().isoformat()
        except ValueError:
            publish_date = datetime.now(timezone.utc).date().isoformat()

        description = _clean_description(description_raw, title)

        articles.append({
            "title": title,
            "text": description if description else "No preview available — click through to read the full article.",
            "source": source,
            "link": link,
            "publish_date": publish_date,
        })

    return articles


if __name__ == "__main__":
    results = fetch_live_articles("India earthquake 2015", max_results=8)
    print(f"Fetched {len(results)} live articles\n")
    for r in results:
        print(f"[{r['publish_date']}] {r['title']} ({r['source']})")
        print(f"    -> {r['text'][:80]}")