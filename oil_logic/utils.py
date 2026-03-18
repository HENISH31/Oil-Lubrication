from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site

def send_order_confirmation_email(request, order):
    """
    Sends a themed order confirmation email to the user.
    """
    current_site = get_current_site(request)
    subject = f'Your OilRec Order Confirmation [#{order.id}]'
    
    context = {
        'order': order,
        'domain': current_site.domain,
        'protocol': 'https' if request.is_secure() else 'http',
    }
    
    html_content = render_to_string('oil_logic/emails/order_confirmation.html', context)
    text_content = strip_tags(html_content)
    
    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [order.user.email]
    )
    email.attach_alternative(html_content, "text/html")
    
    try:
        email.send()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

import random
from decimal import Decimal

# PRICING_RULES configuration
# Format: (Brand, Oil Type): {v1L: (min, max), v4L: (min, max), v5L: (min, max)}
PRICING_RULES = {
    ("Castrol", "Synthetic"): {"1L": (950, 1100), "4L": (3600, 4000), "5L": (4200, 4800)},
    ("Castrol", "Semi-Synthetic"): {"1L": (550, 650), "4L": (2200, 2600), "5L": (2800, 3200)},
    ("Mobil 1", "Synthetic"): {"1L": (900, 1050), "4L": (3400, 3800), "5L": (4000, 4500)},
    ("Mobil Super", "Mineral"): {"1L": (400, 500), "4L": (1600, 2000), "5L": (2000, 2500)},
    ("Motul 7100", "Synthetic"): {"1L": (850, 950), "4L": (3200, 3600), "5L": (3800, 4200)},
    ("Motul 5100", "Semi-Synthetic"): {"1L": (650, 750), "4L": (2600, 3000), "5L": (3200, 3600)},
    ("Motul 3000", "Mineral"): {"1L": (450, 550), "4L": (1800, 2200), "5L": (2200, 2600)},
    ("Shell Helix Ultra", "Synthetic"): {"1L": (800, 950), "4L": (3000, 3500), "5L": (3500, 4000)},
    ("Shell Helix HX7", "Semi-Synthetic"): {"1L": (550, 650), "4L": (2200, 2600), "5L": (2800, 3200)},
    ("Valvoline SynPower", "Synthetic"): {"1L": (850, 1000), "4L": (3200, 3600), "5L": (3800, 4200)},
    ("Valvoline VR1", "Mineral"): {"1L": (750, 850), "4L": (2800, 3200), "5L": (3200, 3600)},
    ("Gulf Formula CX", "Synthetic"): {"1L": (700, 800), "4L": (2600, 3000), "5L": (3200, 3600)},
    ("Gulf Pride 4T", "Mineral"): {"1L": (350, 450), "4L": (1400, 1800), "5L": (1800, 2200)},
    ("Servo 4T Zoom", "Semi-Synthetic"): {"1L": (400, 500), "4L": (1600, 2000), "5L": (2000, 2400)},
    ("Servo Futura D", "Synthetic"): {"1L": (700, 800), "4L": (2600, 3000), "5L": (3200, 3600)},
    ("HP Milcy Turbo", "Semi-Synthetic"): {"1L": (450, 550), "4L": (1800, 2200), "5L": (2200, 2600)},
    ("HP Racer 4", "Mineral"): {"1L": (350, 450), "4L": (1400, 1800), "5L": (1800, 2200)},
    ("Total Quartz 9000", "Synthetic"): {"1L": (800, 900), "4L": (3000, 3400), "5L": (3500, 3900)},
    ("Total Quartz 7000", "Semi-Synthetic"): {"1L": (500, 600), "4L": (2000, 2400), "5L": (2500, 2900)},
    ("Liqui Moly Street Race", "Synthetic"): {"1L": (1000, 1200), "4L": (3800, 4200), "5L": (4500, 5000)},
    ("Amsoil Signature", "Synthetic"): {"1L": (1200, 1500), "4L": (4500, 5000), "5L": (5500, 6000)},
    ("Petronas Syntium", "Synthetic"): {"1L": (800, 900), "4L": (3000, 3400), "5L": (3500, 3900)},
    ("Elf Evolution 900", "Synthetic"): {"1L": (850, 950), "4L": (3200, 3600), "5L": (3800, 4200)},
}

DEFAULT_RULES = {
    "Mineral": {"1L": (400, 500), "4L": (1500, 2000), "5L": (1800, 2500)},
    "Semi-Synthetic": {"1L": (550, 700), "4L": (2000, 2600), "5L": (2500, 3200)},
    "Synthetic": {"1L": (800, 1000), "4L": (3000, 3800), "5L": (3500, 4500)},
    "Racing": {"1L": (1000, 1500), "4L": (3800, 5000), "5L": (4500, 6000)},
}

def get_realistic_price(ranges, deterministic=True):
    min_p, max_p = ranges
    if deterministic:
        return Decimal((min_p + max_p) / 2).quantize(Decimal("0.01"))
    else:
        # Slight variation (e.g., within 2% of middle)
        mid = (min_p + max_p) / 2
        variation = mid * 0.02
        return Decimal(random.uniform(mid - variation, mid + variation)).quantize(Decimal("0.01"))

def update_oil_prices_logic(oil_queryset, stdout=None):
    updated_count = 0
    
    for oil in oil_queryset:
        # Normalize fields for matching
        brand = oil.brand.strip()
        oil_type = oil.oil_type # 'Mineral', 'Synthetic', 'Semi-Synthetic'
        
        # Check specific rule
        rule = PRICING_RULES.get((brand, oil_type))
        
        # If not found, try a generic brand lookup or type default
        if not rule:
            # Special case for "Racing" which might be in oil_type or description
            if "Racing" in oil.oil_type or (oil.description and "Racing" in oil.description):
                rule = DEFAULT_RULES["Racing"]
            else:
                rule = DEFAULT_RULES.get(oil_type, DEFAULT_RULES["Mineral"])

        # Update prices
        oil.volume_1L_price = get_realistic_price(rule["1L"])
        oil.volume_4L_price = get_realistic_price(rule["4L"])
        oil.volume_5L_price = get_realistic_price(rule["5L"])
        
        # Also update the primary 'price' field
        oil.price = oil.volume_1L_price
        oil.save()

        # SYNC VARIANTS
        from .models import OilVariant
        
        # Update or create 1L variant
        OilVariant.objects.update_or_create(
            oil=oil, volume_liters=1.0,
            defaults={'price': oil.volume_1L_price}
        )
        # Update or create 4L variant
        OilVariant.objects.update_or_create(
            oil=oil, volume_liters=4.0,
            defaults={'price': oil.volume_4L_price}
        )
        # Update or create 5L variant
        OilVariant.objects.update_or_create(
            oil=oil, volume_liters=5.0,
            defaults={'price': oil.volume_5L_price}
        )
        
        updated_count += 1
        
        if stdout:
            stdout.write(f"Updated {oil.brand} {oil.viscosity} ({oil_type}) and its variants.")
            
    return updated_count
