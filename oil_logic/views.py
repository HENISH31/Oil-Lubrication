from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Oil, Vehicle, Maintenance, UserProfile, CartItem, Order, OrderItem, VehicleRegistration, ServiceRecord
from .serializers import OilSerializer, VehicleSerializer, MaintenanceSerializer, UserSerializer
from django.http import JsonResponse
from django.utils import timezone
from .services import VehicleLookupService, AIAgentService

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required

# NOTE: Vehicle and Maintenance already imported above with other models

import json
import requests
from django.conf import settings


def home(request):
    return render(request, 'oil_logic/index.html')

def academy(request):
    return render(request, 'oil_logic/academy.html')

def showcase(request):
    return render(request, 'oil_logic/showcase.html')

@login_required
def recommendation_page(request):
    return render(request, 'oil_logic/recommendation.html')

@login_required
def shop_page(request):
    oils = Oil.objects.all()
    
    # Filtering
    brands = request.GET.getlist('brand')
    if brands:
        oils = oils.filter(brand__in=brands)
        
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        oils = oils.filter(price__gte=min_price)
    if max_price:
        oils = oils.filter(price__lte=max_price)
        
    grades = request.GET.getlist('grade')
    if grades:
        oils = oils.filter(viscosity__in=grades)
        
    volumes = request.GET.getlist('volume')
    if volumes:
        oils = oils.filter(volume_liters__in=volumes)
        
    vehicle_types = request.GET.getlist('vehicle_type')
    if vehicle_types:
        oils = oils.filter(vehicle_type__in=vehicle_types)

    # Sorting
    sort = request.GET.get('sort', 'newest')
    if sort == 'price_low':
        oils = oils.order_by('price')
    elif sort == 'price_high':
        oils = oils.order_by('-price')
    elif sort == 'top_rated':
        oils = oils.order_by('-rating')
    else: # newest
        oils = oils.order_by('-id')

    # Get distinct values for filters
    all_brands = Oil.objects.values_list('brand', flat=True).distinct().order_by('brand')
    brand_counts = {brand: Oil.objects.filter(brand=brand).count() for brand in all_brands}
    
    # dynamic options derived from oils only
    brand_options = [b for b in all_brands if b and '{{' not in str(b) and '}}' not in str(b)]
    brand_options.sort()
    
    return render(request, 'oil_logic/shop.html', {
        'oils': oils,
        'total_oils': Oil.objects.count(),
        'brand_counts': brand_counts,
        'selected_brands': brands,
        'selected_grades': grades,
        'selected_volumes': [str(v) for v in volumes],  # ensure string comparison
        'selected_vehicle_types': vehicle_types,
        'min_price': min_price or 200,
        'max_price': max_price or 2000,
        'current_sort': sort,
        # dynamic filter options
        'brand_options': brand_options,
        'grade_options': ['0W-20', '5W-30', '10W-40', '15W-50'],
        'volume_options': ['1', '4', '5'],
        'vehicle_type_options': ['Car', 'Bike', 'Scooter', 'Truck'],
    })

from .forms import CustomRegistrationForm

def brands_view(request):
    # Query distinct brand names from the Oil model
    brands = Oil.objects.values_list('brand', flat=True).distinct().order_by('brand')
    return render(request, 'oil_logic/brands.html', {'brands': brands})

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
    
    # Calculate Stats
    total_vehicles = maintenance_records.count()
    service_records = ServiceRecord.objects.filter(maintenance__user=request.user).order_by('-date')
    total_oil_changes = service_records.count()
    
    avg_oil_life = 0
    if total_vehicles > 0:
        total_life = 0
        for record in maintenance_records:
            total_interval = record.next_due_km - record.last_oil_change_km
            if total_interval > 0:
                consumed = record.current_km - record.last_oil_change_km
                life = max(0, min(100, 100 - (consumed / total_interval * 100)))
                total_life += life
            else:
                total_life += 100
        avg_oil_life = total_life / total_vehicles

    # Expert Tips (Serialized for JS)
    expert_tips_list = [
        "Synthetic oil usually lasts longer than mineral oil, typically 10,000-15,000 KM.",
        "Check your oil level every two weeks to prevent engine damage.",
        "Dark oil doesn't always mean it's dirty; it's just doing its job of cleaning the engine.",
        "Piston rings can wear out faster if oil changes are neglected."
    ]
    expert_tips = json.dumps(expert_tips_list)
    
    # Serialize for Three.js
    records_data = []
    for r in maintenance_records:
        r_data = MaintenanceSerializer(r).data
        # Add calculated fields for frontend
        total_interval = r.next_due_km - r.last_oil_change_km
        if total_interval > 0:
            consumed = r.current_km - r.last_oil_change_km
            r_data['oil_life'] = max(0, min(100, 100 - (consumed / total_interval * 100)))
            r_data['remaining_km'] = max(0, r.next_due_km - r.current_km)
        else:
            r_data['oil_life'] = 100
            r_data['remaining_km'] = 5000 # default
        records_data.append(r_data)
        
    records_json = json.dumps(records_data)
    
    return render(request, 'oil_logic/dashboard.html', {
        'maintenance_records': maintenance_records,
        'records_json': records_json,
        'total_vehicles': total_vehicles,
        'total_oil_changes': total_oil_changes,
        'avg_oil_life': round(avg_oil_life),
        'service_history': service_records[:10], # Last 10 records
        'expert_tips': expert_tips,
        'expert_tips_list': expert_tips_list,
        'now': timezone.now()
    })

