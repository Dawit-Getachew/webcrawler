"""
HTML Utilities
- Cleans up messy HTML (removes scripts, ads, nav)
- Extracts metadata (title, author, date)
- Calculates confidence score for article detection
"""
import json
from bs4 import BeautifulSoup
from config import CONFIDENCE_THRESHOLD, MIN_WORD_COUNT


def sanitize_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.find_all(["script", "style", "nav", "footer", "aside", "form", "iframe", "noscript", "header"]):
        tag.decompose()
    for tag in soup.find_all(True):
        allowed = ["href", "src", "alt", "title"]
        for attr in list(tag.attrs.keys()):
            if attr not in allowed:
                del tag.attrs[attr]
    return str(soup)


def extract_metadata(soup: BeautifulSoup, url: str) -> dict:
    meta = {"title": None, "author": None, "published_at": None, "site_name": None,
            "canonical_url": url, "language": None, "description": None, "tags": []}
    
    if soup.find("title"):
        meta["title"] = soup.find("title").get_text(strip=True)
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        meta["title"] = og_title["content"]
    
    for name in ["author", "article:author"]:
        tag = soup.find("meta", attrs={"name": name}) or soup.find("meta", property=name)
        if tag and tag.get("content"):
            meta["author"] = tag["content"]
            break
    
    for name in ["article:published_time", "date"]:
        tag = soup.find("meta", attrs={"name": name}) or soup.find("meta", property=name)
        if tag and tag.get("content"):
            meta["published_at"] = tag["content"]
            break
    if not meta["published_at"]:
        time_tag = soup.find("time", attrs={"datetime": True})
        if time_tag:
            meta["published_at"] = time_tag.get("datetime")
    
    og_site = soup.find("meta", property="og:site_name")
    if og_site and og_site.get("content"):
        meta["site_name"] = og_site["content"]
    
    canonical = soup.find("link", rel="canonical")
    if canonical and canonical.get("href"):
        meta["canonical_url"] = canonical["href"]
    
    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        meta["language"] = html_tag["lang"]
    
    for name in ["description", "og:description"]:
        tag = soup.find("meta", attrs={"name": name}) or soup.find("meta", property=name)
        if tag and tag.get("content"):
            meta["description"] = tag["content"]
            break
    
    parse_json_ld(soup, meta)
    return meta


def parse_json_ld(soup: BeautifulSoup, meta: dict):
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and data.get("@type") in ["Article", "NewsArticle", "BlogPosting"]:
                if not meta["author"] and data.get("author"):
                    author = data["author"]
                    meta["author"] = author.get("name") if isinstance(author, dict) else author
                if not meta["published_at"] and data.get("datePublished"):
                    meta["published_at"] = data["datePublished"]
        except (json.JSONDecodeError, TypeError):
            pass


def compute_confidence(soup: BeautifulSoup, content_text: str, word_count: int) -> tuple:
    score = 0.3 if word_count >= 300 else (0.15 if word_count >= 100 else 0)
    if soup.find("article"):
        score += 0.2
    if soup.find("title") and len(soup.find("title").get_text(strip=True)) > 10:
        score += 0.1
    if len(soup.find_all("p")) >= 3:
        score += 0.15
    links = soup.find_all("a")
    link_len = sum(len(a.get_text()) for a in links)
    if len(content_text) > 0 and link_len / max(len(content_text), 1) < 0.3:
        score += 0.15
    if soup.find_all(["h1", "h2", "h3"]):
        score += 0.1
    confidence = min(score, 1.0)
    is_article = confidence >= CONFIDENCE_THRESHOLD and word_count >= MIN_WORD_COUNT
    return is_article, confidence
