from django.core.management.base import BaseCommand
from oil_logic.models import Oil
from oil_logic.utils import update_oil_prices_logic

class Command(BaseCommand):
    help = "Update oil prices to realistic 2025-2026 market values based on brand and type."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting oil price update..."))
        
        oils = Oil.objects.all()
        total = oils.count()
        
        updated = update_oil_prices_logic(oils, self.stdout)
        
        self.stdout.write(self.style.SUCCESS(f"Successfully updated {updated}/{total} oil records."))
