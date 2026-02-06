from django.core.management.base import BaseCommand
from product_recommendations.models import Product, Review
from django.db import transaction
from product_recommendations.services.review_summary_service import get_or_generate_review_summary
import random

class Command(BaseCommand):
    help = "Replace reviews for specific products with subtype-appropriate templates and regenerate their summaries"

    def add_arguments(self, parser):
        parser.add_argument('--ids', type=str, help='Comma-separated product ids to update')
        parser.add_argument('--names', type=str, help='Comma-separated product name substrings to match')

    def handle(self, *args, **kwargs):
        ids = kwargs.get('ids')
        names = kwargs.get('names')

        products = Product.objects.none()
        if ids:
            id_list = [int(i.strip()) for i in ids.split(',') if i.strip().isdigit()]
            products = Product.objects.filter(id__in=id_list)
        if names:
            for name in names.split(','):
                products = products | Product.objects.filter(name__icontains=name.strip())

        if not products.exists():
            self.stdout.write(self.style.ERROR('No matching products found.'))
            return

        subtype_templates = {
            'tote': [
                ("Spacious interior and sturdy construction, great for everyday use.", 5),
                ("Comfortable straps and well-made canvas material.", 4),
                ("Could use inner pockets for organization.", 3),
                ("Color faded after several washes for some users.", 2),
            ],
            'watch': [
                ("Minimalist design with accurate timekeeping and good battery life.", 5),
                ("Lightweight and comfortable for daily wear.", 4),
                ("Band may feel stiff initially.", 3),
                ("Not water resistant enough for heavy activity.", 2),
            ],
            # fallback default
            'default': [
                ("Good quality and meets expectations for {product}.", 5),
                ("Reasonably priced and functional.", 4),
                ("Average performance in some situations.", 3),
                ("Not impressed with durability over time.", 2),
            ],
        }

        # keywords to detect subtype
        subtype_keywords = {
            'tote': ['tote', 'tote bag', 'urbancarry'],
            'watch': ['watch', 'timepro'],
        }

        for p in products:
            self.stdout.write(self.style.SUCCESS(f'Updating reviews for product {p.id}: {p.name}'))
            with transaction.atomic():
                Review.objects.filter(product=p).delete()

                lower_name = p.name.lower()
                lower_desc = (p.base_description or '').lower()

                selected = None
                for key, kws in subtype_keywords.items():
                    if any(kw in lower_name or kw in lower_desc for kw in kws):
                        selected = key
                        break

                templates = subtype_templates.get(selected or 'default')

                users = [u for u in p.reviews.model.__module__ and __import__('django.contrib.auth.models', fromlist=['User']).User.objects.all()[:10]]
                # fallback for users: pick any existing user from DB
                from django.contrib.auth.models import User
                all_users = list(User.objects.all()) or [None]

                for text, rating in templates:
                    Review.objects.create(
                        product=p,
                        user=random.choice(all_users),
                        rating=rating,
                        review_text=text.format(product=p.name, brand=(p.brand or p.name), category=p.category.name)
                    )

                # clear caches and regenerate summary
                p.reviews.update(ai_summary_cache=None, sentiment_label=None, last_summarized_at=None)
                summary = get_or_generate_review_summary(p)
                if summary:
                    self.stdout.write(self.style.SUCCESS(f'  Regenerated summary: {summary.get("summary")[:120]}'))
                else:
                    self.stdout.write(self.style.WARNING('  No summary generated (no reviews)'))

        self.stdout.write(self.style.SUCCESS('Done.'))
