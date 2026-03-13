import os
import django
import random

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from oil_logic.models import Vehicle, Oil

def seed_more_data():
    print("Seeding more vehicle data...")
    
    # Ensure some oils exist first
    brands = ['Shell', 'Castrol', 'Mobil 1', 'Motul', 'Valvoline']
    viscosities = ['0W-20', '5W-30', '10W-40', '15W-50']
    types = ['Synthetic', 'Semi-Synthetic', 'Mineral']
    
    for b in brands:
        for v in viscosities:
            for t in types:
                oil, created = Oil.objects.get_or_create(
                    brand=b,
                    viscosity=v,
                    oil_type=t,
                    defaults={
                        'price': random.randint(500, 2500),
                        'volume_liters': 1.0,
                        'rating': round(random.uniform(4.0, 5.0), 1),
                        'api_rating': 'SN/CF'
                    }
                )
                
                # Ensure variants exist with specific pricing: 1L=850, 4L=3200, 5L=3900
                price_map = {1.0: 850, 4.0: 3200, 5.0: 3900}
                for vol, price in price_map.items():
                    from oil_logic.models import OilVariant
                    OilVariant.objects.update_or_create(
                        oil=oil,
                        volume_liters=vol,
                        defaults={'price': price}
                    )

    # Adding diverse vehicles (2010 - 2026)
    vehicles_data = [
        # Older models (2010-2015)
        {'brand': 'Honda', 'model': 'Civic', 'year': 2010, 'engine_type': 'Petrol', 'displacement_cc': 1800, 'oil_type': 'Mineral', 'viscosity': '10W-30'},
        {'brand': 'Toyota', 'model': 'Corolla', 'year': 2012, 'engine_type': 'Petrol', 'displacement_cc': 1800, 'oil_type': 'Semi-Synthetic', 'viscosity': '5W-30'},
        {'brand': 'Maruti Suzuki', 'model': 'Swift', 'year': 2011, 'engine_type': 'Diesel', 'displacement_cc': 1300, 'oil_type': 'Semi-Synthetic', 'viscosity': '5W-40'},
        {'brand': 'Hyundai', 'model': 'i10', 'year': 2013, 'engine_type': 'Petrol', 'displacement_cc': 1100, 'oil_type': 'Mineral', 'viscosity': '10W-40'},
        {'brand': 'Mahindra', 'model': 'Scorpio', 'year': 2014, 'engine_type': 'Diesel', 'displacement_cc': 2200, 'oil_type': 'Semi-Synthetic', 'viscosity': '15W-40'},
        
        # Mid-range models (2016-2020)
        {'brand': 'Honda', 'model': 'City', 'year': 2017, 'engine_type': 'Petrol', 'displacement_cc': 1500, 'oil_type': 'Synthetic', 'viscosity': '0W-20'},
        {'brand': 'Toyota', 'model': 'Fortuner', 'year': 2018, 'engine_type': 'Diesel', 'displacement_cc': 2800, 'oil_type': 'Synthetic', 'viscosity': '5W-30'},
        {'brand': 'Hyundai', 'model': 'Creta', 'year': 2019, 'engine_type': 'Diesel', 'displacement_cc': 1600, 'oil_type': 'Synthetic', 'viscosity': '5W-30'},
        {'brand': 'Ford', 'model': 'EcoSport', 'year': 2016, 'engine_type': 'Petrol', 'displacement_cc': 1500, 'oil_type': 'Semi-Synthetic', 'viscosity': '5W-30'},
        
        # Recent & Future models (2021-2026)
        {'brand': 'Honda', 'model': 'Elevate', 'year': 2024, 'engine_type': 'Petrol', 'displacement_cc': 1500, 'oil_type': 'Synthetic', 'viscosity': '0W-20'},
        {'brand': 'Toyota', 'model': 'Urban Cruiser', 'year': 2025, 'engine_type': 'Petrol', 'displacement_cc': 1500, 'oil_type': 'Synthetic', 'viscosity': '0W-20'},
        {'brand': 'Maruti Suzuki', 'model': 'Fronx', 'year': 2024, 'engine_type': 'Petrol', 'displacement_cc': 1000, 'oil_type': 'Synthetic', 'viscosity': '0W-16'},
        {'brand': 'Mahindra', 'model': 'XUV700', 'year': 2024, 'engine_type': 'Diesel', 'displacement_cc': 2200, 'oil_type': 'Synthetic', 'viscosity': '5W-30'},
        {'brand': 'Hyundai', 'model': 'Ioniq 5', 'year': 2026, 'engine_type': 'Petrol', 'displacement_cc': 0, 'oil_type': 'Synthetic', 'viscosity': '0W-20'}, # Mocking for hybrid/future tech
        {'brand': 'Tata', 'model': 'Harrier', 'year': 2025, 'engine_type': 'Diesel', 'displacement_cc': 2000, 'oil_type': 'Synthetic', 'viscosity': '0W-30'},
        {'brand': 'Kia', 'model': 'Seltos', 'year': 2026, 'engine_type': 'Petrol', 'displacement_cc': 1500, 'oil_type': 'Synthetic', 'viscosity': '0W-20'},
    ]
    
    for v_entry in vehicles_data:
        # Find a suitable oil to recommend
        recommended_oil = Oil.objects.filter(
            viscosity=v_entry['viscosity'], 
            oil_type=v_entry['oil_type']
        ).first()
        
        if not recommended_oil:
            # Fallback to any oil of same viscosity
            recommended_oil = Oil.objects.filter(viscosity=v_entry['viscosity']).first()

        Vehicle.objects.get_or_create(
            brand=v_entry['brand'],
            model=v_entry['model'],
            year=v_entry['year'],
            engine_type=v_entry['engine_type'],
            variant_name='Standard',
            defaults={
                'displacement_cc': v_entry['displacement_cc'],
                'oil_capacity': 4.0,
                'recommended_oil': recommended_oil
            }
        )
    
    print(f"Seeding complete. Added/Updated {len(vehicles_data)} vehicles.")

if __name__ == '__main__':
    seed_more_data()
