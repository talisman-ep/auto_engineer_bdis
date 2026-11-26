import argparse
import asyncio
import logging
import os
import random
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from backend.application.dtos import IngestCarBundleDTO
from backend.domain.entities import CarModel, Engineer, Manufacturer, Review, Technology

from backend.model_profiles import BRANDS, BODY_TYPES, FUEL_TYPES, MODEL_PROFILES, ModelProfile

FIRST_NAMES = ["Олександр", "Андрій", "Максим", "Іван", "Дмитро", "Анна", "Марія", "Олена", "Софія", "Ірина"]
LAST_NAMES = ["Коваленко", "Шевченко", "Бондар", "Мельник", "Кравченко", "Ткаченко", "Лисенко", "Савчук", "Бойко", "Поліщук", "Мороз", "Олійник"]
ROLES = ["Головний інженер", "Шеф-дизайнер", "Інженер шасі", "Інженер двигунів", "Інженер електроніки"]
TECH_GROUPS = {
    "Двигуни": {
        "Турбонаддув": "Подає стиснене повітря в циліндри для збільшення потужності двигуна.",
        "Пряме впорскування": "Подає паливо безпосередньо в камеру згоряння.",
        "Змінні фази газорозподілу": "Регулює моменти відкриття клапанів залежно від режиму двигуна.",
        "Рекуперація енергії": "Перетворює частину кінетичної енергії на електричну під час уповільнення.",
        "Гібридний привід": "Поєднує двигун внутрішнього згоряння та електродвигун.",
        "Електродвигун": "Перетворює електричну енергію на обертання приводного вала.",
    },
    "Автопілот": {
        "Адаптивний круїз-контроль": "Регулює швидкість для підтримання дистанції до транспорту попереду.",
        "Утримання смуги": "Допомагає коригувати траєкторію в межах смуги руху.",
        "Автоматичне гальмування": "Ініціює гальмування при виявленні загрози зіткнення.",
        "Розпізнавання знаків": "Визначає дорожні знаки за зображеннями з камери.",
        "Контроль сліпих зон": "Попереджає про транспорт у зонах обмеженої видимості.",
        "Паркувальний асистент": "Допомагає маневрувати під час паркування за даними датчиків.",
    },
    "Аеродинаміка": {
        "Активний спойлер": "Змінює положення для регулювання аеродинамічних сил.",
        "Дифузор": "Керує потоком повітря під задньою частиною кузова.",
        "Активні жалюзі": "Регулюють потік повітря до системи охолодження.",
        "Плоске днище": "Зменшує нерівномірність повітряного потоку під автомобілем.",
        "Аеродинамічний обвіс": "Змінює обтікання кузова для керування опором і притискною силою.",
        "Повітряні канали": "Спрямовують потоки повітря до компонентів автомобіля.",
    },
    "Шасі": {
        "Адаптивна підвіска": "Змінює характеристики амортизаторів відповідно до умов руху.",
        "Керамічні гальма": "Використовують композитні диски зі стійкістю до високих температур.",
        "Повний привід": "Передає крутний момент на обидві осі автомобіля.",
        "Електронний диференціал": "Керує розподілом тяги між колесами за допомогою електроніки.",
        "Активне кермування": "Регулює реакцію кермового механізму залежно від швидкості.",
        "Пневматична підвіска": "Використовує пневматичні пружини для регулювання висоти кузова.",
    },
    "Батарейні системи": {
        "Літій-іонна батарея": "Накопичує електричну енергію в літій-іонних комірках.",
        "Швидке заряджання": "Забезпечує заряджання тягової батареї за підвищеної потужності.",
        "Термоконтроль батареї": "Підтримує робочу температуру акумуляторних комірок.",
        "Система BMS": "Контролює напругу, температуру та стан заряду батареї.",
        "Балансування комірок": "Вирівнює рівні заряду окремих комірок батареї.",
        "Рекуперативне гальмування": "Використовує електродвигун як генератор під час гальмування.",
    },
}
COUNTRIES = ["Україна", "Німеччина", "Японія", "США", "Італія", "Франція", "Швеція"]
KEYWORDS = ["динаміка", "керованість", "аеродинаміка", "стійкість", "комфорт",
            "безпека", "ефективність", "підвіска", "гальмування", "маневреність",
            "ергономіка", "шумоізоляція", "надійність", "прискорення", "зчеплення",
            "охолодження", "модернізація", "збалансованість", "витривалість", "інновації"]
REVIEW_TYPES = ["Тест-драйв", "Технічний огляд", "Огляд інновацій", "Аналіз характеристик"]


def stable_id(kind: str, name: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"auto-engineers/{kind}/{name}")


