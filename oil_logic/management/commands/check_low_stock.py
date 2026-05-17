from django.core.management.base import BaseCommand
from oil_logic.models import Oil, OilVariant
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Checks inventory for low stock items and triggers alerts.'

    def handle(self, *args, **options):
        LOW_STOCK_THRESHOLD = 10
        low_stock_items = []

        # Check primary oils
        oils = Oil.objects.filter(stock_count__lt=LOW_STOCK_THRESHOLD)
        for oil in oils:
            low_stock_items.append(f"Oil: {oil.brand} {oil.viscosity} - Only {oil.stock_count} left!")

        # Check variants
        variants = OilVariant.objects.filter(stock_count__lt=LOW_STOCK_THRESHOLD)
        for variant in variants:
            low_stock_items.append(f"Variant: {variant.oil.brand} {variant.volume_liters}L - Only {variant.stock_count} left!")

        if low_stock_items:
            message = "The following items are running low on stock:\n\n" + "\n".join(low_stock_items)
            self.stdout.write(self.style.WARNING(f"Found {len(low_stock_items)} low stock items."))
            
            # Log it
            logger.warning("Low stock alert: \n%s", message)

            # In production, you would send an email:
            # try:
            #     send_mail(
            #         'Low Stock Alert - Inventory Management',
            #         message,
            #         settings.DEFAULT_FROM_EMAIL,
            #         [admin_email for admin_name, admin_email in settings.ADMINS],
            #         fail_silently=True,
            #     )
            # except Exception as e:
            #     self.stdout.write(self.style.ERROR(f"Failed to send email: {e}"))
                
            self.stdout.write(self.style.SUCCESS('Successfully processed low stock alerts.'))
        else:
            self.stdout.write(self.style.SUCCESS('All items have sufficient stock.'))
