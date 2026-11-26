import logging
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from pymongo.errors import PyMongoError

from backend.application.dtos import CarFilterDTO
from backend.main import bootstrap, setup_logging

logger = logging.getLogger('auto_engineers.api')


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    container = bootstrap()
    app.state.container = container
    try:
        yield
    finally:
        container.mongo_adapter.close()


app = FastAPI(title='Auto Engineers', lifespan=lifespan)


@app.get('/', include_in_schema=False)
async def index():
    return FileResponse(Path(__file__).with_name('index.html'))


@app.get('/api/cars')
async def list_cars(
    request: Request,
    body_type: str | None = None,
    fuel_type: str | None = None,
    release_year: int | None = Query(None, ge=1995, le=2026),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    filters = CarFilterDTO(
        body_type=body_type, fuel_type=fuel_type, release_year=release_year,
        limit=limit, offset=offset,
    )
    try:
        cars = await request.app.state.container.car_controller.list_cars(filters)
    except PyMongoError as exc:
        logger.exception('MongoDB catalog read failed')
        raise HTTPException(503, 'MongoDB недоступна') from exc
    logger.info('Catalog: %s, returned=%d', filters, len(cars))
    return cars


@app.get('/api/cars/{model_id}')
async def get_car(request: Request, model_id: UUID):
    try:
        car = await request.app.state.container.car_controller.get_car(model_id)
    except PyMongoError as exc:
        logger.exception('MongoDB car read failed')
        raise HTTPException(503, 'MongoDB недоступна') from exc
    if car is None:
        raise HTTPException(404, 'Автомобіль не знайдено')
    logger.info('Car found: %s', model_id)
    return car


@app.get('/api/analytics/fuel-stats')
async def get_fuel_stats(request: Request):
    try:
        items = await request.app.state.container.car_controller.get_fuel_stats()
    except PyMongoError as exc:
        logger.exception('MongoDB aggregation failed')
        raise HTTPException(503, 'MongoDB недоступна') from exc

    logger.info('Cross-shard aggregation returned %d rows', len(items))
    return {
        'query': 'fuel_stats_by_type',
        'engine': 'mongodb_aggregation_pipeline',
        'collection': 'auto_engineers.car_models',
        'items': [asdict(item) for item in items],
    }