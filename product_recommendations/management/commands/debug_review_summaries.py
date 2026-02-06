from django.core.management.base import BaseCommand
from product_recommendations.models import Product, Review
from product_recommendations.services.review_summary_service import (
    extract_bullets, extract_summary_only, extract_sentiment
)

class Command(BaseCommand):
    help = "Debug AI review summaries across products"

    def handle(self, *args, **kwargs):
        for p in Product.objects.all():
            reviews = Review.objects.filter(product=p)
            cached = reviews.filter(ai_summary_cache__isnull=False).first()
            if cached:
                content = cached.ai_summary_cache or ""
                summary = extract_summary_only(content) if content else ""
                pros = extract_bullets(content, "Pros")
                cons = extract_bullets(content, "Cons")
                sentiment = cached.sentiment_label or extract_sentiment(content)
                self.stdout.write(self.style.SUCCESS(f"Product {p.id}: {p.name}"))
                self.stdout.write(f"  Reviews: {reviews.count()}")
                self.stdout.write(f"  Summary: {summary[:120]}")
                self.stdout.write(f"  Pros ({len(pros)}): {pros}")
                self.stdout.write(f"  Cons ({len(cons)}): {cons}")
                self.stdout.write(f"  Sentiment: {sentiment}")
            else:
                self.stdout.write(self.style.WARNING(f"Product {p.id}: {p.name} - No cached summary"))
