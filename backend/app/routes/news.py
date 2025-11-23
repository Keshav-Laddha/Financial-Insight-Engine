import os
from typing import List, Dict

import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter()

# Correct NewsAPI endpoint  
NEWS_API_PROVIDER_URL = "https://newsapi.org/v2/everything"


@router.get("/{company}")
async def fetch_company_news(company: str) -> List[Dict[str, str]]:
    """
    Fetch latest news articles for a company.
    Returns a list of {title, description, url, image}.
    """
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="NEWS_API_KEY not configured.")

    if not NEWS_API_PROVIDER_URL:
        raise HTTPException(
            status_code=500,
            detail="NEWS_API_PROVIDER_URL is not configured.",
        )

    params = {
    "q": f'("{company}" OR "{company} stock" OR "{company} results" OR "{company} earnings") AND (profit OR revenue OR technology OR software OR finance)',
    "searchIn": "title,description",
    "sortBy": "publishedAt",
    "language": "en",
    "pageSize": 3,
    "apiKey": api_key,
}


    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(NEWS_API_PROVIDER_URL, params=params)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=500, detail=f"News provider request failed: {exc}") from exc

    if response.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail=f"News provider error: {response.text}",
        )

    data = response.json()

    # NewsAPI returns {"articles": [...]}
    articles = data.get("articles", [])

    cleaned = []
    for article in articles[:3]:
        cleaned.append(
            {
                "title": article.get("title") or "Untitled",
                "description": article.get("description") or "",
                "url": article.get("url") or "",
                "image": article.get("urlToImage") or None,
            }
        )

    return cleaned
