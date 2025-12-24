# Article Scraper API

Extracts articles from web pages and crawls sites for content.

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Go to http://localhost:3888/docs for interactive API docs.

## Endpoints

| Method | Endpoint | What it does |
|--------|----------|--------------|
| POST | `/extract` | Extract single article |
| POST | `/crawl` | Start site crawl |
| GET | `/crawl/jobs` | List all crawl jobs |
| GET | `/crawl/{id}` | Get crawl results |
| POST | `/self_test` | Test extraction works |

## Examples

**Extract article:**
```json
POST /extract
{"url": "https://example.com/article"}
```

**Crawl site:**
```json
POST /crawl
{"start_url": "https://example.com", "max_pages": 20}
```

## Docker

```bash
docker-compose up
```

Results saved to `data/` folder.
