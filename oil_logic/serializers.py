from rest_framework import serializers
from .models import Oil, Vehicle, Maintenance
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class OilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Oil
        fields = '__all__'

class VehicleSerializer(serializers.ModelSerializer):
    recommended_oil_details = OilSerializer(source='recommended_oil', read_only=True)
    
    class Meta:
        model = Vehicle
        fields = ['id', 'vehicle_type', 'brand', 'model', 'variant_name', 'year', 'engine_type', 'displacement_cc', 'oil_capacity', 'recommended_oil', 'recommended_oil_details']

class MaintenanceSerializer(serializers.ModelSerializer):
    vehicle_details = VehicleSerializer(source='vehicle', read_only=True)
    is_overdue = serializers.ReadOnlyField()

    class Meta:
        model = Maintenance
        fields = '__all__'
