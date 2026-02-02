from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from product_recommendations.models import (
    UserProfile,
    Category,
    Product,
    UserInteraction,
    Recommendation
)
import random


class Command(BaseCommand):
    help = "Seed initial data for product recommendation system"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("🌱 Seeding data started..."))

        # -----------------------------
        # 1. Create Categories
        # -----------------------------
        categories = ['Electronics', 'Books', 'Fashion', 'Home', 'Sports']
        category_objs = []

        for name in categories:
            category, _ = Category.objects.get_or_create(name=name)
            category_objs.append(category)

        # -----------------------------
        # 2. Create Products
        # -----------------------------
        products_data = [
            ("Electronics 1", "Electronics", 1500,"Smartphone with 6GB RAM"),
            ("Electronics 2", "Electronics", 900,"Laptop with 8GB RAM"),
            ("Sports 1", "Sports", 120,"Running Shoes Size 10"),
            ("Home 1", "Home", 250,"Office Chair Ergonomic"),
            ("Book 1", "Books", 40,"Cookbook for Beginners"),
            ("Fashion 1", "Fashion", 30,"T-Shirt Size M"),
            ("Electronics 3", "Electronics", 180,"Headphones Noise Cancelling"),
            ("Sports 2", "Sports", 50,"Yoga Mat 6mm Thick"),
            ("Home 2", "Home", 60,"Desk Lamp LED"),
            ("Book 2", "Books", 25,"Novel Bestseller 2025"),
        ]

        product_objs = []

        for name, category_name, price, description in products_data:
            category = Category.objects.get(name=category_name)
            product, _ = Product.objects.get_or_create(
                name=name,
                category=category,
                price=price,
                description=description,
                stock=50,
                is_active=True
            )
            product_objs.append(product)

        # -----------------------------
        # 3. Create Users (10 users)
        # -----------------------------
        for i in range(1, 11):
            username = f"user{i}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": f"user{i}@example.com"}
            )

            if created:
                user.set_password("password123")
                user.save()

            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    "age": random.randint(18, 50),
                    "gender": random.choice(["Male", "Female"]),
                    "location": random.choice(["Singapore", "Malaysia", "UK"])
                }
            )

        users = User.objects.filter(username__startswith="user")

        # -----------------------------
        # 4. Create User Interactions
        # -----------------------------
        interaction_types = ['view', 'click', 'add_to_cart', 'purchase', 'like']

        for user in users:
            for _ in range(5):  # 5 interactions per user
                UserInteraction.objects.create(
                    user=user,
                    product=random.choice(product_objs),
                    interaction_type=random.choice(interaction_types)
                )

        # -----------------------------
        # 5. Simulated Recommendations
        # -----------------------------
        for user in users:
            sampled_products = random.sample(product_objs, 3)
            for product in sampled_products:
                Recommendation.objects.get_or_create(
                    user=user,
                    product=product,
                    defaults={
                        "score": round(random.uniform(0.6, 0.95), 2),
                        "generated_by": "Gemini AI (Simulated)"
                    }
                )

        self.stdout.write(self.style.SUCCESS("✅ Seeding completed successfully!"))