class CarGenerator:
    def __init__(self) -> None:
        self.brands = [Manufacturer(stable_id("manufacturer", name), name, country, year, segment)
                       for name, country, year, segment in BRANDS]
        self.brand_by_name = {brand.brand_name: brand for brand in self.brands}
        current_year = datetime.now(timezone.utc).year
        self.profiles_by_fuel = {
            fuel: tuple(p for p in MODEL_PROFILES if p.fuel == fuel and p.first_year <= current_year)
            for fuel in FUEL_TYPES
        }
        self.engineers_by_year = {}
        rng = random.Random(13)
        self.engineers = []
        for first in FIRST_NAMES:
            for last in LAST_NAMES:
                name = f"{first} {last}"
                role = rng.choice(ROLES)
                country = rng.choice(COUNTRIES)
                year = rng.randint(1980, 2018)
                bio = rng.choice([
                    f"Країна походження — {country}. Початок кар'єри — {year} рік. Спеціалізація: {role.lower()}.",
                    f"Спеціалізація: {role.lower()}. Професійна діяльність з {year} року, країна походження — {country}.",
                    f"З {year} року працює в автомобільній галузі. Напрям роботи: {role.lower()}. Країна походження — {country}.",
                ])
                self.engineers.append(Engineer(stable_id("engineer", name), name, role, country, year, bio))
        self.technologies = [Technology(stable_id("tech", name), name, category, description)
                             for category, entries in TECH_GROUPS.items()
                             for name, description in entries.items()]

    def _technologies_for(self, car: CarModel, profile: ModelProfile) -> list[Technology]:
        fuel = car.fuel_type
        year = car.release_year
        required = set()
        if profile.turbo:
            required.add("Турбонаддув")
        if fuel == "Електро":
            required.add("Електродвигун")
        if fuel == "Гібрид":
            required.add("Гібридний привід")
        if car.drivetrain == "Повний":
            required.add("Повний привід")

        modern_from = {
            "Адаптивний круїз-контроль": 2005,
            "Утримання смуги": 2010,
            "Автоматичне гальмування": 2010,
            "Розпізнавання знаків": 2012,
            "Контроль сліпих зон": 2008,
            "Паркувальний асистент": 2008,
            "Активний спойлер": 2000,
            "Керамічні гальма": 2002,
            "Активні жалюзі": 2010,
            "Швидке заряджання": 2015,
            "Термоконтроль батареї": 2010,
            "Літій-іонна батарея": 2010,
        }
        combustion = {"Турбонаддув", "Пряме впорскування", "Змінні фази газорозподілу"}
        electric = {"Електродвигун", "Рекуперація енергії"}
        sporty = car.body_type in {"Купе", "Родстер"} and car.horsepower >= 300
        allowed = []
        for tech in self.technologies:
            name = tech.tech_name
            if year < modern_from.get(name, 1995):
                continue
            if name == "Турбонаддув" and not profile.turbo:
                continue
            if name == "Повний привід" and car.drivetrain != "Повний":
                continue
            if fuel == "Електро" and (name in combustion or name == "Гібридний привід"):
                continue
            if fuel in {"Бензин", "Дизель"} and (name in electric or name == "Гібридний привід" or tech.category == "Батарейні системи"):
                continue
            if fuel == "Гібрид" and name == "Швидке заряджання":
                continue
            if fuel == "Дизель" and name == "Змінні фази газорозподілу":
                continue
            if name in {"Активний спойлер", "Керамічні гальма", "Аеродинамічний обвіс"} and not sporty:
                continue
            if name == "Пневматична підвіска" and (car.body_type != "Кросовер" or self.brand_by_name[profile.brand].segment == "масовий"):
                continue
            if year < 2000 and tech.category == "Автопілот":
                continue
            allowed.append(tech)
        selected = [tech for tech in allowed if tech.tech_name in required]
        optional = [tech for tech in allowed if tech.tech_name not in required]
        target = random.randint(max(2, len(selected)), 4)
        return selected + random.sample(optional, min(len(optional), target - len(selected)))

    def _review(self, brand: Manufacturer, car: CarModel,
                engineers: list[Engineer], technologies: list[Technology]) -> Review:
        label = f"{brand.brand_name} {car.model_name}"
        review_type = random.choice(REVIEW_TYPES)
        keywords = random.sample(KEYWORDS, random.randint(6, 10))
        names = ", ".join(e.full_name for e in engineers)
        intro = random.choice([
            f"У цьому синтетичному огляді розглянуто модель {label} ({car.release_year}).",
            f"Предмет синтетичного тест-драйву — {label}, {car.release_year} року випуску.",
        ])
        dynamics = random.choice([
            f"Потужність становить {car.horsepower} к.с., розгін до 100 км/год — {car.acceleration_0_100} с.",
            f"Для моделі задано {car.horsepower} к.с. і час розгону до 100 км/год {car.acceleration_0_100} с.",
        ])
        tech_text = " ".join(f"{t.tech_name}: {t.description}" for t in technologies)
        content = (f"{intro} Тип кузова: {car.body_type}. Паливо: {car.fuel_type}. "
                   f"Конструктори: {names}.\n\n{dynamics} Привід: {car.drivetrain}.\n\n"
                   f"Технології синтетичної конфігурації: {tech_text}\n\n"
                   f"Підсумок. Критерії оцінювання: {', '.join(keywords)}.")
        now = datetime.now(timezone.utc).replace(microsecond=0)
        start = datetime(car.release_year, 1, 1, tzinfo=timezone.utc)
        published = start + timedelta(seconds=random.randint(0, int((now - start).total_seconds())))
        return Review(uuid4(), car.model_id, f"{review_type}: {label} ({car.release_year})",
                      content, published, round(min(10.0, max(5.0, random.gauss(8.0, 1.0))), 1))

    def generate(self, profile: ModelProfile | None = None) -> IngestCarBundleDTO:
        # Preserve the four fuel categories used by the sharding benchmark.
        if profile is None:
            fuel = random.choice(FUEL_TYPES)
            profile = random.choice(self.profiles_by_fuel[fuel])
        brand = self.brand_by_name[profile.brand]
        year = random.randint(profile.first_year, min(profile.last_year, datetime.now(timezone.utc).year))
        power = random.randint(profile.min_hp, profile.max_hp)
        span = profile.max_hp - profile.min_hp
        fraction = (power - profile.min_hp) / span if span else 0.5
        acc = profile.max_acc - fraction * (profile.max_acc - profile.min_acc)
        acc += random.uniform(-0.15, 0.15)
        acc = round(max(profile.min_acc, min(profile.max_acc, acc)), 1)
        name = profile.name
        car = CarModel(
            model_id=uuid4(), manufacturer_id=brand.manufacturer_id,
            model_name=name, body_type=profile.body, fuel_type=profile.fuel, release_year=year,
            horsepower=power, acceleration_0_100=acc,
            drivetrain=profile.drive,
            video_review_url="https://www.youtube.com/results?" + urlencode({"search_query": f"{brand.brand_name} {name} review"}),
        )
        if year not in self.engineers_by_year:
            self.engineers_by_year[year] = [e for e in self.engineers if e.career_start_year <= year]
        engineers = random.sample(self.engineers_by_year[year], random.randint(1, 2))
        technologies = self._technologies_for(car, profile)
        return IngestCarBundleDTO(brand, car, engineers, technologies,
                                  self._review(brand, car, engineers, technologies))


