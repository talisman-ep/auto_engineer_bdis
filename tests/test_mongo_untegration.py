import os
import unittest
from dataclasses import replace
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorClient

from backend.application.dtos import CarFilterDTO
from backend.application.services import CarMetadataService
from backend.generator import CarGenerator
from backend.infrastructure.mongo_adapter import MongoCarAdapter


@unittest.skipUnless(os.getenv("MONGO_TEST_DSN"), "MONGO_TEST_DSN not configured")
class MongoIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_save_read_filter_update_delete(self):
        dsn = os.environ["MONGO_TEST_DSN"]
        db_name = f"auto_engineers_test_{uuid4().hex}"
        repo = MongoCarAdapter(dsn, db_name)
        client = AsyncIOMotorClient(dsn)
        try:
            await repo.ensure_indexes()
            service = CarMetadataService(repo)
            bundle = CarGenerator().generate()
            brand, car, engineers = bundle.manufacturer, bundle.car_model, bundle.engineers
            await repo.upsert_manufacturer(brand)
            for engineer in engineers:
                await repo.upsert_engineer(engineer)
            for tech in bundle.technologies:
                await repo.upsert_technology(tech)
            await repo.create_bundles([bundle])
            doc = await client[db_name].car_models.find_one({"_id": str(car.model_id)})
            self.assertEqual(doc["review"]["content"], bundle.review.content)
            self.assertEqual(doc["engineer_ids"], [str(e.engineer_id) for e in engineers])
            self.assertEqual(doc["technology_ids"], [str(t.tech_id) for t in bundle.technologies])
            self.assertEqual(await service.get_car(car.model_id), car)
            self.assertEqual(await repo.get_manufacturer(brand.manufacturer_id), brand)
            self.assertEqual(await repo.get_engineer(engineers[0].engineer_id), engineers[0])
            self.assertEqual(await repo.list_all(), [car])
            self.assertEqual(await service.filter_cars(CarFilterDTO(fuel_type=car.fuel_type, release_year=car.release_year)), [car])
            self.assertEqual(await service.filter_cars(CarFilterDTO(release_year=1800)), [])
            self.assertEqual(await repo.get_many_by_ids([uuid4(), car.model_id]), [car])
            self.assertIsNone(await service.get_car(uuid4()))
            changed = replace(car, horsepower=car.horsepower + 10)
            self.assertEqual(await repo.update(changed), changed)
            self.assertEqual(await service.get_car(car.model_id), changed)
            updated = await client[db_name].car_models.find_one({"_id": str(car.model_id)})
            self.assertEqual(updated["review"], doc["review"])
            self.assertEqual(updated["engineer_ids"], doc["engineer_ids"])
            self.assertTrue(await repo.delete(car.model_id))
            self.assertFalse(await repo.delete(car.model_id))
        finally:
            repo.close()
            try:
                await client.drop_database(db_name)
            finally:
                client.close()
