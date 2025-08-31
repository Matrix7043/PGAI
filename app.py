import os, json, time, signal, threading
from typing import TypedDict, List, Dict
from collections import defaultdict

# Load .env first
from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, START, END
from tools_search import search_google_cse
from tools_crawl import crawl_site
from tools_summarize import summarize_long_parallel  # parallel + timeout + cancel

# === Ultra-fast, seed-only profile ===
SEEDS = 2
PAGES_PER_SEED = 1          # seed page only
CRAWL_DEPTH = 0             # no link following
CRAWL_DEADLINE_PER_SEED = 5 # 5s per seed, hard cap
CRAWL_WORKERS = 2

SUMMARIES_MAX = 2
SUMMARIZE_MAX_CHARS = 1600
SUMMARIZE_WORKERS = 2
LLM_TIMEOUT_PER_SUMMARY = 6
GLOBAL_BUDGET = 22

# common blockers (skip to avoid empty pages)
BLOCKED_DOMAINS = {
    "www.imdb.com", "imdb.com",
    "www.reuters.com", "reuters.com",
    "www.wired.com", "wired.com",
    "www.bloomberg.com", "bloomberg.com",
}

# cancellation + timing
stop_event = threading.Event()
_tmarks: Dict[str, float] = {}
_spans: Dict[str, float] = defaultdict(float)

def _on_sigint(signum, frame):
    print("\n[!] Cancel requested — stopping soon…", flush=True)
    stop_event.set()

signal.signal(signal.SIGINT, _on_sigint)
if hasattr(signal, "SIGBREAK"):
    signal.signal(signal.SIGBREAK, _on_sigint)

def t_start(key: str): _tmarks.__setitem__(key, time.time())
def t_end(key: str):
    t = _tmarks.pop(key, None)
    if t is not None:
        _spans[key] += time.time() - t

def _startup_env_check() -> None:
    missing = [k for k in ("GOOGLE_API_KEY", "GOOGLE_CSE_ID", "GOOGLE_CSE_KEY") if not os.getenv(k)]
    if missing:
        raise RuntimeError(
            "Missing env vars: " + ", ".join(missing) +
            "\nCreate .env with:\nGOOGLE_API_KEY=...\nGOOGLE_CSE_ID=...\nGOOGLE_CSE_KEY=...\n"
        )

class State(TypedDict, total=False):
    query: str
    seeds: List[Dict]
    crawled: List[Dict]
    outputs: List[Dict]

def _domain(url: str) -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc.lower()
    except Exception:
        return ""

def node_search(state: State) -> State:
    if stop_event.is_set(): return {"seeds": []}
    t_start("search")
    print("[1/3] Searching…", flush=True)
    seeds_all = search_google_cse(state["query"], top_k=max(SEEDS * 3, 2))
    # filter out blocked domains, keep first SEEDS usable
    seeds = []
    for item in seeds_all:
        if _domain(item["url"]) in BLOCKED_DOMAINS:
            continue
        seeds.append(item)
        if len(seeds) >= SEEDS:
            break
    print(f"    Using {len(seeds)} seed URLs.", flush=True)
    for i, s in enumerate(seeds, 1):
        print(f"      {i}. {s['title']} — {s['url']}", flush=True)
    t_end("search")
    return {"seeds": seeds}

def node_crawl(state: State) -> State:
    if stop_event.is_set(): return {"crawled": []}
    t_start("crawl")
    print("[2/3] Crawling (seed-only, fast)…", flush=True)
    pages: List[Dict] = []
    for seed in state["seeds"]:
        if stop_event.is_set(): break
        try:
            batch = crawl_site(
                seed["url"],
                max_pages=PAGES_PER_SEED,
                max_depth=CRAWL_DEPTH,
                only_articles=False,            # seed is always kept
                total_deadline_sec=CRAWL_DEADLINE_PER_SEED,
                workers=CRAWL_WORKERS,
                stop_event=stop_event,
                force_save_seed=True,           # <-- guarantee seed is saved
                verbose=True,                   # <-- show GET/save logs
            )
            print(f"    {seed['url']} → {len(batch)} page(s)", flush=True)
            pages.extend(batch)
        except Exception as e:
            print(f"    Skipped {seed['url']} ({e})", flush=True)

    # de-dup by URL
    seen, uniq = set(), []
    for p in pages:
        if p["url"] not in seen:
            uniq.append(p); seen.add(p["url"])
    print(f"    Unique pages: {len(uniq)}", flush=True)
    t_end("crawl")
    return {"crawled": uniq}

def node_summarize(state: State) -> State:
    if stop_event.is_set(): return {"outputs": []}
    t_start("summarize")
    print("[3/3] Summarizing (parallel)…", flush=True)

    candidates = [p for p in state["crawled"] if p.get("text")]
    candidates.sort(key=lambda x: len(x["text"]), reverse=True)
    candidates = candidates[:SUMMARIES_MAX]

    elapsed_total = sum(_spans.values())
    time_left = GLOBAL_BUDGET - elapsed_total
    if time_left <= 2 or not candidates:
        print("    Skipping summaries (budget/inputs).", flush=True)
        t_end("summarize"); return {"outputs": []}

    outs = summarize_long_parallel(
        candidates,
        max_chars=SUMMARIZE_MAX_CHARS,
        workers=SUMMARIZE_WORKERS,
        timeout_per_item=LLM_TIMEOUT_PER_SUMMARY,
        time_budget_seconds=int(time_left) - 1,
        verbose=True,
        stop_event=stop_event,
    )
    print(f"    Summaries written: {len(outs)}", flush=True)
    t_end("summarize")
    return {"outputs": outs}

# wire the graph
builder = StateGraph(State)
builder.add_node("search", node_search)
builder.add_node("crawl", node_crawl)
builder.add_node("summarize", node_summarize)
builder.add_edge(START, "search")
builder.add_edge("search", "crawl")
builder.add_edge("crawl", "summarize")
builder.add_edge("summarize", END)
graph = builder.compile()

if __name__ == "__main__":
    _startup_env_check()
    user_query = input("Enter your topic (e.g. 'latest AI safety blog posts'): ")
    t0 = time.time()
    try:
        final_state = graph.invoke({"query": user_query})
    except KeyboardInterrupt:
        stop_event.set()
        print("\n[!] Aborted by user.", flush=True)
        final_state = {"outputs": []}

    out_path = f"summaries_{int(time.time())}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(final_state.get("outputs", []), f, ensure_ascii=False, indent=2)

    total = time.time() - t0
    print(f"\nWrote {out_path} with {len(final_state.get('outputs', []))} summaries.", flush=True)
    print("\nTiming breakdown (seconds):", flush=True)
    for k in ("search", "crawl", "summarize"):
        print(f"  {k:10s} { _spans.get(k, 0.0):5.2f}", flush=True)
    other = total - sum(_spans.values())
    print(f"  other      {other:5.2f}")
    print(f"  TOTAL      {total:5.2f}\n")
