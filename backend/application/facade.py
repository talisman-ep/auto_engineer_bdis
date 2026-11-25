import asyncio
from uuid import UUID

from backend.application.dtos import (
    CarFilterDTO,
    EngineerPortfolioDTO,
    GeneratorRateDTO,
    IngestCarBundleDTO,
    SearchResponseDTO,
)
from backend.application.ports import ICachePort
from backend.application.services import (
    CarGraphService,
    CarMetadataService,
    ReviewSearchService,
)
from backend.domain.entities import CarModel


class CarFacade:
    def __init__(
        self,
        metadata_service: CarMetadataService,
        review_service: ReviewSearchService,
        graph_service: CarGraphService,
        cache: ICachePort,
    ) -> None:
        self._metadata = metadata_service
        self._reviews = review_service
        self._graph = graph_service
        self._cache = cache
        self._current_rps = 10

    # --- CQRS Write ---

    async def ingest_car_bundle(self, bundle: IngestCarBundleDTO) -> UUID:
        engineer_ids = [e.engineer_id for e in bundle.engineers]
        tech_ids = [t.tech_id for t in bundle.technologies]

        await asyncio.gather(
            self._metadata.save_metadata(
                manufacturer=bundle.manufacturer,
                car=bundle.car_model,
                engineers=bundle.engineers,
                technologies=bundle.technologies,
            ),
            self._reviews.index_review(bundle.review),
            self._graph.link_car(
                car=bundle.car_model,
                manufacturer_id=bundle.manufacturer.manufacturer_id,
                engineer_ids=engineer_ids,
                tech_ids=tech_ids,
            ),
        )
        await self._cache.increment_counter("saved_docs")
        return bundle.car_model.model_id

    async def update_generator_rate(self, dto: GeneratorRateDTO) -> int:
        if not 10 <= dto.target_rps <= 5000:
            raise ValueError("target_rps must be between 10 and 5000")
        self._current_rps = dto.target_rps
        return self._current_rps

    # --- CQRS Read ---

    async def filter_cars(self, filters: CarFilterDTO) -> list[CarModel]:
        return await self._metadata.filter_cars(filters)

    async def get_car(self, model_id: UUID) -> CarModel | None:
        return await self._metadata.get_car(model_id)

    async def search_reviews(
        self, query: str, limit: int = 20
    ) -> SearchResponseDTO:
        return await self._reviews.search(query, limit=limit)

    async def get_engineer_portfolio(
        self, engineer_id: UUID
    ) -> EngineerPortfolioDTO | None:
        engineer = await self._metadata.get_engineer(engineer_id)
        if engineer is None:
            return None
        model_ids = await self._graph.get_engineer_model_ids(engineer_id)
        models = await self._metadata.get_cars_by_ids(model_ids)
        return EngineerPortfolioDTO(engineer=engineer, models=models)

    async def get_recommendations(
        self, model_id: UUID, limit: int = 5
    ) -> list[CarModel]:
        similar_ids = await self._graph.get_similar_model_ids(model_id, limit=limit)
        return await self._metadata.get_cars_by_ids(similar_ids)