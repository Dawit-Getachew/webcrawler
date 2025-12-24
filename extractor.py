"""
Article Extractor
- Fetches a single web page
- Pulls out the main article content
- Returns title, author, text, and metadata
"""
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
from readability import Document
from config import USER_AGENT, REQUEST_TIMEOUT
from utils import sanitize_html, extract_metadata, compute_confidence


async def fetch_page(client: httpx.AsyncClient, url: str) -> tuple:
    response = await client.get(url, follow_redirects=True)
    return response.text, str(response.url), response.status_code


async def extract_article(url: str, raw: bool = False) -> dict:
    async with httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT,
        follow_redirects=True
    ) as client:
        try:
            html, final_url, status = await fetch_page(client, url)
        except Exception as e:
            return {"ok": False, "error": str(e), "url": url}
    
    if status >= 400:
        return {"ok": False, "error": f"HTTP {status}", "url": url, "status": status}
    
    soup = BeautifulSoup(html, "lxml")
    metadata = extract_metadata(soup, final_url)
    
    try:
        doc = Document(html)
        content_html = doc.summary()
        if not metadata["title"]:
            metadata["title"] = doc.title()
    except Exception:
        article = soup.find("article") or soup.find("main") or soup.find("body")
        content_html = str(article) if article else ""
    
    content_html = sanitize_html(content_html)
    content_soup = BeautifulSoup(content_html, "lxml")
    content_text = content_soup.get_text(separator=" ", strip=True)
    word_count = len(content_text.split())
    is_article, confidence = compute_confidence(soup, content_text, word_count)
    
    result = {
        "ok": True,
        "url": url,
        "final_url": final_url,
        "status": status,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "title": metadata["title"],
        "author": metadata["author"],
        "published_at": metadata["published_at"],
        "site_name": metadata["site_name"],
        "canonical_url": metadata["canonical_url"],
        "language": metadata["language"],
        "description": metadata["description"],
        "tags": metadata["tags"],
        "content_html": content_html,
        "content_text": content_text,
        "word_count": word_count,
        "is_article": is_article,
        "confidence": round(confidence, 2)
    }
    if raw:
        result["raw_html"] = html
    return result
