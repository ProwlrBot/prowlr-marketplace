from __future__ import annotations
from fastapi import APIRouter, Request
from api.models import CategoriesResponse, CategoryCount

router = APIRouter()

CATEGORY_NAMES = {
    "skills": "Skills", "agents": "Agents", "prompts": "Prompts",
    "mcp-servers": "MCP Servers", "themes": "Themes",
    "workflows": "Workflows", "specs": "Specs",
}

@router.get("/categories", response_model=CategoriesResponse)
async def list_categories(request: Request):
    counts = request.app.state.index_meta.get("categories", {})
    categories = [
        CategoryCount(id=cat_id, name=CATEGORY_NAMES.get(cat_id, cat_id), count=count)
        for cat_id, count in sorted(counts.items())
    ]
    return CategoriesResponse(categories=categories)
