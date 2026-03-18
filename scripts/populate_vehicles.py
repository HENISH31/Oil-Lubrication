import os
import django

# Set up Django environment
# Assuming the script is in /scripts/ folder
import sys

def run():
    from oil_logic.models import Vehicle, Oil

    new_vehicles = [
        # --- CARS ---
        # Maruti Suzuki
        {'vehicle_type': 'Car', 'brand': 'Maruti Suzuki', 'model': 'Grand Vitara', 'variant_name': 'Alpha', 'year': 2023, 'engine_type': 'Petrol', 'displacement_cc': 1462, 'oil_capacity': 3.5},
        {'vehicle_type': 'Car', 'brand': 'Maruti Suzuki', 'model': 'Grand Vitara', 'variant_name': 'Zeta', 'year': 2024, 'engine_type': 'CNG', 'displacement_cc': 1462, 'oil_capacity': 3.5},
        {'vehicle_type': 'Car', 'brand': 'Maruti Suzuki', 'model': 'Fronx', 'variant_name': 'Delta+', 'year': 2023, 'engine_type': 'Petrol', 'displacement_cc': 1197, 'oil_capacity': 3.2},
        {'vehicle_type': 'Car', 'brand': 'Maruti Suzuki', 'model': 'Jimny', 'variant_name': 'Alpha', 'year': 2024, 'engine_type': 'Petrol', 'displacement_cc': 1462, 'oil_capacity': 3.8},
        
        # Tata Motors
        {'vehicle_type': 'Car', 'brand': 'Tata', 'model': 'Safari', 'variant_name': 'Adventure', 'year': 2023, 'engine_type': 'Diesel', 'displacement_cc': 1956, 'oil_capacity': 5.0},
        {'vehicle_type': 'Car', 'brand': 'Tata', 'model': 'Harrier', 'variant_name': 'Dark Edition', 'year': 2024, 'engine_type': 'Diesel', 'displacement_cc': 1956, 'oil_capacity': 5.0},
        {'vehicle_type': 'Car', 'brand': 'Tata', 'model': 'Nexon', 'variant_name': 'Creative', 'year': 2023, 'engine_type': 'Petrol', 'displacement_cc': 1199, 'oil_capacity': 3.5},
        {'vehicle_type': 'Car', 'brand': 'Tata', 'model': 'Punch', 'variant_name': 'Accomplished', 'year': 2024, 'engine_type': 'CNG', 'displacement_cc': 1199, 'oil_capacity': 3.3},
        
        # Hyundai
        {'vehicle_type': 'Car', 'brand': 'Hyundai', 'model': 'Exter', 'variant_name': 'SX(O)', 'year': 2023, 'engine_type': 'Petrol', 'displacement_cc': 1197, 'oil_capacity': 3.4},
        {'vehicle_type': 'Car', 'brand': 'Hyundai', 'model': 'Verna', 'variant_name': 'Turbo', 'year': 2024, 'engine_type': 'Petrol', 'displacement_cc': 1482, 'oil_capacity': 4.0},
        {'vehicle_type': 'Car', 'brand': 'Hyundai', 'model': 'Creta', 'variant_name': 'Knight', 'year': 2024, 'engine_type': 'Diesel', 'displacement_cc': 1493, 'oil_capacity': 4.8},
        
        # Mahindra
        {'vehicle_type': 'Car', 'brand': 'Mahindra', 'model': 'XUV700', 'variant_name': 'AX7', 'year': 2023, 'engine_type': 'Petrol', 'displacement_cc': 1997, 'oil_capacity': 5.5},
        {'vehicle_type': 'Car', 'brand': 'Mahindra', 'model': 'XUV700', 'variant_name': 'AX7', 'year': 2023, 'engine_type': 'Diesel', 'displacement_cc': 2184, 'oil_capacity': 6.0},
        {'vehicle_type': 'Car', 'brand': 'Mahindra', 'model': 'Scorpio-N', 'variant_name': 'Z8L', 'year': 2024, 'engine_type': 'Diesel', 'displacement_cc': 2184, 'oil_capacity': 6.0},
        {'vehicle_type': 'Car', 'brand': 'Mahindra', 'model': 'Thar', 'variant_name': 'RWD', 'year': 2023, 'engine_type': 'Petrol', 'displacement_cc': 1997, 'oil_capacity': 5.2},
        
        # Toyota
        {'vehicle_type': 'Car', 'brand': 'Toyota', 'model': 'Innova Hycross', 'variant_name': 'VX', 'year': 2023, 'engine_type': 'Petrol', 'displacement_cc': 1987, 'oil_capacity': 4.5},
        {'vehicle_type': 'Car', 'brand': 'Toyota', 'model': 'Fortuner', 'variant_name': 'Legender', 'year': 2024, 'engine_type': 'Diesel', 'displacement_cc': 2755, 'oil_capacity': 7.5},
        
        # Kia
        {'vehicle_type': 'Car', 'brand': 'Kia', 'model': 'Seltos', 'variant_name': 'GT Line', 'year': 2024, 'engine_type': 'Petrol', 'displacement_cc': 1482, 'oil_capacity': 4.0},
        {'vehicle_type': 'Car', 'brand': 'Kia', 'model': 'Carens', 'variant_name': 'Luxury Plus', 'year': 2023, 'engine_type': 'Diesel', 'displacement_cc': 1493, 'oil_capacity': 4.5},

        # --- BIKES ---
        # Royal Enfield
        {'vehicle_type': 'Bike', 'brand': 'Royal Enfield', 'model': 'Himalayan 450', 'variant_name': 'Standard', 'year': 2024, 'engine_type': 'Petrol', 'displacement_cc': 452, 'oil_capacity': 2.1},
        {'vehicle_type': 'Bike', 'brand': 'Royal Enfield', 'model': 'Hunter 350', 'variant_name': 'Metro', 'year': 2023, 'engine_type': 'Petrol', 'displacement_cc': 349, 'oil_capacity': 1.9},
        {'vehicle_type': 'Bike', 'brand': 'Royal Enfield', 'model': 'Interceptor 650', 'variant_name': 'Chrome', 'year': 2024, 'engine_type': 'Petrol', 'displacement_cc': 648, 'oil_capacity': 3.1},
        
        # Bajaj
        {'vehicle_type': 'Bike', 'brand': 'Bajaj', 'model': 'Pulsar NS200', 'variant_name': 'UG', 'year': 2023, 'engine_type': 'Petrol', 'displacement_cc': 199, 'oil_capacity': 1.2},
        {'vehicle_type': 'Bike', 'brand': 'Bajaj', 'model': 'Dominar 400', 'variant_name': 'Touring', 'year': 2024, 'engine_type': 'Petrol', 'displacement_cc': 373, 'oil_capacity': 1.7},
        
        # TVS
        {'vehicle_type': 'Bike', 'brand': 'TVS', 'model': 'Apache RTR 310', 'variant_name': 'Standard', 'year': 2024, 'engine_type': 'Petrol', 'displacement_cc': 312, 'oil_capacity': 1.6},
        {'vehicle_type': 'Bike', 'brand': 'TVS', 'model': 'Ronin', 'variant_name': 'DS', 'year': 2023, 'engine_type': 'Petrol', 'displacement_cc': 225, 'oil_capacity': 1.2},
        
        # KTM
        {'vehicle_type': 'Bike', 'brand': 'KTM', 'model': 'Duke 390', 'variant_name': 'Gen 3', 'year': 2024, 'engine_type': 'Petrol', 'displacement_cc': 399, 'oil_capacity': 1.7},
        {'vehicle_type': 'Bike', 'brand': 'KTM', 'model': 'Adventure 390', 'variant_name': 'SW', 'year': 2023, 'engine_type': 'Petrol', 'displacement_cc': 373, 'oil_capacity': 1.7},

        # Honda
        {'vehicle_type': 'Bike', 'brand': 'Honda', 'model': 'CB350', 'variant_name': 'RS', 'year': 2024, 'engine_type': 'Petrol', 'displacement_cc': 348, 'oil_capacity': 2.0},
        
        # Adding some generic older models for depth
        {'vehicle_type': 'Car', 'brand': 'Maruti Suzuki', 'model': 'Swift', 'variant_name': 'Lxi', 'year': 2022, 'engine_type': 'Petrol', 'displacement_cc': 1197, 'oil_capacity': 3.1},
        {'vehicle_type': 'Car', 'brand': 'Maruti Suzuki', 'model': 'Swift', 'variant_name': 'Vxi', 'year': 2021, 'engine_type': 'Petrol', 'displacement_cc': 1197, 'oil_capacity': 3.1},
        {'vehicle_type': 'Car', 'brand': 'Maruti Suzuki', 'model': 'Swift', 'variant_name': 'Zxi', 'year': 2020, 'engine_type': 'Petrol', 'displacement_cc': 1197, 'oil_capacity': 3.1},
        
        {'vehicle_type': 'Car', 'brand': 'Hyundai', 'model': 'i20', 'variant_name': 'Magna', 'year': 2022, 'engine_type': 'Petrol', 'displacement_cc': 1197, 'oil_capacity': 3.3},
        {'vehicle_type': 'Car', 'brand': 'Hyundai', 'model': 'i20', 'variant_name': 'Asta', 'year': 2021, 'engine_type': 'Diesel', 'displacement_cc': 1493, 'oil_capacity': 4.5},
        
        {'vehicle_type': 'Car', 'brand': 'Volkswagen', 'model': 'Virtus', 'variant_name': 'GT', 'year': 2023, 'engine_type': 'Petrol', 'displacement_cc': 1498, 'oil_capacity': 4.0},
        {'vehicle_type': 'Car', 'brand': 'Skoda', 'model': 'Slavia', 'variant_name': 'Style', 'year': 2024, 'engine_type': 'Petrol', 'displacement_cc': 999, 'oil_capacity': 3.5},
        
        # Adding 20 more to reach comfortably over 300
        {'vehicle_type': 'Bike', 'brand': 'Yamaha', 'model': 'R15 V4', 'variant_name': 'M', 'year': 2023, 'engine_type': 'Petrol', 'displacement_cc': 155, 'oil_capacity': 1.0},
        {'vehicle_type': 'Bike', 'brand': 'Yamaha', 'model': 'MT-15', 'variant_name': 'Ver 2.0', 'year': 2024, 'engine_type': 'Petrol', 'displacement_cc': 155, 'oil_capacity': 1.0},
        
        {'vehicle_type': 'Car', 'brand': 'MG', 'model': 'Hector', 'variant_name': 'Sharp', 'year': 2023, 'engine_type': 'Diesel', 'displacement_cc': 1956, 'oil_capacity': 5.2},
        {'vehicle_type': 'Car', 'brand': 'Jeep', 'model': 'Compass', 'variant_name': 'Model S', 'year': 2024, 'engine_type': 'Diesel', 'displacement_cc': 1956, 'oil_capacity': 5.4},
        
        {'vehicle_type': 'Car', 'brand': 'Renault', 'model': 'Kiger', 'variant_name': 'RXZ', 'year': 2023, 'engine_type': 'Petrol', 'displacement_cc': 999, 'oil_capacity': 3.1},
        {'vehicle_type': 'Car', 'brand': 'Nissan', 'model': 'Magnite', 'variant_name': 'XV Premium', 'year': 2024, 'engine_type': 'Petrol', 'displacement_cc': 999, 'oil_capacity': 3.2},
        
        {'vehicle_type': 'Bike', 'brand': 'Hero', 'model': 'Xpulse 200 4V', 'variant_name': 'Pro', 'year': 2024, 'engine_type': 'Petrol', 'displacement_cc': 199, 'oil_capacity': 1.1},
        {'vehicle_type': 'Bike', 'brand': 'Hero', 'model': 'Mavrick 440', 'variant_name': 'Base', 'year': 2024, 'engine_type': 'Petrol', 'displacement_cc': 440, 'oil_capacity': 2.0},
        
        # Padding with more years/variants for popular models to hit 300
        {'vehicle_type': 'Car', 'brand': 'Maruti Suzuki', 'model': 'Ertiga', 'variant_name': 'Zxi+', 'year': 2023, 'engine_type': 'Petrol', 'displacement_cc': 1462, 'oil_capacity': 3.5},
        {'vehicle_type': 'Car', 'brand': 'Maruti Suzuki', 'model': 'Brezza', 'variant_name': 'Zxi', 'year': 2024, 'engine_type': 'Petrol', 'displacement_cc': 1462, 'oil_capacity': 3.5},
        
        {'vehicle_type': 'Car', 'brand': 'Tata', 'model': 'Tiago', 'variant_name': 'XZ+', 'year': 2023, 'engine_type': 'Petrol', 'displacement_cc': 1199, 'oil_capacity': 3.2},
        {'vehicle_type': 'Car', 'brand': 'Tata', 'model': 'Tigor', 'variant_name': 'XZA', 'year': 2022, 'engine_type': 'CNG', 'displacement_cc': 1199, 'oil_capacity': 3.2},
        
        {'vehicle_type': 'Car', 'brand': 'Hyundai', 'model': 'Venue', 'variant_name': 'N Line', 'year': 2023, 'engine_type': 'Petrol', 'displacement_cc': 998, 'oil_capacity': 3.6},
        {'vehicle_type': 'Car', 'brand': 'Hyundai', 'model': 'Alcazar', 'variant_name': 'Signature', 'year': 2024, 'engine_type': 'Diesel', 'displacement_cc': 1493, 'oil_capacity': 4.8},
        
        {'vehicle_type': 'Car', 'brand': 'Kia', 'model': 'Sonet', 'variant_name': 'X-Line', 'year': 2024, 'engine_type': 'Petrol', 'displacement_cc': 998, 'oil_capacity': 3.6},
        {'vehicle_type': 'Car', 'brand': 'Honda', 'model': 'City', 'variant_name': 'ZX', 'year': 2023, 'engine_type': 'Petrol', 'displacement_cc': 1498, 'oil_capacity': 3.7},
        {'vehicle_type': 'Car', 'brand': 'Honda', 'model': 'Elevate', 'variant_name': 'ZX', 'year': 2024, 'engine_type': 'Petrol', 'displacement_cc': 1498, 'oil_capacity': 3.7},
        
        {'vehicle_type': 'Bike', 'brand': 'Jawa', 'model': '350', 'variant_name': 'Standard', 'year': 2024, 'engine_type': 'Petrol', 'displacement_cc': 334, 'oil_capacity': 2.3},
        {'vehicle_type': 'Bike', 'brand': 'Yezdi', 'model': 'Adventure', 'variant_name': 'Mountain Pack', 'year': 2023, 'engine_type': 'Petrol', 'displacement_cc': 334, 'oil_capacity': 2.3},
        
        {'vehicle_type': 'Bike', 'brand': 'Triumph', 'model': 'Speed 400', 'variant_name': 'Standard', 'year': 2024, 'engine_type': 'Petrol', 'displacement_cc': 398, 'oil_capacity': 2.0},
        {'vehicle_type': 'Bike', 'brand': 'Triumph', 'model': 'Scrambler 400X', 'variant_name': 'Standard', 'year': 2024, 'engine_type': 'Petrol', 'displacement_cc': 398, 'oil_capacity': 2.0},
    ]

    count = 0
    for v_data in new_vehicles:
        obj, created = Vehicle.objects.get_or_create(
            brand=v_data['brand'],
            model=v_data['model'],
            year=v_data['year'],
            variant_name=v_data['variant_name'],
            engine_type=v_data['engine_type'],
            defaults={
                'vehicle_type': v_data['vehicle_type'],
                'displacement_cc': v_data['displacement_cc'],
                'oil_capacity': v_data['oil_capacity']
            }
        )
        if created:
            count += 1
    
    print(f"Successfully added {count} new vehicle records!")
    print(f"Total Vehicle Count: {Vehicle.objects.count()}")

if __name__ == "__main__":
    # This block allows running the script directly if needed, 
    # but we will use it with 'python manage.py shell'
    run()
