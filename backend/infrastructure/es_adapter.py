from uuid import UUID

from backend.application.dtos import ReviewSearchResultDTO
from backend.domain.entities import Review


class ElasticsearchReviewAdapter:
    """Driven Adapter for Elasticsearch full-text search (index: car_reviews)."""

    def __init__(self, url: str, index_name: str = "car_reviews") -> None:
        self.url = url
        self.index_name = index_name

    async def create(self, entity: Review) -> Review:
        raise NotImplementedError("Elasticsearch index document is not connected yet")

    async def get_by_id(self, entity_id: UUID) -> Review | None:
        raise NotImplementedError("Elasticsearch get is not connected yet")

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[Review]:
        raise NotImplementedError("Elasticsearch match_all is not connected yet")

    async def update(self, entity: Review) -> Review:
        raise NotImplementedError("Elasticsearch update is not connected yet")

    async def delete(self, entity_id: UUID) -> bool:
        raise NotImplementedError("Elasticsearch delete is not connected yet")

    async def search_full_text(
        self, query: str, limit: int = 20
    ) -> list[ReviewSearchResultDTO]:
        raise NotImplementedError("Elasticsearch full-text search is not connected yet")