import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SmartShop.settings')
import django
django.setup()
from product_recommendations.models import Product

print('Products with "hair" in name:')
for p in Product.objects.filter(is_active=True, name__icontains='hair'):
    print('-', p.name, 'price=', p.price, 'category=', p.category.name, 'is_active=', p.is_active)

print('\nSearch for keywords hair, dryer in name/description:')
from django.db.models import Q
qs = Product.objects.filter(is_active=True).filter(
    Q(name__icontains='hair') | Q(base_description__icontains='hair') | Q(name__icontains='dryer') | Q(base_description__icontains='dryer')
)
print('Matches:', [p.name for p in qs])
print('\nAll categories:', list(set([p.category.name for p in Product.objects.filter(is_active=True)])))
