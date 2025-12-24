"""
Request and Response Models
- Defines what data the API accepts
- Defines what data the API returns
- Uses Pydantic for validation
"""
from typing import Optional
from pydantic import BaseModel, Field


class ExtractRequest(BaseModel):
    url: str = Field(examples=["https://martinfowler.com/articles/design-token-based-ui-architecture.html"])
    raw: bool = Field(default=False, examples=[False])


class CrawlRequest(BaseModel):
    start_url: str = Field(examples=["https://martinfowler.com"])
    max_pages: int = Field(default=30, examples=[10])


class SelfTestRequest(BaseModel):
    url: str = Field(
        default="https://martinfowler.com/articles/design-token-based-ui-architecture.html",
        examples=["https://martinfowler.com/articles/design-token-based-ui-architecture.html"]
    )


class ExtractResponse(BaseModel):
    ok: bool
    url: str
    final_url: Optional[str] = None
    status: Optional[int] = None
    fetched_at: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[str] = None
    site_name: Optional[str] = None
    canonical_url: Optional[str] = None
    language: Optional[str] = None
    description: Optional[str] = None
    tags: list = []
    content_html: Optional[str] = None
    content_text: Optional[str] = None
    word_count: Optional[int] = None
    is_article: Optional[bool] = None
    confidence: Optional[float] = None
    raw_html: Optional[str] = None
    error: Optional[str] = None


class CrawlStartResponse(BaseModel):
    ok: bool
    job_id: str
    status_url: str


class CrawlStatusResponse(BaseModel):
    ok: bool
    job_id: str
    state: str
    progress: dict
    results: list
    errors: list


class SelfTestResponse(BaseModel):
    ok: bool
    notes: list
    signals: dict
