import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SmartShop.settings')
import django
django.setup()
from django.test import Client

c = Client()
# Seeded user password is 'password123'
logged_in = c.login(username='Ethan Wong', password='password123')
print('Logged in:', logged_in)

queries = ['hair dryer', 'looking for a powerful hair dryer under $100']
for q in queries:
    # Use HTTP_HOST header matching the running dev server so Django accepts the host
    resp = c.get('/search/', {'q': q}, HTTP_HOST='127.0.0.1')
    print('-' * 40)
    print('Query:', q)
    try:
        print('Status code:', resp.status_code)
        print('JSON:', resp.json())
    except Exception as e:
        print('Non-JSON response or error:', e)
        print(resp.content)
