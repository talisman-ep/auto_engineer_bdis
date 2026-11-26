import asyncio
import os

from backend.infrastructure.es_adapter import ElasticsearchReviewAdapter
from backend.infrastructure.mongo_adapter import MongoCarAdapter


async def run() -> None:
    mongo = MongoCarAdapter(os.getenv("MONGO_DSN", "mongodb://localhost:27017"))
    es = ElasticsearchReviewAdapter(os.getenv("ES_URL", "http://localhost:9200"))
    count = 0
    batch = []
    try:
        await es.ensure_index()
        async for review in mongo.iter_reviews():
            batch.append(review)
            if len(batch) >= 500:
                count += await es.index_many(batch)
                batch.clear()
        count += await es.index_many(batch)
        await es.refresh()
        print(f"Indexed reviews: {count}", flush=True)
    finally:
        mongo.close()
        await es.close()


if __name__ == "__main__":
    asyncio.run(run())
