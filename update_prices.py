import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from oil_logic.models import OilVariant

def update_variant_prices():
    print("Updating OilVariant prices...")
    price_map = {
        1.0: 850.00,
        4.0: 3200.00,
        5.0: 3900.00
    }
    
    total_updated = 0
    for volume, new_price in price_map.items():
        count = OilVariant.objects.filter(volume_liters=volume).update(price=new_price)
        total_updated += count
        print(f"Updated {count} variants for {volume}L to ₹{new_price}")
    
    print(f"Total records updated: {total_updated}")

if __name__ == '__main__':
    update_variant_prices()
