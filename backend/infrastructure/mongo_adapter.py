from dataclasses import asdict, fields
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

from backend.application.dtos import CarFilterDTO, CrossShardFuelStatsDTO, IngestCarBundleDTO
from backend.domain.entities import CarModel, Engineer, Manufacturer, Technology


def _to_doc(entity, id_field: str) -> dict:
    doc = {key: str(value) if isinstance(value, UUID) else value
           for key, value in asdict(entity).items()}
    doc["_id"] = doc[id_field]
    return doc


def _from_doc(doc: dict, entity_type, *uuid_fields: str):
    values = {field.name: doc[field.name] for field in fields(entity_type)}
    for key in uuid_fields:
        values[key] = UUID(values[key])
    return entity_type(**values)


def _to_car(doc: dict) -> CarModel:
    return _from_doc(doc, CarModel, "model_id", "manufacturer_id")


class MongoCarAdapter:
    def __init__(self, dsn: str, db_name: str = "auto_engineers") -> None:
        self.dsn = dsn
        self.db_name = db_name
        self._client: AsyncIOMotorClient | None = None

    def _collection(self, name: str) -> AsyncIOMotorCollection:
        if self._client is None:
            self._client = AsyncIOMotorClient(self.dsn)
        return self._client[self.db_name][name]

    def _cars_collection(self) -> AsyncIOMotorCollection:
        return self._collection("car_models")

    async def ensure_indexes(self) -> None:
        cars = self._cars_collection()
        await cars.create_index([("fuel_type", 1), ("model_id", 1)])
        await cars.create_index("body_type")
        await cars.create_index("release_year")
        await cars.create_index("manufacturer_id")

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    async def create(self, entity: CarModel) -> CarModel:
        await self._cars_collection().insert_one(_to_doc(entity, "model_id"))
        return entity

    async def create_bundles(self, bundles: list[IngestCarBundleDTO]) -> None:
        if not bundles:
            return
        docs = []
        for bundle in bundles:
            doc = _to_doc(bundle.car_model, "model_id")
            doc["engineer_ids"] = [str(e.engineer_id) for e in bundle.engineers]
            doc["technology_ids"] = [str(t.tech_id) for t in bundle.technologies]
            review = _to_doc(bundle.review, "review_id")
            review.pop("_id")
            doc["review"] = review
            docs.append(doc)
        await self._cars_collection().insert_many(docs, ordered=True)

    async def get_by_id(self, entity_id: UUID) -> CarModel | None:
        doc = await self._cars_collection().find_one({"_id": str(entity_id)})
        return _to_car(doc) if doc is not None else None

    async def _find_cars(self, query: dict, limit: int, offset: int) -> list[CarModel]:
        if limit < 1 or offset < 0:
            raise ValueError("limit must be positive and offset non-negative")
        cursor = self._cars_collection().find(query).sort("_id", 1).skip(offset).limit(limit)
        return [_to_car(doc) async for doc in cursor]

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[CarModel]:
        return await self._find_cars({}, limit, offset)

    async def update(self, entity: CarModel) -> CarModel:
        doc = _to_doc(entity, "model_id")
        doc.pop("_id")
        result = await self._cars_collection().update_one(
            {"_id": str(entity.model_id)}, {"$set": doc}
        )
        if result.matched_count == 0:
            raise LookupError(f"Car not found: {entity.model_id}")
        return entity

    async def delete(self, entity_id: UUID) -> bool:
        result = await self._cars_collection().delete_one({"_id": str(entity_id)})
        return result.deleted_count > 0

    async def filter_cars(self, filters: CarFilterDTO) -> list[CarModel]:
        query = {name: value for name, value in (
            ("body_type", filters.body_type),
            ("fuel_type", filters.fuel_type),
            ("release_year", filters.release_year),
        ) if value is not None}
        return await self._find_cars(query, filters.limit, filters.offset)

    async def get_many_by_ids(self, model_ids: list[UUID]) -> list[CarModel]:
        if not model_ids:
            return []
        cursor = self._cars_collection().find({"_id": {"$in": [str(i) for i in model_ids]}})
        cars = {}
        async for doc in cursor:
            car = _to_car(doc)
            cars[car.model_id] = car
        return [cars[i] for i in model_ids if i in cars]

    async def upsert_manufacturer(self, manufacturer: Manufacturer) -> Manufacturer:
        doc = _to_doc(manufacturer, "manufacturer_id")
        await self._collection("manufacturers").replace_one({"_id": doc["_id"]}, doc, upsert=True)
        return manufacturer

    async def get_manufacturer(self, manufacturer_id: UUID) -> Manufacturer | None:
        doc = await self._collection("manufacturers").find_one({"_id": str(manufacturer_id)})
        return _from_doc(doc, Manufacturer, "manufacturer_id") if doc is not None else None

    async def upsert_engineer(self, engineer: Engineer) -> Engineer:
        doc = _to_doc(engineer, "engineer_id")
        await self._collection("engineers").replace_one({"_id": doc["_id"]}, doc, upsert=True)
        return engineer

    async def get_engineer(self, engineer_id: UUID) -> Engineer | None:
        doc = await self._collection("engineers").find_one({"_id": str(engineer_id)})
        return _from_doc(doc, Engineer, "engineer_id") if doc is not None else None

    async def upsert_technology(self, tech: Technology) -> Technology:
        doc = _to_doc(tech, "tech_id")
        await self._collection("technologies").replace_one({"_id": doc["_id"]}, doc, upsert=True)
        return tech

    async def aggregate_fuel_stats(self) -> list[CrossShardFuelStatsDTO]:
        pipeline = [
            {
                "$group": {
                    "_id": "$fuel_type",
                    "cars_count": {"$sum": 1},
                    "avg_horsepower": {"$avg": "$horsepower"},
                    "avg_acceleration": {"$avg": "$acceleration_0_100"},
                    "min_year": {"$min": "$release_year"},
                    "max_year": {"$max": "$release_year"},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        cursor = self._cars_collection().aggregate(pipeline, allowDiskUse=True)
        return [
            CrossShardFuelStatsDTO(
                fuel_type=doc["_id"],
                cars_count=doc["cars_count"],
                avg_horsepower=round(doc["avg_horsepower"], 2),
                avg_acceleration=round(doc["avg_acceleration"], 2),
                min_year=doc["min_year"],
                max_year=doc["max_year"],
            )
            async for doc in cursor
        ]