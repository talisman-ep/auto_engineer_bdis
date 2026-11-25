from dataclasses import dataclass, field
from uuid import UUID

from backend.domain.entities import (
    CarModel,
    Engineer,
    Manufacturer,
    Review,
    Technology,
)


@dataclass
class IngestCarBundleDTO:
    manufacturer: Manufacturer
    car_model: CarModel
    engineers: list[Engineer]
    technologies: list[Technology]
    review: Review


@dataclass
class CarFilterDTO:
    body_type: str | None = None
    fuel_type: str | None = None
    release_year: int | None = None
    limit: int = 20
    offset: int = 0


@dataclass
class CarCardDTO:
    model_id: UUID
    brand_name: str
    model_name: str
    body_type: str
    fuel_type: str
    release_year: int
    horsepower: int
    acceleration_0_100: float
    drivetrain: str
    video_review_url: str
    engineers: list[str] = field(default_factory=list)
    technologies: list[str] = field(default_factory=list)


@dataclass
class ReviewSearchResultDTO:
    review_id: UUID
    model_id: UUID
    title: str
    snippet: str
    rating: float
    score: float = 0.0


@dataclass
class SearchResponseDTO:
    raw_query: str
    normalized_query: str
    source: str  # "cache" або "elasticsearch"
    items: list[ReviewSearchResultDTO] = field(default_factory=list)


@dataclass
class EngineerPortfolioDTO:
    engineer: Engineer
    models: list[CarModel] = field(default_factory=list)


@dataclass
class GeneratorRateDTO:
    target_rps: int