import re, urllib.parse, requests
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124 Safari/537.36"
    )
}

# Generic "this looks like a news/article URL" patterns
YEAR_PATH = re.compile(r"/20\d{2}/\d{2}/\d{2}/")  # e.g., /2025/09/02/
ARTICLE_SEGMENTS = (
    "/news/", "/story/", "/stories/", "/article/", "/articles/",
    "/sport/", "/sports/", "/cricket/", "/olympic", "/olympics/",
    "/business/", "/tech/", "/technology/",
)

EXCLUDE_SEGMENTS = (
    "/tag/", "/tags/", "/category/", "/topics/", "/about/", "/privacy", "/terms", "/contact",
)

def fetch(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=12)
    r.raise_for_status()
    return r.text

def _get_meta(soup: BeautifulSoup, prop: str, attr: str = "content") -> Optional[str]:
    tag = soup.find("meta", attrs={"property": prop}) or soup.find("meta", attrs={"name": prop})
    return tag.get(attr).strip() if tag and tag.get(attr) else None

def extract_text_and_meta(html: str) -> Dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    text = ""
    for selector in [
        "article",
        "[itemprop='articleBody']",
        ".article-content",
        ".entry-content",
        ".post-content",
        ".story-content",
        "#readability-page-1",
        "#main", "#content", "#primary",
        "main",
    ]:
        node = soup.select_one(selector)
        if node and node.get_text(strip=True):
            text = node.get_text(" ", strip=True)
            break
    if not text:
        text = soup.get_text(" ", strip=True)

    title = (_get_meta(soup, "og:title") or (soup.title.string if soup.title else "") or "").strip()
    desc  = (_get_meta(soup, "og:description") or _get_meta(soup, "description") or "").strip()
    canonical = None
    link_canon = soup.find("link", rel=lambda v: v and "canonical" in v)
    if link_canon and link_canon.get("href"):
        canonical = link_canon["href"].strip()
    return {"text": text, "title": title, "desc": desc, "canonical": canonical}

def looks_like_article(href: str) -> bool:
    if not href or href.startswith("#"):
        return False
    href_l = href.lower()
    if any(seg in href_l for seg in EXCLUDE_SEGMENTS):
        return False
    return YEAR_PATH.search(href_l) is not None or any(seg in href_l for seg in ARTICLE_SEGMENTS)

def crawl_seed_and_links(url: str, limit_links: int = 3) -> List[Dict]:
    pages: List[Dict] = []
    try:
        html = fetch(url)
        meta = extract_text_and_meta(html)
        pages.append({"url": url, **meta})
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            href = urllib.parse.urljoin(url, a["href"])
            if looks_like_article(href) and href not in links:
                links.append(href)
            if len(links) >= limit_links:
                break
        for link in links:
            try:
                sub_html = fetch(link)
                sub_meta = extract_text_and_meta(sub_html)
                canon = sub_meta.get("canonical")
                final_url = canon if canon and canon.startswith("http") else link
                pages.append({"url": final_url, **sub_meta})
            except Exception:
                pass
    except Exception:
        pass
    return pages

def crawl_many(seeds: List[str], per_seed_links: int = 3) -> List[Dict]:
    all_pages: List[Dict] = []
    seen = set()
    for s in seeds:
        for p in crawl_seed_and_links(s, per_seed_links):
            url = p.get("url")
            if not url or url in seen:
                continue
            seen.add(url)
            all_pages.append(p)
    return all_pages
