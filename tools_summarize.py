import os, concurrent.futures, time, threading
from typing import Dict, List, Optional, Annotated
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

class ArticleSummary(BaseModel):
    title: Annotated[str, Field(max_length=12, description="The title of the post (max 12 characters).")]
    content: Annotated[str, Field(max_length=150, description="The main content of the post (max 150 characters).")]
    reference: Annotated[str, Field(max_length=30, description="The reference or source of the content (max 30 characters).")]

_model = None

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
    text = (article.get("text") or "").strip()
    url  = (article.get("url")  or "").strip()
    ogt  = (article.get("title") or "").strip()
    ogd  = (article.get("desc")  or "").strip()

    if len(text) < 220:
        title = (ogt or "Untitled")[:12]
        content = (ogd or text or "Insufficient content")[:150]
        reference = url[:30]
        final_summary = ArticleSummary(title=title, content=content, reference=reference)
        return final_summary.model_dump()

    class LLMSummary(BaseModel):
        title: str
        content: str

    structured = _get_model().with_structured_output(LLMSummary)
    prompt = (
        "Summarize the webpage into ONE compact, neutral paragraph, with a title.\n"
        "The title should be at most 12 characters.\n"
        "The content should be at most 150 characters.\n"
        "No speculation. If content is thin, say 'Insufficient content'.\n\n"
        f"URL: {url}\n"
        f"Extracted text:\n{text}\n"
    )
    res = structured.invoke(prompt)

    title = (res.title or "").strip()[:12]
    content = (res.content or "").strip()[:150]
    if not content:
        content = (ogd or "Insufficient content")[:150]
    reference = url[:30]
    final_summary = ArticleSummary(title=title, content=content, reference=reference)
    return final_summary.model_dump()

def _trim_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    keep_each = max(1, max_chars // 2)
    return text[:keep_each] + "\n...\n" + text[-keep_each:]

def summarize_long(article: dict, max_chars: int = 1600) -> dict:
    text = _trim_text(article.get("text", ""), max_chars)
    item = dict(article)
    item["text"] = text
    return _summarize_once(item)

def summarize_long_parallel(
    articles: List[Dict],
    max_chars: int = 1600,
    workers: int = 2,
    timeout_per_item: int = 6,
    time_budget_seconds: Optional[int] = None,
    verbose: bool = False,
    stop_event: Optional[threading.Event] = None,
) -> List[Dict]:
    if stop_event is None:
        stop_event = threading.Event()

    start = time.time()
    results: List[Dict] = []
    if not articles:
        return results

    trimmed = []
    for a in articles:
        text = _trim_text(a.get("text", ""), max_chars)
        item = dict(a)
        item["text"] = text
        trimmed.append(item)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        # submit and remember when each future started
        pending: Dict[concurrent.futures.Future, float] = {}
        for i, item in enumerate(trimmed, 1):
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

            # Collect any futures that finished in this tick
            done, not_done = concurrent.futures.wait(
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

            # Enforce per-item timeout for still-running futures
            to_drop = []
            for fut, t0 in pending.items():
                if timeout_per_item is not None and (now - t0) > timeout_per_item:
                    to_drop.append(fut)
            for fut in to_drop:
                if verbose:
                    print("      Timed out (skipping).", flush=True)
                # We can't kill the thread, but we stop waiting for it:
                pending.pop(fut, None)

    return results

