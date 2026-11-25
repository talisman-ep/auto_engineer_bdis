from dataclasses import dataclass

from backend.application.facade import CarFacade
from backend.application.services import (
    CarGraphService,
    CarMetadataService,
    ReviewSearchService,
)
from backend.infrastructure.es_adapter import ElasticsearchReviewAdapter
from backend.infrastructure.mongo_adapter import MongoCarAdapter
from backend.infrastructure.neo4j_adapter import Neo4jGraphAdapter
from backend.infrastructure.redis_adapter import RedisCacheAdapter
from backend.presentation.controllers import (
    CarController,
    IngestController,
    SearchController,
)


@dataclass
class AppContainer:
    ingest_controller: IngestController
    car_controller: CarController
    search_controller: SearchController


def bootstrap() -> AppContainer:
    mongo_adapter = MongoCarAdapter(dsn="mongodb://localhost:27017")
    es_adapter = ElasticsearchReviewAdapter(url="http://localhost:9200")
    neo4j_adapter = Neo4jGraphAdapter(
        uri="bolt://localhost:7687", user="neo4j", password="password"
    )
    redis_adapter = RedisCacheAdapter(url="redis://localhost:6379/0")

    metadata_service = CarMetadataService(car_repo=mongo_adapter)
    review_service = ReviewSearchService(
        review_repo=es_adapter, cache=redis_adapter
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
    )


if __name__ == "__main__":
    app = bootstrap()
    print("Тестовий запуск", app)