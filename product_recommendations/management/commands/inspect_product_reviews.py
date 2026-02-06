from django.core.management.base import BaseCommand
from django.db.models import Avg
from product_recommendations.models import Product

class Command(BaseCommand):
    help = 'Print review texts for a specific product name (for debugging)'

    def add_arguments(self, parser):
        parser.add_argument('product_name', type=str)

    def handle(self, *args, **kwargs):
        name = kwargs['product_name']
        try:
            p = Product.objects.get(name__icontains=name)
        except Product.DoesNotExist:
            self.stdout.write(self.style.ERROR('Product not found'))
            return

        self.stdout.write(self.style.SUCCESS(f'Product: {p.name} (id={p.id})'))
        for r in p.reviews.all():
            self.stdout.write(f'- [{r.rating}] {r.review_text} | sentiment_label={r.sentiment_label} | cache_len={len(r.ai_summary_cache or "")}')

        avg = p.reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
        self.stdout.write(self.style.SUCCESS(f'Average rating: {avg}'))

        cached = p.reviews.filter(ai_summary_cache__isnull=False).first()
        if cached:
            self.stdout.write(self.style.SUCCESS('Cached content (first 200 chars):'))
            self.stdout.write(cached.ai_summary_cache[:200])
            # test sentiment extractor
            from product_recommendations.services.review_summary_service import extract_sentiment
            s = extract_sentiment(cached.ai_summary_cache, p.reviews.all())
            self.stdout.write(self.style.SUCCESS(f'Extracted sentiment from cache: {repr(s)}'))
            s2 = extract_sentiment(' '.join([r.review_text for r in p.reviews.all()][:3]), p.reviews.all())
            self.stdout.write(self.style.SUCCESS(f'Extracted sentiment from excerpt: {s2}'))

