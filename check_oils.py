import os
import sys
import django

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from oil_logic.models import Oil
import json

oils = []
for o in Oil.objects.all():
    oils.append({
        'id': o.id,
        'brand': o.brand,
        'viscosity': o.viscosity,
        'image': str(o.image) if o.image else None,
        'image_url': o.image_url
    })

print(json.dumps(oils, indent=2))
