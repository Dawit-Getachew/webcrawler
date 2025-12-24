"""
FastAPI Application
- Defines all API endpoints
- Handles requests for extracting articles and crawling sites
- Returns JSON responses
"""
import uuid
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
from models import ExtractRequest, CrawlRequest, SelfTestRequest
from config import CONFIDENCE_THRESHOLD, MIN_WORD_COUNT
from extractor import extract_article
from crawler import crawl_jobs, run_crawl

app = FastAPI(
    title="Web Article Scraper",
    description="Extract articles from web pages and crawl sites",
    version="1.0.0"
)


@app.get("/")
async def root():
    return {"ok": True, "name": "Web Article Scraper API", "version": "1.0.0",
            "endpoints": ["/extract", "/crawl", "/crawl/{job_id}", "/self_test"],
            "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/extract")
async def extract_endpoint(request: ExtractRequest):
    result = await extract_article(request.url, request.raw)
    return JSONResponse(content=result)


@app.post("/crawl")
async def crawl_endpoint(request: CrawlRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    crawl_jobs[job_id] = {
        "job_id": job_id, "state": "queued",
        "progress": {"queued": 1, "fetched": 0, "extracted": 0, "skipped": 0, "failed": 0},
        "results": [], "errors": []
    }
    background_tasks.add_task(run_crawl, job_id, request.start_url, request.max_pages)
    return JSONResponse(content={"ok": True, "job_id": job_id, "status_url": f"/crawl/{job_id}"})


@app.get("/crawl/jobs")
async def list_jobs():
    jobs = [{"job_id": j["job_id"], "state": j["state"], "extracted": j["progress"]["extracted"],
             "fetched": j["progress"]["fetched"]} for j in crawl_jobs.values()]
    return JSONResponse(content={"ok": True, "jobs": jobs})


@app.get("/crawl/{job_id}")
async def crawl_status(job_id: str):
    if job_id not in crawl_jobs:
        return JSONResponse(content={"ok": False, "error": "Job not found"}, status_code=404)
    return JSONResponse(content={"ok": True, **crawl_jobs[job_id]})


@app.post("/self_test")
async def self_test(request: SelfTestRequest):
    result = await extract_article(request.url)
    signals = {"status": result.get("status", 0), "is_article": result.get("is_article", False),
               "confidence": result.get("confidence", 0), "word_count": result.get("word_count", 0),
               "title_present": bool(result.get("title"))}
    notes, ok = [], True
    if not result.get("ok"):
        ok, notes = False, [f"Extraction failed: {result.get('error')}"]
    elif signals["confidence"] < CONFIDENCE_THRESHOLD or signals["word_count"] < MIN_WORD_COUNT:
        ok, notes = False, ["Low confidence or word count"]
    else:
        notes = ["All checks passed", f"Extracted: {signals['word_count']} words at {signals['confidence']} confidence"]
    return JSONResponse(content={"ok": ok, "notes": notes, "signals": signals})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
