import asyncio
import json
import os
import unittest
from unittest.mock import AsyncMock
from uuid import uuid4

from backend.application.dtos import ReviewSearchResultDTO
from backend.application.ports import CacheUnavailableError
from backend.application.services import ReviewSearchService


class SearchCacheTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.item = ReviewSearchResultDTO(uuid4(), uuid4(), 'BMW', 'Турбонаддув', 8.2, 2.5)
        self.repo = AsyncMock()
        self.repo.search_full_text.return_value = [self.item]
        self.cache = AsyncMock()
        self.data = {}

        async def save(key, value, ttl_seconds):
            self.data[key] = value

        self.cache.get.side_effect = self.data.get
        self.cache.set.side_effect = save
        self.service = ReviewSearchService(self.repo, self.cache)

    async def test_normalized_key_hit_and_uuid_roundtrip(self):
        first = await self.service.search(' BMW  турбонаддув ', limit=5)
        second = await self.service.search('ТУРБОНАДДУВ bmw', limit=5)
        self.assertEqual(first.cache_status, 'miss')
        self.assertEqual(second.cache_status, 'hit')
        self.assertEqual(second.source, 'cache')
        self.assertEqual(second.items, [self.item])
        self.assertEqual(second.raw_query, 'ТУРБОНАДДУВ bmw')
        self.assertEqual(first.cache_stats.hits, 0)
        self.assertEqual(second.cache_stats.hits, 1)
        self.assertEqual(second.cache_stats.misses, 1)
        self.repo.search_full_text.assert_awaited_once_with('bmw турбонаддув', limit=5)
        self.cache.set.assert_awaited_once()
        self.assertEqual(self.cache.set.await_args.kwargs['ttl_seconds'], 300)

    async def test_different_limits_use_different_keys(self):
        await self.service.search('BMW', limit=5)
        second = await self.service.search('BMW', limit=10)
        self.assertEqual(second.cache_status, 'miss')
        self.assertEqual(len(self.data), 2)
        self.assertEqual(self.repo.search_full_text.await_count, 2)

    async def test_empty_results_cached(self):
        self.repo.search_full_text.return_value = []
        await self.service.search('xyzabc123')
        second = await self.service.search('xyzabc123')
        self.assertEqual(second.items, [])
        self.assertEqual(second.cache_status, 'hit')
        self.assertEqual(self.repo.search_full_text.await_count, 1)

    async def test_unavailable_cache_bypassed_and_recovers(self):
        self.cache.get.side_effect = CacheUnavailableError('offline')
        first = await self.service.search('BMW')
        self.assertEqual(first.cache_status, 'bypass')
        self.assertEqual(first.source, 'elasticsearch')
        self.assertEqual(first.items, [self.item])
        self.assertEqual(first.cache_stats.bypasses, 1)
        self.assertEqual(first.cache_stats.misses, 0)
        self.cache.set.assert_not_awaited()
        self.cache.get.side_effect = self.data.get
        await self.service.search('BMW')
        third = await self.service.search('BMW')
        self.assertEqual(third.cache_status, 'hit')
        self.assertEqual(third.cache_stats.hits, 1)
        self.assertEqual(third.cache_stats.misses, 1)
        self.assertEqual(third.cache_stats.bypasses, 1)

    async def test_failed_cache_write_does_not_fail_search(self):
        self.cache.set.side_effect = CacheUnavailableError('offline')
        result = await self.service.search('BMW')
        self.assertEqual(result.cache_status, 'miss_write_failed')
        self.assertEqual(result.items, [self.item])
        self.assertEqual(result.cache_stats.misses, 1)
        self.assertEqual(result.cache_stats.write_errors, 1)

    async def test_corrupt_cache_rebuilt(self):
        self.data['search:v1:bmw:20'] = json.dumps([{'review_id': 'invalid'}])
        first = await self.service.search('BMW')
        second = await self.service.search('BMW')
        self.assertEqual(first.cache_status, 'miss')
        self.assertEqual(second.cache_status, 'hit')
        self.assertEqual(second.items, [self.item])

    async def test_without_cache(self):
        result = await ReviewSearchService(self.repo).search('BMW')
        self.assertEqual(result.cache_status, 'disabled')
        self.assertEqual(result.source, 'elasticsearch')


@unittest.skipUnless(os.getenv('RUN_REDIS_INTEGRATION') == '1', 'Redis integration disabled')
class RedisIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_roundtrip_and_expiration(self):
        from backend.infrastructure.redis_adapter import RedisCacheAdapter

        adapter = RedisCacheAdapter(os.environ['REDIS_URL'])
        key = f'test:cache:{uuid4()}'
        try:
            self.assertIsNone(await adapter.get(key))
            await adapter.set(key, 'тест Redis', ttl_seconds=1)
            self.assertEqual(await adapter.get(key), 'тест Redis')
            await asyncio.sleep(1.2)
            self.assertIsNone(await adapter.get(key))
        finally:
            await adapter.close()
