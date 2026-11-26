import asyncio
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from backend.application.facade import CarFacade
from backend.application.services import (
    CarGraphService,
    CarMetadataService,
    ReviewSearchService,
)
from backend.domain.entities import CarModel
from backend.infrastructure.es_adapter import ElasticsearchReviewAdapter
from backend.infrastructure.mongo_adapter import MongoCarAdapter
from backend.infrastructure.neo4j_adapter import Neo4jGraphAdapter
from backend.infrastructure.redis_adapter import RedisCacheAdapter
from backend.presentation.controllers import (
    CarController,
    IngestController,
    SearchController,
)


def setup_logging() -> logging.Logger:
    log_dir = Path(os.getenv("LOG_DIR", "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
        force=True,
    )
    return logging.getLogger("auto_engineers")


@dataclass
class AppContainer:
    ingest_controller: IngestController
    car_controller: CarController
    search_controller: SearchController
    mongo_adapter: MongoCarAdapter
    es_adapter: ElasticsearchReviewAdapter


def bootstrap() -> AppContainer:
    mongo_dsn = os.getenv("MONGO_DSN", "mongodb://localhost:27017")
    mongo_adapter = MongoCarAdapter(dsn=mongo_dsn)
    es_adapter = ElasticsearchReviewAdapter(url=os.getenv("ES_URL", "http://localhost:9200"))
    neo4j_adapter = Neo4jGraphAdapter(
        uri="bolt://localhost:7687", user="neo4j", password="password"
    )
    redis_adapter = RedisCacheAdapter(url="redis://localhost:6379/0")

    metadata_service = CarMetadataService(car_repo=mongo_adapter)
    review_service = ReviewSearchService(
        review_repo=es_adapter, cache=None
    )
    graph_service = CarGraphService(graph_repo=neo4j_adapter)

    facade = CarFacade(
        metadata_service=metadata_service,
        review_service=review_service,
        graph_service=graph_service,
        cache=redis_adapter,
    )

    return AppContainer(
        ingest_controller=IngestController(facade=facade),
        car_controller=CarController(facade=facade),
        search_controller=SearchController(facade=facade),
        mongo_adapter=mongo_adapter,
        es_adapter=es_adapter,
    )


async def run_db_demo(container: AppContainer, logger: logging.Logger) -> None:
    sample_car = CarModel(
        model_id=uuid4(),
        manufacturer_id=uuid4(),
        model_name="911 GT3 RS (992)",
        body_type="Купе",
        fuel_type="Бензин",
        release_year=2024,
        horsepower=525,
        acceleration_0_100=3.2,
        drivetrain="Задній",
        video_review_url="https://youtube.com/watch?v=demo1234567",
    )

    print("Підключення до MongoDB та збереження тестової моделі...", flush=True)
    logger.info("Connecting to MongoDB at %s", container.mongo_adapter.dsn)

    await container.mongo_adapter.create(sample_car)
    logger.info(
        "Saved CarModel to MongoDB: id=%s, name=%s",
        sample_car.model_id,
        sample_car.model_name,
    )
    print(f"Модель збережено в БД: {sample_car.model_name} (ID: {sample_car.model_id})", flush=True)

    loaded = await container.car_controller.get_car(sample_car.model_id)
    logger.info("Read back from MongoDB via CarController: %s", loaded)

    if loaded:
        print(
            f"Успішно прочитано з БД: {loaded.model_name}, {loaded.release_year} р., {loaded.horsepower} к.с.",
            flush=True,
        )
    else:
        print("Не вдалося знайти збережену модель у базі даних.", flush=True)


if __name__ == "__main__":
    logger = setup_logging()
    container = bootstrap()
    logger.info("Application container wired successfully")
    print("Контейнер застосунку успішно зібрано", flush=True)

    if os.getenv("RUN_DB_DEMO") == "1":
        asyncio.run(run_db_demo(container, logger))