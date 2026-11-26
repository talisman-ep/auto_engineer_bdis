import unittest
from collections import Counter
from datetime import datetime, timezone

from backend.generator import CarGenerator, FUEL_TYPES, stable_id
from backend.model_profiles import MODEL_PROFILES, BRANDS


class GeneratorTests(unittest.TestCase):
    def setUp(self):
        self.generator = CarGenerator()

    def test_catalog_integrity(self):
        self.assertEqual(len(BRANDS), len({brand[0] for brand in BRANDS}))
        self.assertEqual(len(MODEL_PROFILES), len({(p.brand, p.name) for p in MODEL_PROFILES}))
        self.assertEqual({p.brand for p in MODEL_PROFILES}, {b[0] for b in BRANDS})
        self.assertEqual({p.fuel for p in MODEL_PROFILES}, set(FUEL_TYPES))
        for p in MODEL_PROFILES:
            self.assertLessEqual(p.first_year, p.last_year)
            self.assertLessEqual(p.min_hp, p.max_hp)
            self.assertLessEqual(p.min_acc, p.max_acc)

    def check_bundle(self, bundle, profile):
        car = bundle.car_model
        self.assertEqual(bundle.manufacturer.brand_name, profile.brand)
        self.assertEqual(car.manufacturer_id, stable_id('manufacturer', profile.brand))
        self.assertEqual((car.model_name, car.body_type, car.fuel_type, car.drivetrain),
                         (profile.name, profile.body, profile.fuel, profile.drive))
        self.assertLessEqual(profile.first_year, car.release_year)
        self.assertLessEqual(car.release_year, min(profile.last_year, datetime.now(timezone.utc).year))
        self.assertLessEqual(profile.min_hp, car.horsepower)
        self.assertLessEqual(car.horsepower, profile.max_hp)
        self.assertLessEqual(profile.min_acc, car.acceleration_0_100)
        self.assertLessEqual(car.acceleration_0_100, profile.max_acc)
        self.assertTrue(all(e.career_start_year <= car.release_year for e in bundle.engineers))
        self.assertEqual(bundle.review.model_id, car.model_id)
        self.assertIn(f'{profile.brand} {profile.name}', bundle.review.title)
        self.assertGreaterEqual(bundle.review.published_at.year, car.release_year)
        self.assertLessEqual(bundle.review.published_at, datetime.now(timezone.utc))
        names = {t.tech_name for t in bundle.technologies}
        self.assertEqual(len(names), len(bundle.technologies))
        self.assertTrue(2 <= len(names) <= 4)
        self.assertEqual('Турбонаддув' in names, profile.turbo)
        self.assertEqual('Повний привід' in names, profile.drive == 'Повний')
        if profile.fuel == 'Електро':
            self.assertIn('Електродвигун', names)
            self.assertFalse(names & {'Турбонаддув', 'Пряме впорскування', 'Змінні фази газорозподілу', 'Гібридний привід'})
        if profile.fuel == 'Гібрид':
            self.assertIn('Гібридний привід', names)
            self.assertNotIn('Швидке заряджання', names)
        if profile.fuel in {'Бензин', 'Дизель'}:
            self.assertFalse(names & {'Електродвигун', 'Рекуперація енергії', 'Гібридний привід'})
            self.assertFalse(any(t.category == 'Батарейні системи' for t in bundle.technologies))

    def test_every_profile(self):
        for profile in MODEL_PROFILES:
            for _ in range(10):
                with self.subTest(profile=profile.name):
                    self.check_bundle(self.generator.generate(profile), profile)

    def test_random_population(self):
        lookup = {(p.brand, p.name): p for p in MODEL_PROFILES}
        ids = set()
        reviews = set()
        fuels = Counter()
        for _ in range(5000):
            bundle = self.generator.generate()
            car = bundle.car_model
            self.check_bundle(bundle, lookup[(bundle.manufacturer.brand_name, car.model_name)])
            ids.add(car.model_id)
            reviews.add(bundle.review.review_id)
            fuels[car.fuel_type] += 1
        self.assertEqual(len(ids), 5000)
        self.assertEqual(len(reviews), 5000)
        self.assertEqual(set(fuels), set(FUEL_TYPES))

    def test_jesko(self):
        for profile in MODEL_PROFILES:
            if profile.brand == 'Koenigsegg' and profile.name.startswith('Jesko'):
                car = self.generator.generate(profile).car_model
                self.assertEqual((car.body_type, car.fuel_type, car.drivetrain), ('Купе', 'Бензин', 'Задній'))
                self.assertEqual(car.horsepower, 1280)
                self.assertGreaterEqual(car.release_year, 2023)


if __name__ == '__main__':
    unittest.main()
