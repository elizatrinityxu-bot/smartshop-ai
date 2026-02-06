from django.core.management.base import BaseCommand
from product_recommendations.models import Product, Review
from product_recommendations.services.review_summary_service import get_or_generate_review_summary

class Command(BaseCommand):
    help = "Regenerate AI review summaries for all products (clears cache first)"

    def handle(self, *args, **kwargs):
        products = Product.objects.all()
        total = products.count()
        self.stdout.write(f"Regenerating summaries for {total} products...")

        for p in products:
            # Clear cached values on reviews for this product
            Review.objects.filter(product=p).update(ai_summary_cache=None, sentiment_label=None, last_summarized_at=None)

            # Force generation (will use fallback if OPENAI_API_KEY is missing)
            summary = get_or_generate_review_summary(p)
            if summary:
                self.stdout.write(self.style.SUCCESS(f"  Generated summary for {p.id}: {p.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"  Skipped {p.id}: {p.name} (no reviews)"))

        self.stdout.write(self.style.SUCCESS("Done."))