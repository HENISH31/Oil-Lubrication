from django.contrib import admin
from .models import Oil, Vehicle, Maintenance, VehicleRegistration, OilVariant, CartItem

@admin.register(Oil)
class OilAdmin(admin.ModelAdmin):
    list_display = ('brand', 'viscosity', 'oil_type', 'volume_1L_price', 'volume_4L_price', 'volume_5L_price')
    list_filter = ('brand', 'oil_type')
    search_fields = ('brand', 'viscosity')
    fieldsets = (
        ('Basic Information', {'fields': ('brand', 'viscosity', 'oil_type', 'vehicle_type')}),
        ('Pricing by Volume', {'fields': ('volume_1L_price', 'volume_4L_price', 'volume_5L_price', 'price', 'volume_liters')}),
        ('Specifications', {'fields': ('api_rating', 'jaso_rating', 'change_interval_km', 'change_interval_months')}),
        ('Media & Description', {'fields': ('image', 'image_url', 'description')}),
        ('Stock & Rating', {'fields': ('stock_count', 'rating')}),
    )

@admin.register(OilVariant)
class OilVariantAdmin(admin.ModelAdmin):
    list_display = ('oil', 'volume_liters', 'price', 'stock_count', 'image')
    list_filter = ('volume_liters', 'oil__brand')
    search_fields = ('oil__brand', 'oil__viscosity')

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'oil', 'volume_liters', 'price', 'quantity', 'added_at')
    list_filter = ('added_at', 'user')
    search_fields = ('user__username', 'oil__brand')
    readonly_fields = ('added_at',)

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
