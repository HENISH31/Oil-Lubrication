from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Oil(models.Model):
    VEHICLE_TYPES = [
        ('Car', 'Car'),
        ('Bike', 'Bike'),
        ('Scooter', 'Scooter'),
        ('Truck', 'Truck'),
    ]

    OIL_TYPES = [
        ('Mineral', 'Mineral'),
        ('Synthetic', 'Synthetic'),
        ('Semi-Synthetic', 'Semi-Synthetic'),
    ]

    brand = models.CharField(max_length=100)
    viscosity = models.CharField(max_length=20)  # e.g., 5W-30
    oil_type = models.CharField(max_length=20, choices=OIL_TYPES)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES, default='Car')
    api_rating = models.CharField(max_length=50, blank=True, null=True)
    jaso_rating = models.CharField(max_length=50, blank=True, null=True)
    change_interval_km = models.IntegerField(default=5000)
    change_interval_months = models.IntegerField(default=6)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    volume_liters = models.FloatField(default=1.0, help_text="Volume in Liters")
    # Volume-specific pricing
    volume_1L_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Price for 1L")
    volume_4L_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Price for 4L", blank=True, null=True)
    volume_5L_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Price for 5L", blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    image = models.ImageField(upload_to='oils/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    stock_count = models.IntegerField(default=100)
    rating = models.FloatField(default=4.5)

    def __str__(self):
        return f"{self.brand} {self.viscosity} ({self.oil_type})"

class OilVariant(models.Model):
    """Store volume and price combinations for each oil product"""
    oil = models.ForeignKey(Oil, on_delete=models.CASCADE, related_name='variants')
    volume_liters = models.FloatField(choices=[(1.0, '1L'), (4.0, '4L'), (5.0, '5L')])
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_count = models.IntegerField(default=100)
    image = models.ImageField(upload_to='oil_variants/', blank=True, null=True)
    
    class Meta:
        unique_together = ('oil', 'volume_liters')
    
    def __str__(self):
        return f"{self.oil.brand} {self.oil.viscosity} - {self.volume_liters}L @ ₹{self.price}"

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
    DRIVING_CONDITIONS = [
        ('City', 'City/Traffic'),
        ('Highway', 'Highway/Long Drive'),
        ('Mixed', 'Mixed (Both)'),
        ('Off-road', 'Off-road/Rough terrain'),
    ]
    MILEAGE_RANGES = [
        ('0-50k', '0-50,000 km'),
        ('50k-100k', '50,001-1,00,000 km'),
        ('100k-150k', '1,00,001-1,50,000 km'),
        ('Above-150k', 'Above 1,50,000 km'),
    ]
    OIL_CHANGE_FREQUENCIES = [
        ('3-4m', 'Every 3-4 months'),
        ('5-6m', 'Every 5-6 months'),
        ('12m', 'Every 12 months'),
        ('Manufacturer', 'As per manufacturer only'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='maintenance_records')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    license_plate = models.CharField(max_length=20, blank=True, null=True)
    puc_expiry = models.DateField(blank=True, null=True)
    last_oil_change_km = models.IntegerField()
    last_oil_change_date = models.DateField(default=timezone.now)
    next_due_km = models.IntegerField(blank=True, null=True)
    next_due_date = models.DateField(blank=True, null=True)
    
    # New fields for recommendation logic
    driving_condition = models.CharField(max_length=20, choices=DRIVING_CONDITIONS, default='Mixed')
    mileage_range = models.CharField(max_length=20, choices=MILEAGE_RANGES, default='0-50k')
    preferred_frequency = models.CharField(max_length=20, choices=OIL_CHANGE_FREQUENCIES, default='5-6m')
    color = models.CharField(max_length=7, default='#3B82F6', help_text="Vehicle color in Hex (e.g. #FF0000)")
    current_km = models.IntegerField(default=0)

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

class ServiceRecord(models.Model):
    maintenance = models.ForeignKey(Maintenance, on_delete=models.CASCADE, related_name='service_records')
    date = models.DateField(default=timezone.now)
    oil_type = models.CharField(max_length=100)
    km = models.IntegerField()
    service_center = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Service at {self.km} KM - {self.maintenance.vehicle}"
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    tagline = models.CharField(max_length=255, blank=True, null=True, help_text="A short tagline to display on your profile.")
    
    def __str__(self):
        return f"Profile for {self.user.username}"

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    oil = models.ForeignKey(Oil, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    volume_liters = models.FloatField(default=1.0, help_text="Selected volume in liters")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Price per unit at time of purchase")
    added_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        return self.price * self.quantity

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

class VehicleQuery(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField()
    engine_type = models.CharField(max_length=20, blank=True, null=True)
    displacement_cc = models.IntegerField(default=0)
    odometer_km = models.IntegerField(default=0)
    driving_condition = models.CharField(max_length=50, blank=True, null=True)
    typical_trip_length = models.CharField(max_length=50, blank=True, null=True)
    atmosphere_temp = models.CharField(max_length=50, blank=True, null=True)
    budget_preference = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Query for {self.year} {self.brand} {self.model} at {self.created_at}"

class RecommendationFeedback(models.Model):
    query = models.ForeignKey(VehicleQuery, on_delete=models.CASCADE, related_name='feedbacks')
    recommended_oil = models.ForeignKey(Oil, on_delete=models.CASCADE, related_name='recommendations_given')
    selected_oil = models.ForeignKey(Oil, on_delete=models.SET_NULL, null=True, blank=True, related_name='actual_selections')
    is_helpful = models.BooleanField(default=True)
    rating = models.IntegerField(default=5)  # 1 to 5
    comment = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for {self.recommended_oil.brand} - Helper: {self.is_helpful}"

