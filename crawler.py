"""
Site Crawler
- Crawls an entire website following links
- Extracts articles from each page
- Saves results to data/ folder when done
"""
import asyncio
import json
import os
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
from readability import Document
from config import USER_AGENT, REQUEST_TIMEOUT, REQUEST_DELAY, MAX_CONCURRENCY, SKIP_PATTERNS, SKIP_EXTENSIONS
from utils import sanitize_html, extract_metadata, compute_confidence

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
crawl_jobs: dict = {}


def save_job(job_id: str, job: dict):
    path = os.path.join(DATA_DIR, f"{job_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(job, f, indent=2, ensure_ascii=False)


def should_skip_url(url: str, base_domain: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or parsed.netloc != base_domain:
        return True
    path = parsed.path.lower()
    for ext in SKIP_EXTENSIONS:
        if path.endswith(ext):
            return True
    for pattern in SKIP_PATTERNS:
        if pattern in path:
            return True
    return False


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")


def extract_links(html: str, base_url: str) -> list:
    soup = BeautifulSoup(html, "lxml")
    return [normalize_url(urljoin(base_url, a["href"])) for a in soup.find_all("a", href=True)]


async def run_crawl(job_id: str, start_url: str, max_pages: int):
    job = crawl_jobs[job_id]
    job["state"] = "running"
    base_domain = urlparse(start_url).netloc
    visited, queue = set(), [normalize_url(start_url)]
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    
    async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
        while queue and job["progress"]["fetched"] < max_pages:
            url = queue.pop(0)
            if url in visited or should_skip_url(url, base_domain):
                job["progress"]["skipped"] += 1
                continue
            visited.add(url)
            
            async with semaphore:
                try:
                    resp = await client.get(url, follow_redirects=True)
                    html, status = resp.text, resp.status_code
                    job["progress"]["fetched"] += 1
                    
                    if status >= 400:
                        job["errors"].append({"url": url, "error": f"HTTP {status}"})
                        job["progress"]["failed"] += 1
                        continue
                    
                    soup = BeautifulSoup(html, "lxml")
                    metadata = extract_metadata(soup, str(resp.url))
                    try:
                        doc = Document(html)
                        content_html = sanitize_html(doc.summary())
                        if not metadata["title"]:
                            metadata["title"] = doc.title()
                    except Exception:
                        content_html = ""
                    
                    content_text = BeautifulSoup(content_html, "lxml").get_text(separator=" ", strip=True)
                    word_count = len(content_text.split())
                    is_article, confidence = compute_confidence(soup, content_text, word_count)
                    
                    if is_article:
                        job["results"].append({"url": url, "status": status, "is_article": True,
                            "confidence": round(confidence, 2), "title": metadata["title"],
                            "word_count": word_count, "content_html": content_html, "canonical_url": metadata["canonical_url"]})
                        job["progress"]["extracted"] += 1
                    else:
                        job["progress"]["skipped"] += 1
                    
                    for link in extract_links(html, str(resp.url)):
                        if link not in visited and link not in queue:
                            queue.append(link)
                    job["progress"]["queued"] = len(queue)
                except Exception as e:
                    job["errors"].append({"url": url, "error": str(e)})
                    job["progress"]["failed"] += 1
                await asyncio.sleep(REQUEST_DELAY)
    job["state"] = "done"
    save_job(job_id, job)
