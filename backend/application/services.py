import json
import logging
from dataclasses import asdict, replace
from uuid import UUID

from backend.application.dtos import (
    CacheStatsDTO,
    CarFilterDTO,
    CrossShardFuelStatsDTO,
    ReviewSearchResultDTO,
    SearchResponseDTO,
)
from backend.application.ports import (
    CacheUnavailableError,
    ICachePort,
    ICarDocumentPort,
    ICarGraphPort,
    IReviewSearchPort,
)
from backend.domain.entities import (
    CarModel,
    Engineer,
    Manufacturer,
    Review,
    Technology,
)
from backend.domain.normalizer import normalize_query

logger = logging.getLogger("auto_engineers.search")


class CarMetadataService:
    def __init__(self, car_repo: ICarDocumentPort) -> None:
        self._car_repo = car_repo

    async def save_metadata(
        self,
        manufacturer: Manufacturer,
        car: CarModel,
        engineers: list[Engineer],
        technologies: list[Technology],
    ) -> CarModel:
        await self._car_repo.upsert_manufacturer(manufacturer)
        for eng in engineers:
            await self._car_repo.upsert_engineer(eng)
        for tech in technologies:
            await self._car_repo.upsert_technology(tech)
        return await self._car_repo.create(car)

    async def get_car(self, model_id: UUID) -> CarModel | None:
        return await self._car_repo.get_by_id(model_id)

    async def filter_cars(self, filters: CarFilterDTO) -> list[CarModel]:
        return await self._car_repo.filter_cars(filters)

    async def aggregate_fuel_stats(self) -> list[CrossShardFuelStatsDTO]:
        return await self._car_repo.aggregate_fuel_stats()

    async def get_cars_by_ids(self, model_ids: list[UUID]) -> list[CarModel]:
        return await self._car_repo.get_many_by_ids(model_ids)

    async def get_engineer(self, engineer_id: UUID) -> Engineer | None:
        return await self._car_repo.get_engineer(engineer_id)


class ReviewSearchService:
    def __init__(
        self, review_repo: IReviewSearchPort, cache: ICachePort | None = None
    ) -> None:
        self._review_repo = review_repo
        self._cache = cache
        self._stats = CacheStatsDTO()

    async def index_review(self, review: Review) -> Review:
        return await self._review_repo.create(review)

    async def search(self, raw_query: str, limit: int = 20) -> SearchResponseDTO:
        normalized = normalize_query(raw_query)
        cache_key = f"search:v1:{normalized}:{limit}"
        status = "disabled"

        if self._cache is not None:
            try:
                cached = await self._cache.get(cache_key)
                if cached is not None:
                    raw_items = json.loads(cached)
                    if not isinstance(raw_items, list):
                        raise ValueError("Invalid cache payload")
                    items = [
                        ReviewSearchResultDTO(**{
                            **item,
                            "review_id": UUID(item["review_id"]),
                            "model_id": UUID(item["model_id"]),
                        }) for item in raw_items
                    ]
                    self._stats.hits += 1
                    return SearchResponseDTO(
                        raw_query=raw_query, normalized_query=normalized,
                        source="cache", items=items, cache_status="hit",
                        cache_stats=replace(self._stats),
                    )
                status = "miss"
            except CacheUnavailableError:
                logger.warning("Redis unavailable; searching Elasticsearch directly")
                self._stats.bypasses += 1
                status = "bypass"
            except (ValueError, TypeError, KeyError, AttributeError):
                logger.warning("Invalid cached search payload; rebuilding result")
                status = "miss"

            if status == "miss":
                self._stats.misses += 1

        items = await self._review_repo.search_full_text(normalized, limit=limit)
        if self._cache is not None and status == "miss":
            payload = json.dumps([asdict(item) for item in items], default=str)
            try:
                await self._cache.set(cache_key, payload, ttl_seconds=300)
            except CacheUnavailableError:
                logger.warning("Redis cache write failed; returning Elasticsearch result")
                self._stats.write_errors += 1
                status = "miss_write_failed"

        return SearchResponseDTO(
            raw_query=raw_query, normalized_query=normalized,
            source="elasticsearch", items=items, cache_status=status,
            cache_stats=replace(self._stats),
        )


class CarGraphService:
    def __init__(self, graph_repo: ICarGraphPort) -> None:
        self._graph_repo = graph_repo

    async def link_car(
        self,
        car: CarModel,
        manufacturer_id: UUID,
        engineer_ids: list[UUID],
        tech_ids: list[UUID],
    ) -> None:
        await self._graph_repo.upsert_relations(
            car=car,
            manufacturer_id=manufacturer_id,
            engineer_ids=engineer_ids,
            tech_ids=tech_ids,
        )

    async def get_engineer_model_ids(self, engineer_id: UUID) -> list[UUID]:
        return await self._graph_repo.get_engineer_model_ids(engineer_id)

    async def get_similar_model_ids(
        self, model_id: UUID, limit: int = 5
    ) -> list[UUID]:
        return await self._graph_repo.get_similar_model_ids(model_id, limit=limit)