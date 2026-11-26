import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

from backend.application.dtos import ReviewSearchResultDTO
from backend.application.services import ReviewSearchService
from backend.domain.entities import Review


class ReviewSearchServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_normalized_search_without_cache(self):
        item = ReviewSearchResultDTO(uuid4(), uuid4(), 'Огляд BMW', 'Турбонаддув', 8.2, 2.5)
        repo = AsyncMock()
        repo.search_full_text.return_value = [item]
        service = ReviewSearchService(repo)
        result = await service.search('  Турбонаддув   BMW  ', limit=5)
        repo.search_full_text.assert_awaited_once_with('bmw турбонаддув', limit=5)
        self.assertEqual(result.items, [item])
        self.assertEqual(result.source, 'elasticsearch')
        self.assertEqual(result.normalized_query, 'bmw турбонаддув')

    async def test_empty_results(self):
        repo = AsyncMock()
        repo.search_full_text.return_value = []
        result = await ReviewSearchService(repo).search('невідомеслово')
        self.assertEqual(result.items, [])
        self.assertEqual(result.source, 'elasticsearch')


class ElasticsearchAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_search_mapping(self):
        from backend.infrastructure.es_adapter import ElasticsearchReviewAdapter, _to_doc, _to_review

        review = Review(uuid4(), uuid4(), 'Огляд BMW', 'Опис: турбонаддув.', datetime.now(timezone.utc), 8.2)
        self.assertEqual(_to_review(_to_doc(review)), review)
        adapter = ElasticsearchReviewAdapter('http://localhost:9200')
        client = AsyncMock()
        client.search.return_value = {'hits': {'hits': [{
            '_source': _to_doc(review), '_score': 3.5,
            'highlight': {'content': ['Опис: <em>турбонаддув</em>.']},
        }]}}
        adapter._client = client
        items = await adapter.search_full_text('bmw турбонаддув', limit=5)
        self.assertEqual(items[0].model_id, review.model_id)
        self.assertEqual(items[0].snippet, 'Опис: турбонаддув.')
        self.assertEqual(items[0].score, 3.5)
        call = client.search.await_args.kwargs
        self.assertEqual(call['index'], 'car_reviews')
        self.assertEqual(call['size'], 5)
        self.assertEqual(call['query']['multi_match']['operator'], 'and')
        await adapter.close()
