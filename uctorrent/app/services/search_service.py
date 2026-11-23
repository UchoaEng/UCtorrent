from __future__ import annotations

from collections.abc import Callable

from uctorrent.app.services.search_providers import PublicDomainProvider, SearchProvider, SearchResult


class SearchService:
    """Safe, local-only search plugin registry.

    UCtorrent intentionally ships with no piracy-oriented providers.
    Users may configure legal sources at their own responsibility.
    """

    def __init__(self):
        self.providers: dict[str, SearchProvider | Callable[[str], list[dict]]] = {}
        self.register_provider(PublicDomainProvider().name, PublicDomainProvider())

    def register_provider(self, name: str, provider) -> None:
        self.providers[name] = provider

    def list_providers(self) -> list[str]:
        return sorted(self.providers)

    def search(self, query: str, provider_name: str | None = None, filters: dict | None = None) -> list[dict]:
        if provider_name and provider_name not in self.providers:
            return []
        providers = [self.providers[provider_name]] if provider_name else self.providers.values()
        results: list[dict] = []
        for provider in providers:
            if hasattr(provider, "enabled") and not provider.enabled:
                continue
            raw_results = provider.search(query, filters) if hasattr(provider, "search") else provider(query)
            for item in raw_results:
                if isinstance(item, SearchResult):
                    results.append(item.to_dict())
                else:
                    results.append(dict(item))
        return results
