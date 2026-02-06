import os, sys, django, json
# Ensure project path is on sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SmartShop.settings')
import django
django.setup()
from django.test import RequestFactory
from django.contrib.auth.models import User
from product_recommendations.views import chatbot_api

user = User.objects.first()
if not user:
    print('No users found to test; create one and re-run')
else:
    rf = RequestFactory()
    req = rf.post('/chatbot/', data=json.dumps({'message':'earbuds'}), content_type='application/json')
    req.user = user
    res = chatbot_api(req)
    print('status:', res.status_code)
    print('content:', res.content.decode('utf-8'))