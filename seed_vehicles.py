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
                
                # Ensure variants exist with specific pricing
                # We'll use a more flexible mapping or let the management command handle it
                # For now, let's keep it consistent with the new realistic logic structure
                # but simplified for the seeder
                if t == 'Synthetic':
                    p_map = {1.0: 1000, 4.0: 3800, 5.0: 4500}
                elif t == 'Semi-Synthetic':
                    p_map = {1.0: 650, 4.0: 2400, 5.0: 3000}
                else: # Mineral
                    p_map = {1.0: 450, 4.0: 1800, 5.0: 2200}

                for vol, price in p_map.items():
                    from oil_logic.models import OilVariant
                    OilVariant.objects.update_or_create(
                        oil=oil,
                        volume_liters=vol,
                        defaults={'price': price}
                    )

    # Adding diverse vehicles (2010 - 2026)
    brand_models = {
        'Honda': ['Civic', 'City', 'Accord', 'Amaze', 'CR-V', 'WR-V', 'Jazz', 'Brio', 'Elevate'],
        'Toyota': ['Corolla', 'Camry', 'Fortuner', 'Innova', 'Yaris', 'Etios', 'Glanza', 'Urban Cruiser', 'Hilux'],
        'Maruti Suzuki': ['Swift', 'Baleno', 'Alto', 'WagonR', 'Dzire', 'Ertiga', 'Brezza', 'Celerio', 'S-Cross', 'Ignis', 'Fronx', 'Jimny'],
        'Hyundai': ['i10', 'i20', 'Creta', 'Verna', 'Tucson', 'Venue', 'Santro', 'Aura', 'Alcazar', 'Ioniq 5'],
        'Mahindra': ['Scorpio', 'Bolero', 'XUV500', 'XUV700', 'Thar', 'XUV300', 'Marazzo', 'KUV100'],
        'Tata': ['Nexon', 'Harrier', 'Safari', 'Tiago', 'Tigor', 'Altroz', 'Punch', 'Hexa'],
        'Kia': ['Seltos', 'Sonet', 'Carens', 'Carnival', 'EV6'],
        'Ford': ['EcoSport', 'Endeavour', 'Figo', 'Aspire', 'Freestyle', 'Mustang'],
        'Volkswagen': ['Polo', 'Vento', 'Taigun', 'Virtus', 'Tiguan', 'Passat', 'Jetta'],
        'Skoda': ['Slavia', 'Kushaq', 'Octavia', 'Superb', 'Rapid', 'Kodiaq'],
        'Renault': ['Kwid', 'Duster', 'Kiger', 'Triber', 'Captur'],
        'Nissan': ['Magnite', 'Kicks', 'Micra', 'Sunny', 'Terrano'],
        'MG': ['Hector', 'Astor', 'Gloster', 'ZSEV', 'Comet'],
    }

    engine_types = ['Petrol', 'Diesel']
    oil_types = ['Synthetic', 'Semi-Synthetic', 'Mineral']
    
    # We use the viscosities from the seeded oils above
    viscosities_list = ['0W-20', '5W-30', '10W-40', '15W-50']
    
    vehicles_data = []
    
    # Generate around 950 unique vehicles (95 models * 10 years)
    for brand, models in brand_models.items():
        for model in models:
            for year in range(2015, 2025):
                engine = random.choice(engine_types)
                displacement = random.choice([1000, 1200, 1500, 1800, 2000, 2200, 2500])
                oil_type = random.choice(oil_types)
                viscosity = random.choice(viscosities_list)
                
                vehicles_data.append({
                    'brand': brand,
                    'model': model,
                    'year': year,
                    'engine_type': engine,
                    'displacement_cc': displacement,
                    'oil_type': oil_type,
                    'viscosity': viscosity
                })
    
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
