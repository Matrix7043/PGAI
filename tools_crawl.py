import warnings, time, re, urllib.parse, httpx, threading
from bs4 import XMLParsedAsHTMLWarning, BeautifulSoup
from urllib import robotparser
from typing import List, Dict, Set, Tuple, Optional
from trafilatura import extract

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

UA = "LangGraphArticleBot/0.1 (+https://example.com/; contact: you@example.com)"

def _domain(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc.lower()
    except Exception:
        return ""

def same_domain(url: str, root: str) -> bool:
    a = urllib.parse.urlparse(url).netloc
    b = urllib.parse.urlparse(root).netloc
    return a == b or a.endswith("." + b)

def normalize_url(url: str, base: str) -> str:
    return urllib.parse.urljoin(base, url.split("#")[0])

def looks_like_article(url: str) -> bool:
    return bool(re.search(r"/\d{4}/|/news/|/story|/article|/posts?/", url, re.I))

def allowed_by_robots(url: str, rp: robotparser.RobotFileParser) -> bool:
    try: return rp.can_fetch(UA, url)
    except Exception: return True

def _httpx_client() -> httpx.Client:
    # Fast failures for slow TLS/DNS
    return httpx.Client(
        headers={"User-Agent": UA},
        timeout=httpx.Timeout(connect=1.5, read=3.0, write=1.5, pool=1.5),
        follow_redirects=True,
        http2=False,
    )

def _fallback_text(html: str) -> str:
    """Lightweight fallback extractor when boilerplate removal fails."""
    try:
        soup = BeautifulSoup(html, "lxml")
        parts = []
        title = soup.title.get_text(strip=True) if soup.title else ""
        if title:
            parts.append(title)
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            parts.append(meta["content"].strip())
        for tag in soup.select("h1,h2,p"):
            t = tag.get_text(" ", strip=True)
            if t:
                parts.append(t)
            if sum(len(x) for x in parts) > 1600:
                break
        return "\n".join(parts).strip()
    except Exception:
        return ""

def crawl_site(
    seed_url: str,
    max_pages: int = 1,
    max_depth: int = 0,
    only_articles: bool = False,
    total_deadline_sec: int = 5,
    workers: int = 2,
    stop_event: Optional[threading.Event] = None,
    force_save_seed: bool = True,
    verbose: bool = True,
) -> List[Dict]:
    """
    Ultra-fast, seed-only by default. Always tries to save the seed page, even if the
    primary extractor fails (uses fallback). Hard deadline per seed. Verbose logs.
    """
    if stop_event is None:
        stop_event = threading.Event()

    start = time.time()
    if verbose:
        print(f"      [crawl] seed={seed_url}", flush=True)

    rp = robotparser.RobotFileParser()
    try:
        rp.set_url(urllib.parse.urljoin(seed_url, "/robots.txt"))
        rp.read()
    except Exception:
        pass

    seen: Set[str] = set()
    queue: List[Tuple[str, int]] = [(seed_url, 0)]
    results: List[Dict] = []

    def timed_out() -> bool:
        return (time.time() - start) >= total_deadline_sec

    with _httpx_client() as client:
        while queue and len(results) < max_pages:
            if stop_event.is_set() or timed_out():
                if verbose: print("      [crawl] stop/deadline", flush=True)
                break

            url, depth = queue.pop(0)
            if url in seen: 
                continue
            seen.add(url)

            if not allowed_by_robots(url, rp):
                if verbose: print(f"      [crawl] robots disallow {url}", flush=True)
                if not (force_save_seed and depth == 0):
                    continue

            if verbose: print(f"      [crawl] → GET {url}", flush=True)
            try:
                resp = client.get(url)
                resp.raise_for_status()
                html = resp.text
            except Exception as e:
                if verbose: print(f"      [crawl]   fetch fail: {e}", flush=True)
                continue

            text = extract(html, url=url) or _fallback_text(html)

            if text:
                if verbose: print(f"      [crawl]   +saved ({len(text)} chars)", flush=True)
                results.append({"url": url, "text": text})
            elif depth == 0 and force_save_seed:
                minimal = _fallback_text(html) or ""
                if minimal:
                    if verbose: print(f"      [crawl]   +saved (fallback {len(minimal)} chars)", flush=True)
                    results.append({"url": url, "text": minimal})
                else:
                    if verbose: print("      [crawl]   no text extracted", flush=True)
            else:
                if verbose: print("      [crawl]   no text extracted", flush=True)

            time.sleep(0.02)

    return results
