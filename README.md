# Автомобілі та Інженери

Курсова робота з дисципліни «Бази даних та інформаційні системи» (КПІ, ФПМ).
Варіант 13 — «Автомобілі та Інженери (Конструктори)».

Команда:
- Пилипчук Євгеній (КМ-43)
- Кваченко Дмитро (КМ-43)
- Нагнойний Єгор (КМ-42)

## Технології

- Python, FastAPI, asyncio
- MongoDB — основне сховище з шардуванням на 3 вузли
- Elasticsearch — повнотекстовий та нечіткий пошук оглядів
- Neo4j — графові зв'язки та рекомендації (заплановано)
- Redis — кешування запитів (заплановано)
- Docker Compose — розгортання системи

Архітектура: Layered Architecture, Hexagonal Architecture, CQRS, Polyglot Persistence.

## Реалізований функціонал

- Генерація синтетичних даних на основі 132 профілів моделей від 42 виробників.
- Каталог автомобілів, фільтрація та перегляд характеристик.
- Шардування MongoDB та порівняльне тестування швидкості запису.
- Розподілена агрегація через Aggregation Pipeline.
- Повнотекстовий пошук, Fuzzy Search та нормалізація запитів.
- Модульні та інтеграційні тести.

## Запуск

```bash
docker compose up -d --build --wait
```

Вебінтерфейс: http://localhost:8000

Swagger UI: http://localhost:8000/docs

## Генерація даних

```bash
docker compose run --rm --no-deps backend python -m backend.generator --count 1000 --rate 100
```

## Тестування

```bash
docker compose run --rm --no-deps backend python -m unittest discover -s tests -v
```