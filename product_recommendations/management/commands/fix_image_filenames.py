from django.core.management.base import BaseCommand
from product_recommendations.models import Product

class Command(BaseCommand):
    help = "Fix mismatched image file names for products (e.g., brightlite -> brightlight)"

    def handle(self, *args, **kwargs):
        fixes = [
            ("/media/products/brightlight_lamp.png", "/media/products/brightlite_lamp.png"),
        ]

        total_changed = 0
        for old, new in fixes:
            products = Product.objects.filter(image_url=old)
            count = products.update(image_url=new)
            if count:
                self.stdout.write(self.style.SUCCESS(f"Updated {count} product(s): {old} -> {new}"))
            total_changed += count

        if total_changed == 0:
            self.stdout.write("No product image URLs required updating.")
        else:
            self.stdout.write(self.style.SUCCESS(f"Total updated: {total_changed}"))
