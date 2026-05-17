import os
import sys
import django

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import RequestFactory
from oil_logic.views import VehicleViewSet
from oil_logic.models import Vehicle

from rest_framework.request import Request

def test_recommendation_logic():
    factory = RequestFactory()
    viewset = VehicleViewSet()
    
    # Test cases: (brand, model, year, condition, mileage)
    test_cases = [
        ('Honda', 'City', 2023, 'Highway', '0-50k'),
        ('Honda', 'City', 2023, 'Off-road', 'Above-150k'),
        ('Maruti Suzuki', 'Swift', 2021, 'City', '50k-100k'),
    ]
    
    for brand, model, year, cond, mil in test_cases:
        print(f"\nTesting: {brand} {model} ({year}) | {cond} | {mil}")
        url = f'/api/vehicles/recommendations/?brand={brand}&model={model}&year={year}&driving_condition={cond}&mileage_range={mil}'
        wsgi_request = factory.get(url)
        # Wrap in DRF Request
        request = Request(wsgi_request)
        response = viewset.recommendations(request)
        
        if response.status_code == 200:
            data = response.data
            for vehicle in data:
                recs = vehicle['recommendations']
                print(f"Vehicle: {vehicle['model']} ({vehicle['year']})")
                print(f"  - Primary: {recs['primary']['brand']} {recs['primary']['viscosity']} ({recs['primary']['oil_type']}) - INR {recs['primary']['price']}")
                print(f"  - Premium: {recs['premium']['brand']} {recs['premium']['viscosity']} ({recs['premium']['oil_type']})")
                print(f"  - Economy: {recs['economy']['brand']} {recs['economy']['viscosity']} ({recs['economy']['oil_type']})")
        else:
            print(f"Error: {response.status_code} - {response.data}")

if __name__ == '__main__':
    test_recommendation_logic()
