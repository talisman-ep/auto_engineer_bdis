from uuid import UUID

from backend.application.dtos import CarFilterDTO
from backend.domain.entities import CarModel, Engineer, Manufacturer, Technology


class MongoCarAdapter:
    """Driven Adapter for sharded MongoDB (Motor async client)."""

    def __init__(self, dsn: str, db_name: str = "auto_engineers") -> None:
        self.dsn = dsn
        self.db_name = db_name

    async def create(self, entity: CarModel) -> CarModel:
        raise NotImplementedError("MongoDB insert is not connected yet")

    async def get_by_id(self, entity_id: UUID) -> CarModel | None:
        raise NotImplementedError("MongoDB find_one is not connected yet")

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[CarModel]:
        raise NotImplementedError("MongoDB find is not connected yet")

    async def update(self, entity: CarModel) -> CarModel:
        raise NotImplementedError("MongoDB update_one is not connected yet")

    async def delete(self, entity_id: UUID) -> bool:
        raise NotImplementedError("MongoDB delete_one is not connected yet")

    async def filter_cars(self, filters: CarFilterDTO) -> list[CarModel]:
        raise NotImplementedError("MongoDB filtered query is not connected yet")

    async def get_many_by_ids(self, model_ids: list[UUID]) -> list[CarModel]:
        raise NotImplementedError("MongoDB $in query is not connected yet")

    async def upsert_manufacturer(self, manufacturer: Manufacturer) -> Manufacturer:
        raise NotImplementedError("MongoDB upsert_manufacturer is not connected yet")

    async def get_manufacturer(self, manufacturer_id: UUID) -> Manufacturer | None:
        raise NotImplementedError("MongoDB get_manufacturer is not connected yet")

    async def upsert_engineer(self, engineer: Engineer) -> Engineer:
        raise NotImplementedError("MongoDB upsert_engineer is not connected yet")

    async def get_engineer(self, engineer_id: UUID) -> Engineer | None:
        raise NotImplementedError("MongoDB get_engineer is not connected yet")

    async def upsert_technology(self, tech: Technology) -> Technology:
        raise NotImplementedError("MongoDB upsert_technology is not connected yet")