import os
import sys
import django
# Ensure project root is on sys.path so Django settings are importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SmartShop.settings")
django.setup()
from django.test import RequestFactory
from django.contrib.auth.models import User
from product_recommendations.views import recommendation_dashboard

user = User.objects.filter(username__startswith='user').first()
print('Using user:', user)
rf = RequestFactory()
request = rf.get('/recommendations/dashboard/')
request.user = user
resp = recommendation_dashboard(request)
print('Response type:', type(resp))
if hasattr(resp, 'status_code'):
    print('status:', resp.status_code)

# If response has content (rendered template), print a snippet
if hasattr(resp, 'content'):
    try:
        print(resp.content.decode('utf-8')[:500])
    except Exception as e:
        print('Could not decode content:', e)
