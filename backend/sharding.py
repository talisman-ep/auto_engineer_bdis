import argparse
import csv
import os
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path

from bson import MinKey
from pymongo import MongoClient
from pymongo.write_concern import WriteConcern
from pymongo.errors import OperationFailure, PyMongoError

from backend.generator import CarGenerator, FUEL_TYPES
from backend.infrastructure.mongo_adapter import _to_doc

SHARDS = {f"shard{i}": f"rsShard{i}" for i in range(1, 4)}
KEY = {"fuel_type": 1, "model_id": 1}
DB_NAME = "auto_engineers"
BENCH_DB = "auto_engineers_benchmark"
DSN = os.getenv("MONGO_DSN", "mongodb://localhost:27017")


def wait_primary(client, host):
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        try:
            if client.admin.command("hello").get("isWritablePrimary"):
                return
        except PyMongoError:
            pass
        time.sleep(1)
    raise RuntimeError(f"No primary at {host}")


def init_replicas():
    for host, name in {"configsvr": "rsConfig", **SHARDS}.items():
        with MongoClient(f"mongodb://{host}:27017/?directConnection=true",
                         serverSelectionTimeoutMS=10000) as client:
            try:
                status = client.admin.command("replSetGetStatus")
                if status["set"] != name:
                    raise RuntimeError(f"Unexpected replica set: {status['set']}")
            except OperationFailure as exc:
                if exc.code != 94:
                    raise
                config = {"_id": name, "members": [{"_id": 0, "host": f"{host}:27017"}]}
                if host == "configsvr":
                    config["configsvr"] = True
                client.admin.command("replSetInitiate", config)
            wait_primary(client, host)
            print(f"{host}: {name} PRIMARY", flush=True)


def require_router(client):
    if client.admin.command("hello").get("msg") != "isdbgrid":
        raise RuntimeError("Connect through mongos, not directly to a mongod")


@contextmanager
def paused_balancer(client):
    enabled = client.admin.command("balancerStatus")["mode"] != "off"
    client.admin.command("balancerStop")
    try:
        yield
    finally:
        if enabled:
            client.admin.command("balancerStart")


def chunks_for(client, namespace):
    meta = client.config.collections.find_one({"_id": namespace})
    if not meta:
        return []
    return list(client.config.chunks.find({"uuid": meta["uuid"]}).sort("min", 1))


def split_points():
    points = []
    for i, fuel in enumerate(sorted(FUEL_TYPES)):
        if i:
            points.append({"fuel_type": fuel, "model_id": MinKey()})
        for prefix in ("55555555", "aaaaaaaa"):
            points.append({"fuel_type": fuel, "model_id": f"{prefix}-0000-0000-0000-000000000000"})
    return points


def prepare_collection(client, db_name, name, targets):
    db = client[db_name]
    col = db[name]
    namespace = f"{db_name}.{name}"
    client.admin.command("enableSharding", db_name)
    meta = client.config.collections.find_one({"_id": namespace})
    if meta and dict(meta["key"]) != KEY:
        raise RuntimeError(f"Unexpected shard key for {namespace}")
    if col.count_documents({}) != 0:
        if not meta or set(c["shard"] for c in chunks_for(client, namespace)) != set(targets):
            raise RuntimeError(f"Refusing to rearrange populated collection {namespace}")
        print(f"{namespace}: existing populated collection, unchanged", flush=True)
        return
    col.create_index(list(KEY.items()))
    for field in ("body_type", "release_year", "manufacturer_id"):
        col.create_index(field)
    if not meta:
        client.admin.command("shardCollection", namespace, key=KEY)
    client.admin.command("configureCollectionBalancing", namespace, enableAutoMerger=False)
    for point in split_points():
        if not any(c["min"] == point for c in chunks_for(client, namespace)):
            client.admin.command("split", namespace, middle=point)
    chunks = chunks_for(client, namespace)
    if len(chunks) != 12:
        raise RuntimeError(f"Expected 12 chunks, got {len(chunks)} for {namespace}")
    for i, chunk in enumerate(chunks):
        target = targets[i % len(targets)]
        if chunk["shard"] != target:
            client.admin.command("moveChunk", namespace, bounds=[chunk["min"], chunk["max"]], to=target)
    actual = chunks_for(client, namespace)
    if len(actual) != 12 or any(c["shard"] != targets[i % len(targets)] for i, c in enumerate(actual)):
        raise RuntimeError(f"Incorrect chunk placement for {namespace}")
    print(f"{namespace}: 12 chunks, {len(targets)} shard(s)", flush=True)


