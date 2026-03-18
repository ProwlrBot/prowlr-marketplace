from __future__ import annotations


class SearchEngine:
    def __init__(self, listings: list[dict]) -> None:
        self.listings = listings
        self._build_indexes()

    def _build_indexes(self) -> None:
        self.by_category: dict[str, set[int]] = {}
        self.by_tag: dict[str, set[int]] = {}
        self.by_persona: dict[str, set[int]] = {}
        self.by_difficulty: dict[str, set[int]] = {}
        self.by_pricing: dict[str, set[int]] = {}

        for i, listing in enumerate(self.listings):
            cat = listing.get("category", "")
            self.by_category.setdefault(cat, set()).add(i)
            for tag in listing.get("tags", []):
                self.by_tag.setdefault(tag.lower(), set()).add(i)
            for persona in listing.get("persona_tags", []):
                self.by_persona.setdefault(persona.lower(), set()).add(i)
            diff = listing.get("difficulty", "intermediate")
            self.by_difficulty.setdefault(diff, set()).add(i)
            pricing = listing.get("pricing_model", "free")
            self.by_pricing.setdefault(pricing, set()).add(i)

    def search(
        self,
        q: str | None = None,
        category: str | None = None,
        tags: str | None = None,
        persona: str | None = None,
        difficulty: str | None = None,
        pricing: str | None = None,
        sort: str | None = None,
        download_counts: dict[str, int] | None = None,
    ) -> list[dict]:
        candidates = set(range(len(self.listings)))

        if category:
            candidates &= self.by_category.get(category, set())
        if tags:
            for tag in tags.split(","):
                candidates &= self.by_tag.get(tag.strip().lower(), set())
        if persona:
            candidates &= self.by_persona.get(persona.lower(), set())
        if difficulty:
            candidates &= self.by_difficulty.get(difficulty, set())
        if pricing:
            candidates &= self.by_pricing.get(pricing, set())

        if q:
            scored = []
            for i in candidates:
                score = self._score(self.listings[i], q)
                if score > 0:
                    scored.append((i, score))
            effective_sort = sort or "relevance"
            if effective_sort == "relevance":
                scored.sort(key=lambda x: (-x[1], self.listings[x[0]]["title"]))
                return [self.listings[i] for i, _ in scored]
            results = [self.listings[i] for i, _ in scored]
        else:
            results = [self.listings[i] for i in candidates]

        effective_sort = sort or "title"
        if q and not sort:
            pass
        elif effective_sort == "title":
            results.sort(key=lambda x: x["title"].lower())
        elif effective_sort == "popular":
            counts = download_counts or {}
            results.sort(key=lambda x: (-counts.get(x["id"], 0), x["title"].lower()))

        return results

    def _score(self, listing: dict, query: str) -> float:
        query_lower = query.lower()
        tokens = query_lower.split()
        score = 0.0
        title_lower = listing.get("title", "").lower()
        desc_lower = listing.get("description", "").lower()
        tags = [t.lower() for t in listing.get("tags", [])]

        for token in tokens:
            if token in title_lower:
                score += 3.0
            elif self._fuzzy_match(token, title_lower.split()):
                score += 1.5
            if token in desc_lower:
                score += 1.0
            for tag in tags:
                if token in tag:
                    score += 2.0
                    break
            else:
                if self._fuzzy_match(token, tags):
                    score += 1.0

        return score

    def _fuzzy_match(self, token: str, words: list[str]) -> bool:
        for word in words:
            if self._levenshtein(token, word) <= 2:
                return True
        return False

    @staticmethod
    def _levenshtein(s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return SearchEngine._levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)
        prev_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            curr_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = prev_row[j + 1] + 1
                deletions = curr_row[j] + 1
                substitutions = prev_row[j] + (c1 != c2)
                curr_row.append(min(insertions, deletions, substitutions))
            prev_row = curr_row
        return prev_row[-1]
