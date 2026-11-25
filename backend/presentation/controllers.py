from uuid import UUID

from backend.application.dtos import (
    CarFilterDTO,
    EngineerPortfolioDTO,
    GeneratorRateDTO,
    IngestCarBundleDTO,
    SearchResponseDTO,
)
from backend.application.facade import CarFacade
from backend.domain.entities import CarModel


class IngestController:
    """Command API: POST /api/ingest, PATCH /api/rate"""

    def __init__(self, facade: CarFacade) -> None:
        self._facade = facade

    async def ingest_bundle(self, payload: IngestCarBundleDTO) -> dict[str, str]:
        model_id = await self._facade.ingest_car_bundle(payload)
        return {"status": "saved", "model_id": str(model_id)}

    async def set_rate(self, payload: GeneratorRateDTO) -> dict[str, int]:
        rps = await self._facade.update_generator_rate(payload)
        return {"target_rps": rps}


class CarController:
    """Query API: GET /api/cars, /api/cars/{id}, /api/engineers/{id}, /api/recs/{id}"""

    def __init__(self, facade: CarFacade) -> None:
        self._facade = facade

    async def list_cars(self, filters: CarFilterDTO) -> list[CarModel]:
        return await self._facade.filter_cars(filters)

    async def get_car(self, model_id: UUID) -> CarModel | None:
        return await self._facade.get_car(model_id)

    async def get_engineer_works(
        self, engineer_id: UUID
    ) -> EngineerPortfolioDTO | None:
        return await self._facade.get_engineer_portfolio(engineer_id)

    async def get_recommendations(
        self, model_id: UUID, limit: int = 5
    ) -> list[CarModel]:
        return await self._facade.get_recommendations(model_id, limit=limit)


class SearchController:
    """Query API: GET /api/search"""

    def __init__(self, facade: CarFacade) -> None:
        self._facade = facade

    async def search_reviews(
        self, query: str, limit: int = 20
    ) -> SearchResponseDTO:
        return await self._facade.search_reviews(query, limit=limit)