import os, re, urllib.parse, requests
from typing import List
# tools_search.py (top)
import os, re, urllib.parse, requests
from typing import List

try:
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv(), override=False)
except Exception:
    pass

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124 Safari/537.36"
    )
}

# Block obvious non-HTML doc types
_BAD_EXT = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".zip", ".mp4", ".mp3")

def _clean_url(u: str) -> str:
    if not u:
        return u
    # Strip Google redirectors if any
    if u.startswith("https://www.google.com/url?"):
        q = urllib.parse.urlparse(u).query
        params = urllib.parse.parse_qs(q)
        if "q" in params and params["q"]:
            u = params["q"][0]
    # Remove URL fragments & some tracking params
    parsed = urllib.parse.urlparse(u)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
    query = [(k, v) for (k, v) in query if k.lower() not in ("utm_source","utm_medium","utm_campaign","utm_term","utm_content","gclid","fbclid")]
    new_q = urllib.parse.urlencode(query)
    cleaned = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", new_q, ""))
    return cleaned

def _looks_html(u: str) -> bool:
    if not u or not u.startswith("http"):
        return False
    low = u.lower()
    return not low.endswith(_BAD_EXT)

def search_seeds(topic: str, k: int = 8) -> List[str]:
    key = os.getenv("GOOGLE_CSE_KEY")
    cx  = os.getenv("GOOGLE_CSE_CX")
    if not key or not cx:
        raise RuntimeError("Google Custom Search credentials missing: set GOOGLE_CSE_KEY and GOOGLE_CSE_CX")

    params = {
        "key": key,
        "cx": cx,
        "q": topic,
        "num": min(max(k, 1), 10),  # API allows up to 10 per call
        "safe": "off",
        "hl": "en",
        "gl": "us",
    }
    r = requests.get("https://www.googleapis.com/customsearch/v1", params=params, headers=HEADERS, timeout=12)
    r.raise_for_status()
    data = r.json()
    items = data.get("items", []) or []

    links: List[str] = []
    for it in items:
        link = _clean_url(it.get("link", ""))
        if _looks_html(link):
            links.append(link)

    # Dedupe while preserving order
    links = list(dict.fromkeys(links))

    # If you want more than 10 results, you can page via 'start', but k<=10 keeps it simple
    return links[:k]
