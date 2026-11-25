from uuid import UUID

from backend.domain.entities import CarModel


class Neo4jGraphAdapter:
    """Driven Adapter for Neo4j graph relations and recommendations."""

    def __init__(self, uri: str, user: str, password: str) -> None:
        self.uri = uri
        self.user = user
        self.password = password

    async def upsert_relations(
        self,
        car: CarModel,
        manufacturer_id: UUID,
        engineer_ids: list[UUID],
        tech_ids: list[UUID],
    ) -> None:
        raise NotImplementedError("Neo4j MERGE relations is not connected yet")

    async def get_engineer_model_ids(self, engineer_id: UUID) -> list[UUID]:
        raise NotImplementedError("Neo4j engineer traversal is not connected yet")

    async def get_similar_model_ids(
        self, model_id: UUID, limit: int = 5
    ) -> list[UUID]:
        raise NotImplementedError("Neo4j recommendations query is not connected yet")