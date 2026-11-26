from dataclasses import asdict
from datetime import datetime, timezone
from uuid import UUID

from elasticsearch import AsyncElasticsearch, BadRequestError, NotFoundError
from elasticsearch.helpers import async_bulk

from backend.application.dtos import ReviewSearchResultDTO
from backend.domain.entities import Review


def _to_doc(review: Review) -> dict:
    doc = asdict(review)
    doc["review_id"] = str(review.review_id)
    doc["model_id"] = str(review.model_id)
    date = review.published_at
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    doc["published_at"] = date.isoformat()
    return doc


def _to_review(doc: dict) -> Review:
    return Review(UUID(doc["review_id"]), UUID(doc["model_id"]), doc["title"],
                  doc["content"], datetime.fromisoformat(doc["published_at"]), doc["rating"])


class ElasticsearchReviewAdapter:
    def __init__(self, url: str, index_name: str = "car_reviews") -> None:
        self.url = url
        self.index_name = index_name
        self._client: AsyncElasticsearch | None = None

    def _connection(self) -> AsyncElasticsearch:
        if self._client is None:
            self._client = AsyncElasticsearch(self.url, request_timeout=15)
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def ensure_index(self) -> None:
        client = self._connection()
        if await client.indices.exists(index=self.index_name):
            return
        try:
            await client.indices.create(
                index=self.index_name,
                settings={"number_of_shards": 1, "number_of_replicas": 0},
                mappings={"properties": {
                    "review_id": {"type": "keyword"},
                    "model_id": {"type": "keyword"},
                    "title": {"type": "text", "analyzer": "standard"},
                    "content": {"type": "text", "analyzer": "standard"},
                    "published_at": {"type": "date"},
                    "rating": {"type": "float"},
                }},
            )
        except BadRequestError as exc:
            if exc.error != "resource_already_exists_exception":
                raise

    async def refresh(self) -> None:
        await self._connection().indices.refresh(index=self.index_name)

    async def index_many(self, reviews: list[Review]) -> int:
        if not reviews:
            return 0
        actions = ({"_op_type": "index", "_index": self.index_name,
                    "_id": str(review.review_id), "_source": _to_doc(review)}
                   for review in reviews)
        count, _ = await async_bulk(self._connection(), actions, chunk_size=500)
        return count

    async def create(self, entity: Review) -> Review:
        await self.ensure_index()
        await self._connection().index(index=self.index_name, id=str(entity.review_id),
                                       document=_to_doc(entity), refresh="wait_for")
        return entity

    async def get_by_id(self, entity_id: UUID) -> Review | None:
        try:
            result = await self._connection().get(index=self.index_name, id=str(entity_id))
        except NotFoundError:
            return None
        return _to_review(result["_source"])

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[Review]:
        result = await self._connection().search(index=self.index_name, query={"match_all": {}},
                                                 size=limit, from_=offset, sort=["review_id"])
        return [_to_review(hit["_source"]) for hit in result["hits"]["hits"]]

    async def update(self, entity: Review) -> Review:
        await self._connection().update(index=self.index_name, id=str(entity.review_id),
                                        doc=_to_doc(entity), refresh="wait_for")
        return entity

    async def delete(self, entity_id: UUID) -> bool:
        try:
            await self._connection().delete(index=self.index_name, id=str(entity_id), refresh="wait_for")
        except NotFoundError:
            return False
        return True

    async def search_full_text(self, query: str, limit: int = 20) -> list[ReviewSearchResultDTO]:
        client = self._connection()
        highlight = {"fields": {"content": {"fragment_size": 180, "number_of_fragments": 1}},
                     "pre_tags": ["<em>"], "post_tags": ["</em>"]}
        result = await client.search(
            index=self.index_name, size=limit,
            query={"multi_match": {"query": query, "fields": ["title^2", "content"],
                                   "type": "cross_fields", "operator": "and"}},
            highlight=highlight,
        )
        if not result["hits"]["hits"] and query.split():
            result = await client.search(
                index=self.index_name, size=limit,
                query={"bool": {"must": [
                    {"multi_match": {"query": term, "fields": ["title^2", "content"],
                                     "type": "best_fields", "operator": "and",
                                     "fuzziness": "AUTO", "max_expansions": 30}}
                    for term in query.split()
                ]}},
                highlight=highlight,
            )
        items = []
        for hit in result["hits"]["hits"]:
            doc = hit["_source"]
            fragments = hit.get("highlight", {}).get("content", [])
            snippet = fragments[0].replace("<em>", "").replace("</em>", "") if fragments else doc["content"][:180]
            items.append(ReviewSearchResultDTO(
                review_id=UUID(doc["review_id"]), model_id=UUID(doc["model_id"]),
                title=doc["title"], snippet=snippet, rating=doc["rating"], score=hit["_score"],
            ))
        return items