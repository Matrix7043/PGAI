import os, concurrent.futures, time, threading, re
from typing import Dict, List, Optional, Annotated
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI

# Load .env if present (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


# =========================
# Output contract
# =========================
class ArticleSummary(BaseModel):
    # Keep full headline (no length cap)
    title: str = Field(..., description="Full headline/title derived from the page or model.")
    # Exactly one catchy news line, hard-capped at 150 chars
    content: Annotated[str, Field(max_length=150, description="A catchy, factual one-line news blurb (≤ 150 characters).")]
    # Keep full source URL (no truncation)
    reference: str = Field(..., description="Full source URL of the content.")


_model = None


def _truncate_smart(text: str, limit: int) -> str:
    """Trim at sentence/word boundary, add ellipsis only if needed."""
    text = re.sub(r"\s+", " ", (text or "")).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    # Prefer sentence boundary near the limit
    for i in range(len(cut) - 1, max(-1, limit - 40), -1):
        if cut[i] in ".!?;:":
            return cut[:i + 1]
    # Else last word boundary
    j = cut.rfind(" ")
    if j >= max(10, limit // 2):
        return cut[:j] + "…"
    return cut[:limit - 1] + "…"


def _get_model() -> ChatGoogleGenerativeAI:
    global _model
    if _model is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY is missing. Put it in your .env or export it.")
        _model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0,
            google_api_key=api_key
        )
    return _model


def _summarize_once(article: dict) -> dict:
    """
    Turn arbitrary-length page text into:
      - title: full headline (no cap)
      - content: ONE news line (≤150 chars)
      - reference: full URL
    """
    text = (article.get("text") or "").strip()
    url = (article.get("url") or "").strip()
    ogt = (article.get("title") or "").strip()
    ogd = (article.get("desc") or "").strip()

    # If page is very thin, synthesize directly from metadata
    if len(text) < 220:
        title = ogt or "Untitled"
        content = _truncate_smart(ogd or text or "Insufficient content", 150)
        reference = url
        return ArticleSummary(title=title, content=content, reference=reference).model_dump()

    # Ask Gemini for ONE short news line (not a paragraph summary)
    class LLMSummary(BaseModel):
        title: str
        content: str

    structured = _get_model().with_structured_output(LLMSummary)
    prompt = (
        "Write ONE catchy, factual news line based ONLY on the provided text.\n"
        "Rules:\n"
        "- 1 sentence, <= 150 characters.\n"
        "- No emojis, hashtags, URLs, or site names.\n"
        "- No speculation; only facts present in the text.\n"
        "- Include a key entity or fact; keep it neutral/objective.\n"
        "- If content is too thin, output exactly: Insufficient content.\n\n"
        f"URL: {url}\n"
        f"Extracted text:\n{text}\n"
    )
    res = structured.invoke(prompt)

    title = (res.title or ogt or "Untitled").strip()
    # Hard-enforce 150 char cap on the final line
    content = _truncate_smart(res.content or ogd or "Insufficient content", 150)
    reference = url

    return ArticleSummary(title=title, content=content, reference=reference).model_dump()


def summarize_long(article: dict, max_chars: Optional[int] = None) -> dict:
    """
    Accept ANY size input text; we only constrain the OUTPUT to <= 150 chars.
    """
    return _summarize_once({
        "url": article.get("url", ""),
        "text": article.get("text", ""),
        "title": article.get("title", ""),
        "desc": article.get("desc", "")
    })


def summarize_long_parallel(
    articles: List[Dict],
    max_chars: Optional[int] = None,  # kept for API compatibility; not used
    workers: int = 2,
    timeout_per_item: int = 12,
    time_budget_seconds: Optional[int] = None,
    verbose: bool = False,
    stop_event: Optional[threading.Event] = None,
) -> List[Dict]:
    """
    Parallel summarization with per-item timeout (best-effort) and optional overall budget.
    Never hangs the pipeline even if a single page/model call stalls.
    """
    if stop_event is None:
        stop_event = threading.Event()

    start = time.time()
    results: List[Dict] = []
    if not articles:
        return results

    # Pass full text; preserve any title/desc the crawler scraped
    prepared = [
        {
            "url": a.get("url", ""),
            "text": a.get("text", ""),
            "title": a.get("title", ""),
            "desc": a.get("desc", ""),
        }
        for a in articles
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        pending: Dict[concurrent.futures.Future, float] = {}
        for item in prepared:
            fut = ex.submit(_summarize_once, item)
            pending[fut] = time.time()

        while pending:
            if stop_event.is_set():
                if verbose:
                    print("    Cancelled — stopping summaries.", flush=True)
                break

            now = time.time()
            if time_budget_seconds is not None and (now - start) >= time_budget_seconds:
                if verbose:
                    print("    Budget exhausted — stopping summaries.", flush=True)
                break

            done, _ = concurrent.futures.wait(
                list(pending.keys()),
                timeout=0.2,
                return_when=concurrent.futures.FIRST_COMPLETED
            )

            for fut in list(done):
                try:
                    res = fut.result()
                    results.append(res)
                except Exception as e:
                    if verbose:
                        print(f"      Failed: {e}", flush=True)
                finally:
                    pending.pop(fut, None)

            # Enforce per-item timeout: drop slow tasks so we can finish
            for fut, t0 in list(pending.items()):
                if timeout_per_item and (now - t0) > timeout_per_item:
                    if verbose:
                        print("      Timed out (skipping).", flush=True)
                    pending.pop(fut, None)

    return results
