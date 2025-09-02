import json, time
from typing import List, Dict
from tools_search import search_seeds
from tools_crawl import crawl_many, looks_like_article
from tools_summarize import summarize_long_parallel
# app.py (very top)
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=False)  # loads .env from project root

def write_json(path: str, items: List[Dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def main():
    topic = input("Enter your topic (e.g. 'latest AI safety blog posts'): ").strip()
    t0 = time.time()
    print("[1/3] Searching…")
    seeds = search_seeds(topic, k=8)
    print(f"    Using {len(seeds)} seed URLs.")
    t1 = time.time()

    print("[2/3] Crawling (seed + top links)…")
    pages = crawl_many(seeds, per_seed_links=3)
    print(f"    Unique pages: {len(pages)}")
    t2 = time.time()

    # Prefer article-like URLs (generic heuristics)
    articles = [p for p in pages if looks_like_article(p["url"])]
    if len(articles) < 3:
        fallback = [p for p in pages if p not in articles]
        articles.extend(fallback)
    articles = articles[:5]

    print("[3/3] Summarizing (parallel)…")
    summaries = summarize_long_parallel(
        articles,
        max_chars=None,           # pass full text; we only constrain the OUTPUT to <= 150
        workers=4,
        timeout_per_item=12,
        time_budget_seconds=None,
        verbose=True,
    )

    print(f"    Summaries written: {len(summaries)}")

    out_path = f"summaries_{int(time.time())}.json"
    write_json(out_path, summaries)
    print(f"\nWrote {out_path} with {len(summaries)} summaries.\n")

    print("Timing breakdown (seconds):")
    print(f"  search     {t1 - t0:.2f}")
    print(f"  crawl      {t2 - t1:.2f}")
    print(f"  summarize  {time.time() - t2:.2f}")
    print(f"  TOTAL      {time.time() - t0:.2f}")

if __name__ == "__main__":
    main()
