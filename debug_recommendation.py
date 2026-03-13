import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from oil_logic.views import VehicleViewSet
from rest_framework.test import APIRequestFactory

factory = APIRequestFactory()
request = factory.get('/api/vehicles/recommendations/', {
    'brand': 'Ferrari',
    'model': 'Roma',
    'year': '2024',
    'driving_condition': 'City',
    'mileage_range': '0-50k',
    'preferred_frequency': '5-6m'
})

view = VehicleViewSet.as_view({'get': 'recommendations'})
response = view(request)
print(f"Status: {response.status_code}")
print(f"Data: {response.data}")