@login_required
def garage(request):
    maintenance_records = Maintenance.objects.filter(user=request.user).select_related('vehicle', 'vehicle__recommended_oil')
    total_vehicles = maintenance_records.count()
    
    return render(request, 'oil_logic/garage.html', {
        'maintenance_records': maintenance_records,
        'total_vehicles': total_vehicles,
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
        
        # New parameters
        driving_condition = request.query_params.get('driving_condition', 'Mixed')
        mileage_range = request.query_params.get('mileage_range', '0-50k')
        preferred_frequency = request.query_params.get('preferred_frequency', '5-6m')

        if not all([brand, model, year]):
            return Response({"error": "Brand, model, and year are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        vehicles = Vehicle.objects.filter(brand__iexact=brand, model__iexact=model, year=year)
        if not vehicles.exists():
            return Response({"error": "Vehicle not found"}, status=status.HTTP_404_NOT_FOUND)
            
        data = []
        for v in vehicles:
            v_data = VehicleSerializer(v).data
            
            # Logic for Primary Oil selection (Best match)
            base_oil = v.recommended_oil
            target_viscosity = base_oil.viscosity if base_oil else "5W-30"
            target_type = base_oil.oil_type if base_oil else "Synthetic"

            # Adjustments based on inputs
            if driving_condition == 'Off-road' or mileage_range in ['100k-150k', 'Above-150k']:
                # Nudge towards thicker oil if possible (simple heuristic for this system)
                if target_viscosity == "0W-20": target_viscosity = "5W-30"
                elif target_viscosity == "5W-30": target_viscosity = "5W-40"
                elif target_viscosity == "10W-30": target_viscosity = "10W-40"

            if preferred_frequency == '12m':
                target_type = "Synthetic"

            # 1. Primary Oil (The refined recommendation)
            primary_oil = Oil.objects.filter(viscosity=target_viscosity).order_by('-rating').first()
            if not primary_oil: primary_oil = base_oil

            # 2. Premium Oil (Highest price/rating Synthetic)
            # Exclude primary oil to ensure variety
            premium_oil = Oil.objects.filter(viscosity=target_viscosity, oil_type='Synthetic')
            if primary_oil:
                premium_oil = premium_oil.exclude(id=primary_oil.id)
            premium_oil = premium_oil.order_by('-price').first()
            if not premium_oil: premium_oil = primary_oil

            # 3. Economy Oil (Lowest price Mineral/Semi-Synthetic)
            # Exclude primary and premium oils to ensure variety
            economy_oil = Oil.objects.filter(viscosity=target_viscosity, oil_type__in=['Mineral', 'Semi-Synthetic'])
            exclude_ids = []
            if primary_oil: exclude_ids.append(primary_oil.id)
            if premium_oil: exclude_ids.append(premium_oil.id)
            
            economy_oil = economy_oil.exclude(id__in=exclude_ids)
            economy_oil = economy_oil.order_by('price').first()
            
            if not economy_oil:
                # If still nothing, try any oil of that viscosity that isn't already picked
                economy_oil = Oil.objects.filter(viscosity=target_viscosity).exclude(id__in=exclude_ids).order_by('price').first()
            if not economy_oil: economy_oil = primary_oil

            v_data['recommendations'] = {
                'primary': OilSerializer(primary_oil).data if primary_oil else None,
                'premium': OilSerializer(premium_oil).data if premium_oil else None,
                'economy': OilSerializer(economy_oil).data if economy_oil else None,
            }
            data.append(v_data)

        return Response(data)

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
        
        # Extract volume and price from request body
        try:
            import json
            data = json.loads(request.body) if request.body else {}
            volume = float(data.get('volume', 1.0))
            price = float(data.get('price', oil.price))
        except:
            volume = 1.0
            price = float(oil.price)
        
        # Check if item with same volume already exists
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user, 
            oil=oil, 
            volume_liters=volume,
            defaults={'price': price}
        )
        
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
