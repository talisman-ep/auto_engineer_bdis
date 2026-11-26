import json
from dataclasses import asdict
from uuid import UUID

from backend.application.dtos import (
    CarFilterDTO,
    CrossShardFuelStatsDTO,
    ReviewSearchResultDTO,
    SearchResponseDTO,
)
from backend.application.ports import (
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
        self, review_repo: IReviewSearchPort, cache: ICachePort
    ) -> None:
        self._review_repo = review_repo
        self._cache = cache

    async def index_review(self, review: Review) -> Review:
        return await self._review_repo.create(review)

    async def search(self, raw_query: str, limit: int = 20) -> SearchResponseDTO:
        normalized = normalize_query(raw_query)
        cache_key = f"search:{normalized}:{limit}"

        cached = await self._cache.get(cache_key)
        if cached is not None:
            raw_items = json.loads(cached)
            items = [ReviewSearchResultDTO(**item) for item in raw_items]
            return SearchResponseDTO(
                raw_query=raw_query,
                normalized_query=normalized,
                source="cache",
                items=items,
            )

        items = await self._review_repo.search_full_text(normalized, limit=limit)
        payload = json.dumps([asdict(item) for item in items], default=str)
        await self._cache.set(cache_key, payload, ttl_seconds=300)

        return SearchResponseDTO(
            raw_query=raw_query,
            normalized_query=normalized,
            source="elasticsearch",
            items=items,
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