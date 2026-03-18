import pytest
from api.search import SearchEngine

SAMPLE_LISTINGS = [
    {"id": "skill-api-tester", "slug": "api-tester", "title": "API Tester", "category": "skills",
     "description": "API endpoint testing and validation", "tags": ["api-testing", "validation"],
     "persona_tags": ["developer"], "difficulty": "intermediate", "pricing_model": "free",
     "version": "1.0.0", "author": "ProwlrBot", "license": "Apache-2.0",
     "path": "skills/api-tester", "manifest": "skills/api-tester/manifest.json"},
    {"id": "agent-prowlr-writer", "slug": "prowlr-writer", "title": "Prowlr Writer", "category": "agents",
     "description": "Content writing and documentation generation", "tags": ["writing", "docs"],
     "persona_tags": ["developer", "business"], "difficulty": "beginner", "pricing_model": "free",
     "version": "1.0.0", "author": "ProwlrBot", "license": "Apache-2.0",
     "path": "agents/prowlr-writer", "manifest": "agents/prowlr-writer/manifest.json"},
    {"id": "workflow-deploy-review", "slug": "deploy-review", "title": "Deploy Review Pipeline", "category": "workflows",
     "description": "Automated code review to deployment pipeline", "tags": ["ci-cd", "deployment"],
     "persona_tags": [], "difficulty": "advanced", "pricing_model": "free",
     "version": "1.0.0", "author": "ProwlrBot", "license": "Apache-2.0",
     "path": "workflows/deploy-review", "manifest": "workflows/deploy-review/manifest.json"},
]

@pytest.fixture
def engine():
    return SearchEngine(SAMPLE_LISTINGS)

class TestFullTextSearch:
    def test_search_by_title(self, engine):
        results = engine.search(q="API Tester")
        assert results[0]["id"] == "skill-api-tester"

    def test_search_by_description(self, engine):
        results = engine.search(q="documentation")
        assert any(r["id"] == "agent-prowlr-writer" for r in results)

    def test_search_by_tag(self, engine):
        results = engine.search(q="ci-cd")
        assert results[0]["id"] == "workflow-deploy-review"

    def test_search_case_insensitive(self, engine):
        results = engine.search(q="api tester")
        assert results[0]["id"] == "skill-api-tester"

    def test_search_prefix_match(self, engine):
        results = engine.search(q="deploy")
        assert any(r["id"] == "workflow-deploy-review" for r in results)

    def test_search_no_results(self, engine):
        results = engine.search(q="nonexistent-xyz-term")
        assert len(results) == 0

class TestFacetedFiltering:
    def test_filter_by_category(self, engine):
        results = engine.search(category="skills")
        assert all(r["category"] == "skills" for r in results)

    def test_filter_by_difficulty(self, engine):
        results = engine.search(difficulty="beginner")
        assert all(r["difficulty"] == "beginner" for r in results)

    def test_filter_by_persona(self, engine):
        results = engine.search(persona="business")
        assert all("business" in r["persona_tags"] for r in results)

    def test_filter_by_tag(self, engine):
        results = engine.search(tags="api-testing")
        assert all("api-testing" in r["tags"] for r in results)

    def test_combined_search_and_filter(self, engine):
        results = engine.search(q="testing", category="skills")
        assert len(results) == 1
        assert results[0]["id"] == "skill-api-tester"

class TestSorting:
    def test_default_sort_alphabetical(self, engine):
        results = engine.search()
        titles = [r["title"] for r in results]
        assert titles == sorted(titles)

    def test_sort_by_title(self, engine):
        results = engine.search(sort="title")
        titles = [r["title"] for r in results]
        assert titles == sorted(titles)

class TestFuzzySearch:
    def test_fuzzy_match_typo(self, engine):
        results = engine.search(q="testor")
        assert any(r["id"] == "skill-api-tester" for r in results)
