from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Oil, Vehicle, Maintenance, UserProfile, CartItem, Order, OrderItem, VehicleRegistration
from .serializers import OilSerializer, VehicleSerializer, MaintenanceSerializer, UserSerializer
from django.http import JsonResponse
from django.utils import timezone
from .services import VehicleLookupService

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .models import Vehicle, Maintenance

import json
import requests
from django.conf import settings


def home(request):
    return render(request, 'oil_logic/index.html')

def academy(request):
    return render(request, 'oil_logic/academy.html')

@login_required
def recommendation_page(request):
    return render(request, 'oil_logic/recommendation.html')

@login_required
def shop_page(request):
    oils = Oil.objects.all().order_by('brand')
    return render(request, 'oil_logic/shop.html', {'oils': oils})

from .forms import CustomRegistrationForm

def register(request):
    if request.method == 'POST':
        form = CustomRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.get_or_create(user=user)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('dashboard')
    else:
        form = CustomRegistrationForm()
    return render(request, 'oil_logic/register.html', {'form': form})

@login_required
def dashboard(request):
    maintenance_records = Maintenance.objects.filter(user=request.user).select_related('vehicle', 'vehicle__recommended_oil')
    return render(request, 'oil_logic/dashboard.html', {
        'maintenance_records': maintenance_records,
        'now': timezone.now()
    })

# ─── API ViewSets ─────────────────────────────────────────────────────────────

class VehicleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer

    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        brand = request.query_params.get('brand')
        model = request.query_params.get('model')
        year = request.query_params.get('year')
        
        if not all([brand, model, year]):
            return Response({"error": "Brand, model, and year are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        vehicles = Vehicle.objects.filter(brand__iexact=brand, model__iexact=model, year=year)
        if not vehicles.exists():
            return Response({"error": "Vehicle not found"}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = self.get_serializer(vehicles, many=True)
        return Response(serializer.data)

class MaintenanceViewSet(viewsets.ModelViewSet):
    serializer_class = MaintenanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Maintenance.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BrandListView(generics.ListAPIView):
    def list(self, request, *args, **kwargs):
        vehicle_type = request.query_params.get('vehicle_type')
        queryset = Vehicle.objects.all()
        if vehicle_type:
            queryset = queryset.filter(vehicle_type__iexact=vehicle_type)
        brands = queryset.values_list('brand', flat=True).distinct()
        return Response(brands)

class ModelListView(generics.ListAPIView):
    def list(self, request, *args, **kwargs):
        brand = request.query_params.get('brand')
        if not brand:
            return Response([])
        models = Vehicle.objects.filter(brand__iexact=brand).values_list('model', flat=True).distinct()
        return Response(models)

# ─── Profile & Cart ───────────────────────────────────────────────────────────

@login_required
def profile_page(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'oil_logic/profile.html', {
        'profile': profile,
        'orders': orders,
    })


@login_required
def add_to_cart(request, oil_id):
    if request.method == 'POST':
        oil = Oil.objects.get(id=oil_id)
        cart_item, created = CartItem.objects.get_or_create(user=request.user, oil=oil)
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        
        cart_count = CartItem.objects.filter(user=request.user).count()
        return JsonResponse({'status': 'success', 'cart_count': cart_count})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.total_price() for item in cart_items)
    return render(request, 'oil_logic/cart.html', {
        'cart_items': cart_items,
        'total': total
    })

@login_required
def remove_from_cart(request, item_id):
    cart_item = CartItem.objects.get(id=item_id, user=request.user)
    cart_item.delete()
    return redirect('cart_view')

@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items:
        return redirect('shop_page')
    
    total = sum(item.total_price() for item in cart_items)
    order = Order.objects.create(user=request.user, total_price=total, is_paid=True)
    
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            oil=item.oil,
            quantity=item.quantity,
            price_at_purchase=item.oil.price
        )
    
    cart_items.delete()
    return redirect('profile_page')

@login_required
def lookup_vehicle_by_plate(request):
    license_plate = request.GET.get('plate')
    if not license_plate:
        return JsonResponse({'status': 'error', 'message': 'License plate is required'}, status=400)
    
    # 1. Try real API via service
    api_data = VehicleLookupService.lookup_by_plate(license_plate)
    if api_data:
        return JsonResponse({
            'status': 'success',
            'brand': api_data.get('brand', 'Unknown'),
            'model': api_data.get('model', 'Unknown'),
            'year': api_data.get('year', 2024),
            'vehicle_type': api_data.get('type', 'Car'),
            'puc_expiry': api_data.get('puc_expiry', timezone.now().date().strftime('%Y-%m-%d')),
            'registration_date': api_data.get('reg_date', timezone.now().date().strftime('%Y-%m-%d')),
        })

    # 2. Fallback to local registry
    try:
        reg = VehicleRegistration.objects.select_related('vehicle').get(license_plate__iexact=license_plate)
        data = {
            'status': 'success',
            'brand': reg.vehicle.brand,
            'model': reg.vehicle.model,
            'year': reg.vehicle.year,
            'vehicle_type': reg.vehicle.vehicle_type,
            'engine_type': reg.vehicle.engine_type,
            'puc_expiry': reg.puc_expiry.strftime('%Y-%m-%d'),
            'registration_date': reg.registration_date.strftime('%Y-%m-%d'),
            'vehicle_id': reg.vehicle.id,
            'owner_name': reg.owner_name or "Unknown Owner"
        }
        return JsonResponse(data)
    except VehicleRegistration.DoesNotExist:
        return JsonResponse({'status': 'not_found', 'message': 'Vehicle not found in registry'})

@login_required
def add_vehicle_by_plate(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        license_plate = data.get('plate')
        vehicle_id = data.get('vehicle_id')
        puc_expiry = data.get('puc_expiry')

        vehicle = Vehicle.objects.get(id=vehicle_id)
        
        if Maintenance.objects.filter(user=request.user, license_plate=license_plate).exists():
            return JsonResponse({'status': 'error', 'message': 'Vehicle already in your garage'})

        Maintenance.objects.create(
            user=request.user,
            vehicle=vehicle,
            license_plate=license_plate,
            puc_expiry=puc_expiry,
            last_oil_change_km=0,
            last_oil_change_date=timezone.now().date()
        )
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def ai_chat(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message', '')
        
        if not user_message:
            return JsonResponse({'status': 'error', 'message': 'Message is empty'}, status=400)
            
        response_text = AIAgentService.get_response(user_message, request.user)
        
        return JsonResponse({
            'status': 'success',
            'response': response_text
        })
    return JsonResponse({'status': 'error'}, status=400)
