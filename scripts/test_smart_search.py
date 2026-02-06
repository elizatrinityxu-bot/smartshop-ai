import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SmartShop.settings')
import django
django.setup()
from product_recommendations.services.smart_search_service import smart_search_products

queries = ["recommend hair dryer", "looking for a powerful hair dryer under $100", "durable power bank under $50", "I need a sunscreen for sensitive skin"]
for q in queries:
    res, meta = smart_search_products(q, return_metadata=True)
    print('-' * 40)
    print('Query:', q)
    print('Parsed:', meta.get('parsed'))
    print('Applied filters:', meta.get('applied_filters'))
    print('Matches:', [p.name for p in res[:5]])