def init_cluster(client):
    require_router(client)
    existing = {s["_id"]: s["host"] for s in client.admin.command("listShards")["shards"]}
    if set(existing) - set(SHARDS):
        raise RuntimeError(f"Unexpected shards: {existing}")
    for host, name in SHARDS.items():
        address = f"{name}/{host}:27017"
        if host in existing:
            if existing[host] != address:
                raise RuntimeError(f"Unexpected address for {host}: {existing[host]}")
        else:
            client.admin.command("addShard", address, name=host)
            print(f"Added {host}", flush=True)
    with paused_balancer(client):
        prepare_collection(client, DB_NAME, "car_models", list(SHARDS))


def make_documents(count):
    generator = CarGenerator()
    docs = []
    for _ in range(count):
        bundle = generator.generate()
        doc = _to_doc(bundle.car_model, "model_id")
        doc["engineer_ids"] = [str(e.engineer_id) for e in bundle.engineers]
        doc["technology_ids"] = [str(t.tech_id) for t in bundle.technologies]
        doc["review"] = _to_doc(bundle.review, "review_id")
        doc["review"].pop("_id")
        docs.append(doc)
    return docs


def shard_counts(col):
    return {row["shard"]: row["count"] for row in col.aggregate([{"$collStats": {"count": {}}}])}


def write_batches(col, docs, batch_size, workers):
    batches = [docs[i:i + batch_size] for i in range(0, len(docs), batch_size)]
    def insert(batch):
        return len(col.insert_many(batch, ordered=False).inserted_ids)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        start = time.perf_counter()
        written = sum(pool.map(insert, batches))
        elapsed = time.perf_counter() - start
    if written != len(docs) or col.count_documents({}) != len(docs):
        raise RuntimeError("Document count mismatch")
    return elapsed


def benchmark(client, count, batch_size, workers, rounds):
    require_router(client)
    if {s["_id"] for s in client.admin.command("listShards")["shards"]} != set(SHARDS):
        raise RuntimeError("Initialize the three-shard cluster first")
    print(f"Preparing {count} identical documents for both modes", flush=True)
    docs = make_documents(count)
    db = client[BENCH_DB]
    modes = {"one_shard": ["shard1"], "three_shards": list(SHARDS)}
    rows = []
    with paused_balancer(client):
        try:
            for mode, targets in modes.items():
                db[mode].drop()
                prepare_collection(client, BENCH_DB, mode, targets)
            for mode in modes:
                col = db[mode].with_options(write_concern=WriteConcern(w="majority", j=True))
                write_batches(col, docs[:min(count, 1000)], batch_size, workers)
                col.delete_many({})
            for run in range(1, rounds + 1):
                order = list(modes) if run % 2 else list(reversed(modes))
                for mode in order:
                    col = db[mode].with_options(write_concern=WriteConcern(w="majority", j=True))
                    if col.count_documents({}):
                        raise RuntimeError("Benchmark collection must be empty")
                    elapsed = write_batches(col, docs, batch_size, workers)
                    counts = shard_counts(col)
                    nonempty = {s for s, n in counts.items() if n > 0}
                    if nonempty != set(modes[mode]) or sum(counts.values()) != count:
                        raise RuntimeError(f"Unexpected physical distribution: {counts}")
                    row = {"run": run, "mode": mode, "documents": count, "seconds": round(elapsed, 6),
                           "docs_per_second": round(count / elapsed, 2), "batch_size": batch_size,
                           "workers": workers, **{s: counts.get(s, 0) for s in SHARDS}}
                    rows.append(row)
                    print(row, flush=True)
                    col.delete_many({})
        finally:
            for mode in modes:
                db[mode].drop()
    path = Path("logs/sharding_benchmark.csv")
    path.parent.mkdir(exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    medians = {mode: statistics.median(r["docs_per_second"] for r in rows if r["mode"] == mode) for mode in modes}
    print(f"Median: {medians}")
    print(f"Speedup: {medians['three_shards'] / medians['one_shard']:.3f}x")
    print(f"CSV: {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["init-replicas", "init-cluster", "benchmark"])
    parser.add_argument("--count", type=int, default=15000)
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--rounds", type=int, default=3)
    args = parser.parse_args()
    if not (1000 <= args.count <= 100000 and 1 <= args.batch_size <= 5000 and 1 <= args.workers <= 16 and 1 <= args.rounds <= 10):
        parser.error("count 1000..100000, batch-size 1..5000, workers 1..16, rounds 1..10")
    if args.action == "init-replicas":
        init_replicas()
        return
    with MongoClient(DSN, serverSelectionTimeoutMS=10000) as client:
        if args.action == "init-cluster":
            init_cluster(client)
        else:
            benchmark(client, args.count, args.batch_size, args.workers, args.rounds)


if __name__ == "__main__":
    main()