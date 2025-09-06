import json, time
from typing import List, Dict
from .tools_search import search_seeds
from .tools_crawl import crawl_many, looks_like_article
from .tools_summarize import summarize_long_parallel
import requests
from urllib.parse import urlparse
from langchain_google_genai import ChatGoogleGenerativeAI
# app.py (very top)
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=False)  # loads .env from project root

def generate_short_title(original_title: str) -> str:
    """Uses Gemini via LangChain to generate a short, catchy title under 12 characters."""
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest")
        
        prompt = (
            f"Generate a very short, one or two-word title that is a maximum of 12 characters. "
            f"It must capture the essence of the original article title provided below.\n\n"
            f"ORIGINAL TITLE: '{original_title}'\n\n"
            f"SHORT TITLE:"
        )
        
        response = llm.invoke(prompt)
        short_title = response.content.strip().replace('"', '')
        return short_title[:12]
    except Exception as e:
        print(f"    - AI title generation failed: {e}")
        return original_title[:12]


def write_json(path: str, items: List[Dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def main():
    topic = input("Enter your topic (e.g. 'latest AI safety blog posts'): ").strip()
    t0 = time.time()
    print("[1/4] Searching…")
    seeds = search_seeds(topic, k=8)
    print(f"    Using {len(seeds)} seed URLs.")
    t1 = time.time()

    print("[2/4] Crawling (seed + top links)…")
    pages = crawl_many(seeds, per_seed_links=3)
    print(f"    Unique pages: {len(pages)}")
    t2 = time.time()

    # Prefer article-like URLs (generic heuristics)
    articles = [p for p in pages if looks_like_article(p["url"])]
    if len(articles) < 3:
        fallback = [p for p in pages if p not in articles]
        articles.extend(fallback)
    articles = articles[:5]

    print("[3/4] Summarizing (parallel)…")
    summaries = summarize_long_parallel(
        articles,
        max_chars=None,           # pass full text; we only constrain the OUTPUT to <= 150
        workers=4,
        timeout_per_item=12,
        time_budget_seconds=None,
        verbose=True,
    )

    print(f"    Summaries written: {len(summaries)}")
    t3 = time.time()
    server_url = "http://127.0.0.1:8000/content"
    
    print("\n[4/4] Sending summaries to the image generation server...")
    
    generated_images = 0
    for summary in summaries:
        try:
            title_to_send = summary['title']
            if len(title_to_send) > 12:
                print(f"    - Title is too long. Generating a shorter one for '{title_to_send}...'")
                title_to_send = generate_short_title(title_to_send)
                print(f"    - New title: '{title_to_send}'")

            full_url = summary['reference']
            # Extract just the domain name (e.g., "www.example.com")
            short_url = urlparse(full_url).netloc
            payload_for_image = {
                "title": title_to_send,
                "content": summary['content'],
                "reference": short_url # Use the short URL here
            }
            response = requests.post(server_url, json=payload_for_image)
            if response.status_code == 200:
                print(f"  - Successfully generated image for: {summary['title']}")
                generated_images += 1
            else:
                print(f"  - Error generating image for: {summary['title']} (Status code: {response.status_code})")
                print(f"    Response: {response.text}")

        except requests.exceptions.ConnectionError:
            print("\nError: Could not connect to the image generation server.")
            print("Please ensure the FastAPI server is running in a separate terminal with 'uvicorn server.main:app --reload'")
            break 
            
    print(f"\nImage generation complete. {generated_images} images created.")
    out_path = f"summaries_{int(time.time())}.json"
    write_json(out_path, summaries)
    print(f"\nWrote {out_path} with {len(summaries)} summaries.\n")

    print("Timing breakdown (seconds):")
    print(f"  search          {t1 - t0:.2f}")
    print(f"  crawl           {t2 - t1:.2f}")
    print(f"  summarize       {t3 - t2:.2f}")
    print(f"  creating image  {time.time() -t3:.2f}")
    print(f"  TOTAL           {time.time() - t0:.2f}")

if __name__ == "__main__":
    main()
