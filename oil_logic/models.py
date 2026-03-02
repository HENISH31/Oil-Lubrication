from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Oil(models.Model):
    OIL_TYPES = [
        ('Mineral', 'Mineral'),
        ('Synthetic', 'Synthetic'),
        ('Semi-Synthetic', 'Semi-Synthetic'),
    ]

    brand = models.CharField(max_length=100)
    viscosity = models.CharField(max_length=20)  # e.g., 5W-30
    oil_type = models.CharField(max_length=20, choices=OIL_TYPES)
    api_rating = models.CharField(max_length=50, blank=True, null=True)
    jaso_rating = models.CharField(max_length=50, blank=True, null=True)
    change_interval_km = models.IntegerField(default=5000)
    change_interval_months = models.IntegerField(default=6)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    stock_count = models.IntegerField(default=100)
    rating = models.FloatField(default=4.5)

    def __str__(self):
        return f"{self.brand} {self.viscosity} ({self.oil_type})"

class Vehicle(models.Model):
    VEHICLE_TYPES = [
        ('Car', 'Car'),
        ('Bike', 'Bike'),
    ]
    ENGINE_TYPES = [
        ('Petrol', 'Petrol'),
        ('Diesel', 'Diesel'),
        ('Electric', 'Electric'),
        ('CNG', 'CNG'),
    ]

    vehicle_type = models.CharField(max_length=10, choices=VEHICLE_TYPES)
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    variant_name = models.CharField(max_length=100, default="Standard", help_text="e.g. Vxi, Zxi, Turbo, ABS")
    year = models.IntegerField()
    engine_type = models.CharField(max_length=10, choices=ENGINE_TYPES)
    displacement_cc = models.IntegerField(default=0, help_text="Engine displacement in CC")
    oil_capacity = models.FloatField(help_text="In liters")
    recommended_oil = models.ForeignKey(Oil, on_delete=models.SET_NULL, null=True, related_name='recommended_for')

    class Meta:
        unique_together = ('brand', 'model', 'year', 'variant_name', 'engine_type')

    def __str__(self):
        return f"{self.year} {self.brand} {self.model} {self.variant_name} ({self.engine_type})"

class VehicleRegistration(models.Model):
    license_plate = models.CharField(max_length=20, unique=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    owner_name = models.CharField(max_length=200, blank=True, null=True)
    puc_expiry = models.DateField()
    registration_date = models.DateField()
    
    class Meta:
        verbose_name = "Vehicle Registration"
        verbose_name_plural = "Vehicle Registrations"

    def __str__(self):
        return f"{self.license_plate} - {self.vehicle}"

class Maintenance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='maintenance_records')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    license_plate = models.CharField(max_length=20, blank=True, null=True)
    puc_expiry = models.DateField(blank=True, null=True)
    last_oil_change_km = models.IntegerField()
    last_oil_change_date = models.DateField(default=timezone.now)
    next_due_km = models.IntegerField(blank=True, null=True)
    next_due_date = models.DateField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.next_due_km:
            interval_km = self.vehicle.recommended_oil.change_interval_km if self.vehicle.recommended_oil else 5000
            self.next_due_km = self.last_oil_change_km + interval_km
        if not self.next_due_date:
            interval_months = self.vehicle.recommended_oil.change_interval_months if self.vehicle.recommended_oil else 6
            self.next_due_date = self.last_oil_change_date + timedelta(days=interval_months * 30)
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        # This would ideally be checked against current KM/Date in the view logic
        return False

    def __str__(self):
        return f"Maintenance for {self.vehicle} by {self.user.username}"
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    
    def __str__(self):
        return f"Profile for {self.user.username}"

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    oil = models.ForeignKey(Oil, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        return self.oil.price * self.quantity

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    oil = models.ForeignKey(Oil, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.oil.brand if self.oil else 'Unknown Oil'}"

