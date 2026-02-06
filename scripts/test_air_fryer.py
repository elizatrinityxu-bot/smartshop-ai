import os,sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE','SmartShop.settings')
import django
django.setup()
from product_recommendations.services.smart_search_service import smart_search_products

queries = ["i am looking for air fryer", "air fryer", "looking for air fryer"]
for q in queries:
    res, meta = smart_search_products(q, return_metadata=True)
    names = [p.name for p in (res[:10] if hasattr(res,'__getitem__') else [])]
    print('-'*60)
    print('Query:', q)
    print('Parsed:', meta.get('parsed'))
    print('Applied filters:', meta.get('applied_filters'))
    print('Matches:', names)
