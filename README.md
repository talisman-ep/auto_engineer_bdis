# Автомобілі та Інженери

Курсова робота з дисципліни «Бази даних та інформаційні системи» (КПІ, ФПМ).  
Варіант 13 — «Автомобілі та Інженери (Конструктори)».

**Команда:**
- Пилипчук Євгеній (КМ-43)
- Кваченко Дмитро (КМ-43)
- Нагнойний Єгор (КМ-42)

## Стек і сховища

Бекенд на Python (FastAPI + asyncio) з Polyglot Persistence:
- **MongoDB** (3 shards) — основні дані (`car_models`, `manufacturers`, `engineers`, `technologies`) та фільтрація.
- **Elasticsearch** — full-text search по технічних оглядах (`car_reviews`).
- **Neo4j** — граф зв'язків (`СПРОЄКТУВАВ`, `ВИПУЩЕНА`, `ВИКОРИСТОВУЄ`) та рекомендації.
- **Redis** — кеш для нормалізованих пошукових запитів і лічильники.

## Архітектура

Використано Layered + Hexagonal Architecture (Ports & Adapters) і поділ на Write/Read (CQRS).

Ланцюжок викликів:
`Controllers -> CarFacade -> Services -> Ports (CrudRepository) <- Adapters`

Структура проєкту:
```text
backend/
├── main.py              # bootstrap / збірка залежностей (DI)
├── domain/
│   ├── entities.py      # CarModel, Manufacturer, Engineer, Technology, Review
│   └── normalizer.py    # нормалізація пошукових запитів
├── application/
│   ├── dtos.py          # DTO
│   ├── ports.py         # CrudRepository та порти сховищ
│   ├── services.py      # CarMetadataService, ReviewSearchService, CarGraphService
│   └── facade.py        # CarFacade
├── presentation/
│   └── controllers.py   # IngestController, CarController, SearchController
└── infrastructure/      # адаптери для MongoDB, Elasticsearch, Neo4j, Redis
tests/
└── test_structure.py    # перевірка збірки та заглушок
```

## Поточний стан

Зроблено базовий каркас і класи-заглушки. Адаптери в `infrastructure/` поки повертають `NotImplementedError` — підключення баз даних і генератора буде на наступних етапах.

## Запуск тестів

```bash
python -m unittest discover -s tests -v
```