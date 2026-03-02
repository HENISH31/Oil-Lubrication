from django.contrib import admin
from .models import Oil, Vehicle, Maintenance, VehicleRegistration

@admin.register(Oil)
class OilAdmin(admin.ModelAdmin):
    list_display = ('brand', 'viscosity', 'oil_type', 'api_rating', 'jaso_rating', 'change_interval_km')
    list_filter = ('brand', 'oil_type')
    search_fields = ('brand', 'viscosity')

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('year', 'brand', 'model', 'vehicle_type', 'engine_type', 'recommended_oil')
    list_filter = ('vehicle_type', 'brand', 'engine_type')
    search_fields = ('brand', 'model')

@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'vehicle', 'last_oil_change_km', 'next_due_km', 'next_due_date')
    list_filter = ('user', 'vehicle__vehicle_type')
    readonly_fields = ('next_due_km', 'next_due_date')

class VehicleRegistrationAdmin(admin.ModelAdmin):
    list_display = ('license_plate', 'vehicle', 'owner_name', 'puc_expiry', 'registration_date')
    search_fields = ('license_plate', 'owner_name')
    list_filter = ('vehicle__brand', 'vehicle__vehicle_type')

admin.site.register(VehicleRegistration, VehicleRegistrationAdmin)
