from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Manufacturer:
    manufacturer_id: UUID
    brand_name: str
    country: str
    founded_year: int
    segment: str


@dataclass
class CarModel:
    model_id: UUID
    manufacturer_id: UUID
    model_name: str
    body_type: str
    fuel_type: str
    release_year: int
    horsepower: int
    acceleration_0_100: float
    drivetrain: str
    video_review_url: str


@dataclass
class Engineer:
    engineer_id: UUID
    full_name: str
    role: str
    nationality: str
    career_start_year: int
    bio: str


@dataclass
class Technology:
    tech_id: UUID
    tech_name: str
    category: str
    description: str


@dataclass
class Review:
    review_id: UUID
    model_id: UUID
    title: str
    content: str
    published_at: datetime
    rating: float