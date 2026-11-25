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

BRANDS = [
    ("Toyota", "Японія", 1937, "масовий", "Corolla"),
    ("Honda", "Японія", 1948, "масовий", "Civic"),
    ("Mazda", "Японія", 1920, "масовий", "CX"),
    ("Nissan", "Японія", 1933, "масовий", "Qashqai"),
    ("Subaru", "Японія", 1953, "масовий", "Impreza"),
    ("Hyundai", "Південна Корея", 1967, "масовий", "IONIQ"),
    ("Kia", "Південна Корея", 1944, "масовий", "Sportage"),
    ("Ford", "США", 1903, "масовий", "Focus"),
    ("Chevrolet", "США", 1911, "масовий", "Malibu"),
    ("Volkswagen", "Німеччина", 1937, "масовий", "Golf"),
    ("Skoda", "Чехія", 1895, "масовий", "Octavia"),
    ("Renault", "Франція", 1899, "масовий", "Megane"),
    ("Peugeot", "Франція", 1810, "масовий", "3008"),
    ("Fiat", "Італія", 1899, "масовий", "Tipo"),
    ("BMW", "Німеччина", 1916, "преміум", "Series"),
    ("Mercedes-Benz", "Німеччина", 1926, "преміум", "Class"),
    ("Audi", "Німеччина", 1909, "преміум", "A"),
    ("Volvo", "Швеція", 1927, "преміум", "XC"),
    ("Lexus", "Японія", 1989, "преміум", "RX"),
    ("Jaguar", "Велика Британія", 1922, "преміум", "F-Type"),
    ("Porsche", "Німеччина", 1931, "спорткари", "911"),
    ("Ferrari", "Італія", 1947, "спорткари", "GT"),
    ("Lamborghini", "Італія", 1963, "спорткари", "Huracan"),
    ("McLaren", "Велика Британія", 1963, "гіперкари", "GT"),
    ("Koenigsegg", "Швеція", 1994, "гіперкари", "Jesko"),
]
BODY_TYPES = ["Седан", "Купе", "Кросовер", "Хетчбек", "Універсал", "Родстер"]
FUEL_TYPES = ["Бензин", "Дизель", "Гібрид", "Електро"]
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
POWER_RANGES = {"масовий": (120, 300), "преміум": (180, 600),
                "спорткари": (350, 800), "гіперкари": (650, 1100)}
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
                       for name, country, year, segment, _ in BRANDS]
        self.prefixes = {row[0]: row[4] for row in BRANDS}
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

    @staticmethod
    def _drivetrain(body: str, power: int) -> str:
        if power >= 500:
            weights = (0, 45, 55)
        elif body == "Кросовер":
            weights = (20, 10, 70)
        elif body in {"Купе", "Родстер"}:
            weights = (10, 65, 25)
        else:
            weights = (65, 20, 15)
        return random.choices(["Передній", "Задній", "Повний"], weights=weights, k=1)[0]

    def _technologies_for(self, car: CarModel) -> list[Technology]:
        combustion = {"Турбонаддув", "Пряме впорскування", "Змінні фази газорозподілу"}
        electric = {"Електродвигун", "Рекуперація енергії"}
        allowed = []
        for tech in self.technologies:
            name = tech.tech_name
            fuel = car.fuel_type
            if name == "Повний привід" and car.drivetrain != "Повний":
                continue
            if fuel == "Електро" and (name in combustion or name == "Гібридний привід"):
                continue
            if fuel in {"Бензин", "Дизель"} and (name in electric or name == "Гібридний привід" or tech.category == "Батарейні системи"):
                continue
            if fuel == "Гібрид" and name == "Швидке заряджання":
                continue
            allowed.append(tech)
        return random.sample(allowed, random.randint(2, 4))

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
                   f"Технології моделі: {tech_text}\n\n"
                   f"Підсумок. Критерії оцінювання: {', '.join(keywords)}.")
        now = datetime.now(timezone.utc).replace(microsecond=0)
        start = datetime(car.release_year, 1, 1, tzinfo=timezone.utc)
        published = start + timedelta(seconds=random.randint(0, int((now - start).total_seconds())))
        return Review(uuid4(), car.model_id, f"{review_type}: {label} ({car.release_year})",
                      content, published, round(min(10.0, max(5.0, random.gauss(8.0, 1.0))), 1))

    def generate(self) -> IngestCarBundleDTO:
        brand = random.choice(self.brands)
        fuel = random.choice(FUEL_TYPES)
        body = random.choice(BODY_TYPES)
        low, high = POWER_RANGES[brand.segment]
        power = random.randrange(low, high + 1, 10)
        name = f"{self.prefixes[brand.brand_name]} {random.randint(1, 99)} {random.choice(['Base', 'Sport', 'GT'])}"
        year = random.randint(1995, min(2026, datetime.now(timezone.utc).year))
        car = CarModel(
            model_id=uuid4(), manufacturer_id=brand.manufacturer_id,
            model_name=name, body_type=body, fuel_type=fuel, release_year=year,
            horsepower=power,
            acceleration_0_100=round(max(2.0, 14 - power / 85 + random.uniform(-0.4, 0.4)), 1),
            drivetrain=self._drivetrain(body, power),
            video_review_url="https://www.youtube.com/results?" + urlencode({"search_query": f"{brand.brand_name} {name} review"}),
        )
        engineers = random.sample([e for e in self.engineers if e.career_start_year <= year], random.randint(1, 2))
        technologies = self._technologies_for(car)
        return IngestCarBundleDTO(brand, car, engineers, technologies,
                                  self._review(brand, car, engineers, technologies))


async def run(count: int, rate: int) -> None:
    from backend.infrastructure.mongo_adapter import MongoCarAdapter

    repo = MongoCarAdapter(os.getenv("MONGO_DSN", "mongodb://localhost:27017"))
    generator = CarGenerator()
    logger = logging.getLogger("generator")
    saved = 0
    try:
        await repo.ensure_indexes()
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
            now = time.monotonic()
            if now - last_report >= 1:
                logger.info("Saved %d bundles, average %.1f bundles/s", saved, saved / max(now - started, 0.001))
                last_report = now
            await asyncio.sleep(max(0, size / rate - (time.monotonic() - tick)))
    finally:
        logger.info("Finished: %d bundles in confirmed batches", saved)
        repo.close()


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