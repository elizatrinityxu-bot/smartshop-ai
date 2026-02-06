from django.test import TestCase
from product_recommendations.services.smart_search_service import smart_search_products
from product_recommendations.models import Category, Product


class SmartSearchTests(TestCase):
    def setUp(self):
        cat_shoes = Category.objects.create(name="Shoes")
        cat_beauty = Category.objects.create(name="Beauty & Personal Care")

        Product.objects.create(
            name="FlexRun Lightweight Running Shoes",
            category=cat_shoes,
            price=89.99,
            base_description="Lightweight running shoes ideal for jogging and gym",
            description="Comfortable running shoes",
            stock=10,
            is_active=True,
            brand="FlexRun"
        )

        Product.objects.create(
            name="SunGuard SPF50 Sunscreen",
            category=cat_beauty,
            price=15.99,
            base_description="Sunscreen for sensitive skin",
            description="Protects skin from UV",
            stock=20,
            is_active=True,
            brand="SunGuard"
        )

        Product.objects.create(
            name="RoboClean Compact Vacuum",
            category=Category.objects.create(name="Home & Living"),
            price=249.00,
            base_description="Robotic vacuum for home cleaning",
            description="Smart vacuum",
            stock=5,
            is_active=True,
            brand="RoboClean"
        )

    def test_recommend_shoes_filters(self):
        res, meta = smart_search_products("recommend shoes", return_metadata=True)
        self.assertTrue(meta['applied_filters']['keywords_used'])
        # Either keywords were extracted or category was mapped
        has_shoes = 'shoes' in [kw.lower() for kw in meta['parsed']['keywords']] or meta['parsed']['mapped_category']
        self.assertTrue(has_shoes)
        names = [p.name for p in res]
        self.assertIn("FlexRun Lightweight Running Shoes", names)
        # ensure the results are filtered (not returning the full dataset)
        self.assertLess(len(names), 3)

    def test_recommend_sunscreen_filters(self):
        res, meta = smart_search_products("recommend sunscreen", return_metadata=True)
        self.assertTrue(meta['applied_filters']['keywords_used'])
        has_sunscreen = 'sunscreen' in [kw.lower() for kw in meta['parsed']['keywords']] or meta['parsed']['mapped_category']
        self.assertTrue(has_sunscreen)
        names = [p.name for p in res]
        self.assertIn("SunGuard SPF50 Sunscreen", names)
        self.assertLess(len(names), 3)

    def test_i_need_shoes(self):
        res, meta = smart_search_products("i need shoes", return_metadata=True)
        self.assertTrue(meta['applied_filters']['keywords_used'])
        has_shoes = 'shoes' in [kw.lower() for kw in meta['parsed']['keywords']] or meta['parsed']['mapped_category']
        self.assertTrue(has_shoes)
        names = [p.name for p in res]
        self.assertIn("FlexRun Lightweight Running Shoes", names)

