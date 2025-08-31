import os, httpx
from typing import List, Dict

def _get_cse() -> tuple[str, str]:
    cse_id  = os.getenv("GOOGLE_CSE_ID")
    cse_key = os.getenv("GOOGLE_CSE_KEY")
    if not (cse_id and cse_key):
        raise RuntimeError("Set GOOGLE_CSE_ID and GOOGLE_CSE_KEY in your environment (e.g., .env).")
    return cse_id, cse_key

def search_google_cse(query: str, top_k: int = 5) -> List[Dict]:
    cse_id, cse_key = _get_cse()
    params = {"q": query, "cx": cse_id, "key": cse_key, "num": min(top_k, 10)}
    r = httpx.get(
        "https://www.googleapis.com/customsearch/v1",
        params=params,
        timeout=httpx.Timeout(connect=2.0, read=5.0, write=2.0, pool=2.0),
    )
    r.raise_for_status()
    data = r.json()
    out = []
    for item in (data.get("items") or []):
        out.append({"title": item.get("title", ""), "url": item.get("link", "")})
        if len(out) >= top_k: break
    return out
