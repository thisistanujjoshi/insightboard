"""Product search behind a small protocol.

InMemorySearchIndex for dev/tests; ElasticsearchIndex (INSIGHT_SEARCH=elasticsearch)
for real deployments — same pluggable pattern as the rest of the portfolio.
"""

from typing import Protocol


class SearchIndex(Protocol):
    def index_product(self, tenant_id: str, sku: str, name: str) -> None: ...
    def search(self, tenant_id: str, query: str, limit: int = 10) -> list[dict]: ...


class InMemorySearchIndex:
    def __init__(self) -> None:
        self._docs: dict[tuple[str, str], dict] = {}

    def index_product(self, tenant_id: str, sku: str, name: str) -> None:
        self._docs[(tenant_id, sku)] = {"sku": sku, "name": name}

    def search(self, tenant_id: str, query: str, limit: int = 10) -> list[dict]:
        q = query.lower()
        return [
            d for (tid, _), d in self._docs.items()
            if tid == tenant_id and q in d["name"].lower()
        ][:limit]


class ElasticsearchIndex:
    def __init__(self, url: str) -> None:
        from elasticsearch import Elasticsearch

        self._es = Elasticsearch(url)

    def index_product(self, tenant_id: str, sku: str, name: str) -> None:
        self._es.index(index=f"products-{tenant_id}", id=sku,
                       document={"sku": sku, "name": name})

    def search(self, tenant_id: str, query: str, limit: int = 10) -> list[dict]:
        result = self._es.search(index=f"products-{tenant_id}",
                                 query={"match": {"name": query}}, size=limit)
        return [hit["_source"] for hit in result["hits"]["hits"]]


def create_index(kind: str, es_url: str) -> SearchIndex:
    if kind == "elasticsearch":
        return ElasticsearchIndex(es_url)
    return InMemorySearchIndex()
