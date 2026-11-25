import asyncio
import unittest
from uuid import uuid4

from backend.application.dtos import GeneratorRateDTO
from backend.domain.normalizer import normalize_query
from backend.main import bootstrap


class ArchitectureSkeletonTests(unittest.TestCase):
    def test_bootstrap_wires_controllers(self) -> None:
        container = bootstrap()
        self.assertIsNotNone(container.car_controller)
        self.assertIsNotNone(container.search_controller)
        self.assertIsNotNone(container.ingest_controller)

    def test_query_normalization_order_invariant(self) -> None:
        q1 = normalize_query("  Активна   Аеродинаміка Купе ")
        q2 = normalize_query("купе аеродинаміка активна")
        self.assertEqual(q1, q2)
        self.assertEqual(q1, "аеродинаміка активна купе")

    def test_rate_validation(self) -> None:
        container = bootstrap()
        result = asyncio.run(
            container.ingest_controller.set_rate(GeneratorRateDTO(target_rps=250))
        )
        self.assertEqual(result["target_rps"], 250)

        with self.assertRaises(ValueError):
            asyncio.run(
                container.ingest_controller.set_rate(GeneratorRateDTO(target_rps=9999))
            )

    def test_stub_adapters_raise_not_implemented(self) -> None:
        container = bootstrap()
        with self.assertRaises(NotImplementedError):
            asyncio.run(container.car_controller.get_recommendations(uuid4()))
        with self.assertRaises(NotImplementedError):
            asyncio.run(container.search_controller.search_reviews("активна аеродинаміка"))


if __name__ == "__main__":
    unittest.main()