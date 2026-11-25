from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

from backend.application.dtos import CarFilterDTO
from backend.domain.entities import CarModel, Engineer, Manufacturer, Technology


class MongoCarAdapter:
    """Driven Adapter for sharded MongoDB (Motor async client)."""

    def __init__(self, dsn: str, db_name: str = "auto_engineers") -> None:
        self.dsn = dsn
        self.db_name = db_name
        self._client: AsyncIOMotorClient | None = None

    def _cars_collection(self) -> AsyncIOMotorCollection:
        if self._client is None:
            self._client = AsyncIOMotorClient(self.dsn)
        return self._client[self.db_name]["car_models"]

    async def create(self, entity: CarModel) -> CarModel:
        doc = {
            "_id": str(entity.model_id),
            "model_id": str(entity.model_id),
            "manufacturer_id": str(entity.manufacturer_id),
            "model_name": entity.model_name,
            "body_type": entity.body_type,
            "fuel_type": entity.fuel_type,
            "release_year": entity.release_year,
            "horsepower": entity.horsepower,
            "acceleration_0_100": entity.acceleration_0_100,
            "drivetrain": entity.drivetrain,
            "video_review_url": entity.video_review_url,
        }
        await self._cars_collection().insert_one(doc)
        return entity

    async def get_by_id(self, entity_id: UUID) -> CarModel | None:
        doc = await self._cars_collection().find_one({"_id": str(entity_id)})
        if doc is None:
            return None
        return CarModel(
            model_id=UUID(doc["model_id"]),
            manufacturer_id=UUID(doc["manufacturer_id"]),
            model_name=doc["model_name"],
            body_type=doc["body_type"],
            fuel_type=doc["fuel_type"],
            release_year=doc["release_year"],
            horsepower=doc["horsepower"],
            acceleration_0_100=doc["acceleration_0_100"],
            drivetrain=doc["drivetrain"],
            video_review_url=doc["video_review_url"],
        )

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