async def run(count: int, rate: int) -> None:
    from backend.infrastructure.mongo_adapter import MongoCarAdapter

    repo = MongoCarAdapter(os.getenv("MONGO_DSN", "mongodb://localhost:27017"))
    from backend.infrastructure.es_adapter import ElasticsearchReviewAdapter

    es_url = os.getenv("ES_URL")
    es = ElasticsearchReviewAdapter(es_url) if es_url else None
    generator = CarGenerator()
    logger = logging.getLogger("generator")
    saved = 0
    try:
        await repo.ensure_indexes()
        if es is not None:
            await es.ensure_index()
        for manufacturer in generator.brands:
            await repo.upsert_manufacturer(manufacturer)
        for engineer in generator.engineers:
            await repo.upsert_engineer(engineer)
        for tech in generator.technologies:
            await repo.upsert_technology(tech)

        started = last_report = time.monotonic()
        batch_size = max(1, rate // 10)
        while count == 0 or saved < count:
            tick = time.monotonic()
            size = batch_size if count == 0 else min(batch_size, count - saved)
            bundles = [generator.generate() for _ in range(size)]
            await repo.create_bundles(bundles)
            saved += size
            if es is not None:
                try:
                    await es.index_many([bundle.review for bundle in bundles])
                except Exception:
                    logger.exception("Reviews remain in MongoDB; rerun backend.index_reviews to recover the index")
                    raise
            now = time.monotonic()
            if now - last_report >= 1:
                logger.info("Saved %d bundles, average %.1f bundles/s", saved, saved / max(now - started, 0.001))
                last_report = now
            await asyncio.sleep(max(0, size / rate - (time.monotonic() - tick)))
        if es is not None:
            await es.refresh()
    finally:
        logger.info("Finished: %d bundles in confirmed batches", saved)
        repo.close()
        if es is not None:
            await es.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=100, help="0 = continuous")
    parser.add_argument("--rate", type=int, default=10)
    args = parser.parse_args()
    if args.count < 0 or not 10 <= args.rate <= 5000:
        parser.error("count >= 0, rate between 10 and 5000 required")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    try:
        asyncio.run(run(args.count, args.rate))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()