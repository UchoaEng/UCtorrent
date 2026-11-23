from __future__ import annotations

import re


class RssRulesService:
    def matches(self, title: str, rule: dict) -> bool:
        text = title.lower()
        must_contain = (rule.get("must_contain") or "").strip().lower()
        must_not_contain = (rule.get("must_not_contain") or "").strip().lower()
        regex = (rule.get("regex") or "").strip()
        if must_contain and must_contain not in text:
            return False
        if must_not_contain and must_not_contain in text:
            return False
        if regex and not re.search(regex, title):
            return False
        return True

    def matches_item(self, item: dict, rule: dict) -> bool:
        haystack = " ".join([str(item.get("title") or ""), str(item.get("url") or "")])
        return self.matches(haystack, rule)

    def test_rule(self, titles: list[str], rule: dict) -> list[str]:
        return [title for title in titles if self.matches(title, rule)]
