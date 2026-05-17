# Author: HENISHRANA
# Main views for oil logic
from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
import razorpay
import os
from django.utils import timezone
from .models import Oil, Vehicle, Maintenance, UserProfile, CartItem, Order, OrderItem, VehicleRegistration, ServiceRecord, VehicleQuery, RecommendationFeedback, PromoCode
from .ai_engine import AIOilRecommender
recommender = AIOilRecommender()
from .serializers import OilSerializer, VehicleSerializer, MaintenanceSerializer, UserSerializer
from .utils import send_order_confirmation_email
from django.http import JsonResponse
from .services import VehicleLookupService, AIAgentService, GarageLocatorService

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

import json
import requests
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
def home(request):
    return render(request, 'oil_logic/index.html')

def academy(request):
    return render(request, 'oil_logic/academy.html')

def service_locator(request):
    return render(request, 'oil_logic/service_locator.html', {
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY
    })

@login_required
def recommendation_page(request):
    return render(request, 'oil_logic/recommendation.html')

@login_required
def shop_page(request):
    oils = Oil.objects.prefetch_related('variants').all()
    
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

from .forms import CustomRegistrationForm, LocatorForm

def register(request):
    if request.method == 'POST':
        form = CustomRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            # Referral Logic
            referral_code = form.cleaned_data.get('referral_code')
            if referral_code:
                try:
                    referrer_profile = UserProfile.objects.get(referral_code__iexact=referral_code)
                    profile.referred_by = referrer_profile
                    profile.wallet_balance += 50.00
                    profile.save()
                    
                    referrer_profile.wallet_balance += 100.00
                    referrer_profile.save()
                except UserProfile.DoesNotExist:
                    pass
            
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('home')
    else:
        form = CustomRegistrationForm()
    return render(request, 'oil_logic/register.html', {'form': form})

@login_required
def dashboard(request):
    maintenance_records = Maintenance.objects.filter(user=request.user).select_related('vehicle', 'vehicle__recommended_oil')
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Calculate Stats
    total_vehicles = maintenance_records.count()
    service_records = ServiceRecord.objects.filter(maintenance__user=request.user).order_by('-date')
    total_oil_changes = service_records.count()
    
    avg_oil_life = 0
    if total_vehicles > 0:
        totalLife = 0
        for record in maintenance_records:
            # print(record.id) # checking if record comes
            totalInterval = record.next_due_km - record.last_oil_change_km
            if totalInterval > 0:
                consumed = record.current_km - record.last_oil_change_km
                # simple life calc
                life = max(0, min(100, 100 - (consumed / totalInterval * 100)))
                totalLife += life
            else:
                totalLife += 100
        avg_oil_life = totalLife / total_vehicles

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
        # Industrial Predictive Analytics
        r_data['oil_life'] = r.oil_health_score
        r_data['remaining_km'] = max(0, r.next_due_km - r.current_km)
        r_data['predicted_date'] = r.predict_service_date().isoformat()
        r_data['is_overdue'] = r.is_overdue
        
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
        'now': timezone.now(),
        'profile': profile,
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

    def getContextualOilData(self, request, oil, vehicle_type, capacity):
        # Helper to inject prices
        if not oil: return None
        
        # Determine recommended volume
        recVol = 1.0 # Default (Bikes)
        if vehicle_type == 'Car':
            recVol = 4.0
            if capacity and capacity > 4.0:
                recVol = 5.0
        
        # Determine price based on user rules
        sample_oil = oil or Oil.objects.first()
        if sample_oil:
            priceMap = {
                1.0: float(sample_oil.volume_1L_price),
                4.0: float(sample_oil.volume_4L_price),
                5.0: float(sample_oil.volume_5L_price)
            }
        else:
            priceMap = {1.0: 850.00, 4.0: 3200.00, 5.0: 3900.00}
        
        recPrice = priceMap.get(recVol, 850.00)
        
        # Serialize and inject
        data = OilSerializer(oil, context={'request': request}).data
        data['rec_price'] = recPrice
        data['rec_volume'] = recVol
        return data

    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        brand = request.query_params.get('brand')
        model = request.query_params.get('model')
        year_raw = request.query_params.get('year')
        
        # New parameters
        driving_condition = request.query_params.get('driving_condition', 'Mixed')
        mileage_range = request.query_params.get('mileage_range', '0-50k')
        preferred_frequency = request.query_params.get('preferred_frequency', '5-6m')
        vehicle_type = request.query_params.get('vehicle_type', 'Car')

        # 1. Proactive Input Validation
        if not all([brand, model, year_raw]):
            return Response({"error": "Brand, model, and year are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            year = int(year_raw)
        except (ValueError, TypeError):
            return Response({"error": "Field 'year' must be a valid number"}, status=status.HTTP_400_BAD_REQUEST)
        
        vehicles = Vehicle.objects.filter(brand__iexact=brand, model__iexact=model, year=year)
        
        # Global absolute fallback oil (Use a common high-rating synthetic as base)
        global_fallback_oil = Oil.objects.filter(rating__gte=4.5).order_by('-rating').first() or Oil.objects.first()
        
        # fallback logic if no exact vehicle found
        if not vehicles.exists():
            print(f"DEBUG: No exact vehicle found for {brand} {model} {year}. Triggering AI fallback.")
            try:
                from .ai_engine import AIOilRecommender
                ai_recommender = AIOilRecommender()
                
                if not ai_recommender.is_available():
                    print("DEBUG: AI Model not available. Using standard defaults.")
                
                # Map mileage range to odometer_km
                mileage_map = {
                    '0-50k': 25000,
                    '50k-100k': 75000,
                    '100k-150k': 125000,
                    'Above-150k': 175000
                }
                odometer = mileage_map.get(mileage_range, 30000)
                
                # Prepare query for AI
                try:
                    year_int = int(year)
                except (ValueError, TypeError):
                    year_int = 2024 # Fallback to current if invalid
                
                query_data = {
                    'brand': brand,
                    'model': model,
                    'year': year_int,
                    'driving_condition': driving_condition,
                    'odometer_km': odometer,
                    'engine_type': 'Petrol', # Guess if not provided
                    'displacement_cc': 1500 # Guess if not provided
                }
                
                # Get AI recommendation
                best_oil_id, confidence = ai_recommender.predict(query_data)
                print(f"DEBUG: AI Predicted Oil ID: {best_oil_id} with confidence {confidence}")
                
                primary_oil = Oil.objects.filter(id=best_oil_id).first() if best_oil_id else None
                if not primary_oil:
                    # AI failed or returned invalid ID, try matching a standard viscosity
                    target_viscosity = "5W-30" # Standard default
                    primary_oil = Oil.objects.filter(viscosity=target_viscosity).order_by('-rating').first()
                
                if not primary_oil:
                    primary_oil = global_fallback_oil
                
                # Synthesize options
                target_viscosity = primary_oil.viscosity if primary_oil else "5W-30"
                premium_oil = Oil.objects.filter(viscosity=target_viscosity, oil_type='Synthetic').order_by('-price').first()
                economy_oil = Oil.objects.filter(viscosity=target_viscosity, oil_type__in=['Mineral', 'Semi-Synthetic']).order_by('price').first()
                
                # Ensure recommendations are never null
                if not target_viscosity: target_viscosity = "5W-30"
                if not premium_oil: premium_oil = primary_oil
                if not economy_oil: economy_oil = primary_oil

                # Create a virtual vehicle result
                virtual_v = {
                    'id': 0,
                    'brand': brand,
                    'model': model,
                    'year': year,
                    'engine_type': f'{vehicle_type} (AI Optimized)',
                    'displacement_cc': 'Unknown',
                    'variant_name': 'AI Synthesis',
                    'recommendations': {
                        'primary': self.getContextualOilData(request, primary_oil, vehicle_type, 2.0),
                        'premium': self.getContextualOilData(request, premium_oil, vehicle_type, 2.0),
                        'economy': self.getContextualOilData(request, economy_oil, vehicle_type, 2.0),
                    }
                }
                return Response([virtual_v])
            except Exception as e:
                print(f"FATAL RECO ERROR: {str(e)}")
                return Response({"error": "Failed to analyze vehicle data. Please contact support."}, status=500)
            
        data = []
        for v in vehicles:
            v_data = VehicleSerializer(v).data
            
            # --- REFINED LOGIC ---
            v_data['recommendations'] = self._get_refined_recommendations(request, v, driving_condition, mileage_range, preferred_frequency)
            data.append(v_data)

        return Response(data)

    def _get_refined_recommendations(self, request, vehicle, driving_condition, mileage_range, preferred_frequency):
        """Refined hybrid logic for accurate comparisons"""
        base_oil = vehicle.recommended_oil
        target_viscosity = base_oil.viscosity if base_oil else "5W-30"
        target_type = base_oil.oil_type if base_oil else "Synthetic"
        
        # 1. VISCOSITY ADJUSTMENT (Rules)
        if driving_condition == 'Off-road' or mileage_range in ['100k-150k', 'Above-150k']:
            if target_viscosity == "0W-20": target_viscosity = "5W-30"
            elif target_viscosity == "5W-30": target_viscosity = "5W-40"
            elif target_viscosity == "10W-30": target_viscosity = "10W-40"
        
        # 2. OIL TYPE ADJUSTMENT (Rules)
        if preferred_frequency == '12m' or driving_condition in ['City', 'Off-road']:
            target_type = "Synthetic"

        # 3. AI SANITY CHECK
        try:
            query_data = {
                'brand': vehicle.brand,
                'model': vehicle.model,
                'year': vehicle.year,
                'driving_condition': driving_condition,
                'odometer_km': {'0-50k': 25000, '50k-100k': 75000, '100k-150k': 125000, 'Above-150k': 175000}.get(mileage_range, 30000),
                'engine_type': vehicle.engine_type,
                'displacement_cc': vehicle.displacement_cc or 1500
            }
            ai_oil_id, confidence = recommender.predict(query_data)
            if ai_oil_id and confidence > 0.8:
                ai_oil = Oil.objects.filter(id=ai_oil_id).first()
                if ai_oil:
                    # If AI is very confident, use its viscosity but respect our safety bounds
                    target_viscosity = ai_oil.viscosity
        except Exception as e:
            print(f"AI Check failed in refined logic: {e}")

        # 4. SELECT COMPONENT OILS
        # Global absolute fallback
        fallback = Oil.objects.filter(rating__gte=4.5).order_by('-rating').first() or Oil.objects.first()

        # PRIMARY: Best match (respecting adjusted viscosity and type)
        primary = Oil.objects.filter(viscosity=target_viscosity, oil_type=target_type).order_by('-rating').first()
        if not primary:
            primary = Oil.objects.filter(viscosity=target_viscosity).order_by('-rating').first()
        if not primary:
            primary = base_oil or fallback

        # PREMIUM: Top-tier synthetic
        premium = Oil.objects.filter(viscosity=target_viscosity, oil_type='Synthetic').order_by('-price', '-rating').first()
        if not premium or premium.id == primary.id:
            # Try to find a more expensive one even if different viscosity (premium brands)
            premium = Oil.objects.filter(oil_type='Synthetic').order_by('-price').first()
        if not premium:
            premium = primary

        # ECONOMY: Best value
        economy = Oil.objects.filter(viscosity=target_viscosity, oil_type__in=['Mineral', 'Semi-Synthetic']).order_by('price').first()
        if not economy or economy.id == primary.id:
            economy = Oil.objects.filter(oil_type__in=['Mineral', 'Semi-Synthetic']).order_by('price').first()
        if not economy:
            economy = primary

        return {
            'primary': self.getContextualOilData(request, primary, vehicle.vehicle_type, vehicle.oil_capacity),
            'premium': self.getContextualOilData(request, premium, vehicle.vehicle_type, vehicle.oil_capacity),
            'economy': self.getContextualOilData(request, economy, vehicle.vehicle_type, vehicle.oil_capacity),
        }

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
    subtotal = sum(item.total_price() for item in cart_items)
    
    # Promo code logic
    promo_discount = 0
    promo_code_str = request.session.get('promo_code')
    if promo_code_str:
        try:
            promo = PromoCode.objects.get(code=promo_code_str, active=True)
            if promo.is_valid():
                if promo.discount_type == 'Percentage':
                    promo_discount = subtotal * (promo.discount_value / 100)
                else:
                    promo_discount = promo.discount_value
        except PromoCode.DoesNotExist:
            del request.session['promo_code']
            
    total = max(0, subtotal - promo_discount)
    
    return render(request, 'oil_logic/cart.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'promo_discount': promo_discount,
        'promo_code': promo_code_str,
        'total': total
    })

@login_required
def apply_promo_code(request):
    if request.method == 'POST':
        code = request.POST.get('promo_code', '').strip()
        if code:
            try:
                promo = PromoCode.objects.get(code__iexact=code, active=True)
                if promo.is_valid():
                    request.session['promo_code'] = promo.code
                else:
                    # Could add a message framework error here
                    pass
            except PromoCode.DoesNotExist:
                # Invalid code
                pass
        else:
            if 'promo_code' in request.session:
                del request.session['promo_code']
                
    return redirect('cart_view')

@login_required
def checkout_details(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items:
        return redirect('shop_page')
        
    if request.method == 'POST':
        request.session['shipping_name'] = request.POST.get('shipping_name')
        request.session['shipping_phone'] = request.POST.get('shipping_phone')
        request.session['shipping_address'] = request.POST.get('shipping_address')
        request.session['shipping_city'] = request.POST.get('shipping_city')
        request.session['shipping_pincode'] = request.POST.get('shipping_pincode')
        return redirect('checkout')
        
    return render(request, 'oil_logic/checkout_details.html')

@login_required
def remove_from_cart(request, item_id):
    CartItem.objects.filter(id=item_id, user=request.user).delete()
    return redirect('cart_view')

@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items:
        return redirect('shop_page')
    
    subtotal = sum(item.total_price() for item in cart_items)
    
    # Promo code logic
    promo_discount = 0
    promo_code_str = request.session.get('promo_code')
    if promo_code_str:
        try:
            promo = PromoCode.objects.get(code=promo_code_str, active=True)
            if promo.is_valid():
                if promo.discount_type == 'Percentage':
                    promo_discount = subtotal * (promo.discount_value / 100)
                else:
                    promo_discount = promo.discount_value
        except PromoCode.DoesNotExist:
            pass
            
    total_after_promo = max(0, subtotal - promo_discount)

    profile = getattr(request.user, 'profile', None)
    discount = 0
    if profile and profile.wallet_balance > 0:
        discount = min(total_after_promo, profile.wallet_balance)
        
    total = total_after_promo - discount

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    # Initialize Razorpay Order
    payment = None
    error_msg = None
    try:
        if total > 0:
            payment = client.order.create({
                "amount": int(total * 100), # amount in paise
                "currency": "INR",
                "payment_capture": "1"
            })
    except razorpay.errors.BadRequestError:
        error_msg = "Razorpay authentication failed. Please update your RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in settings.py with real Test Keys from your Razorpay Dashboard."
    except Exception as e:
        error_msg = f"Payment Gateway Error: {str(e)}"
    
    context = {
        'payment': payment,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'total': total,
        'subtotal': subtotal,
        'wallet_discount': discount,
        'promo_discount': promo_discount,
        'cart_items': cart_items,
        'error': error_msg
    }
    return render(request, 'oil_logic/payment.html', context)

@csrf_exempt
@login_required
def payment_success(request):
    if request.method == "POST":
        data = request.POST
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': data.get('razorpay_order_id'),
                'razorpay_payment_id': data.get('razorpay_payment_id'),
                'razorpay_signature': data.get('razorpay_signature')
            })
            
            # Payment is successful and authentic, process order
            cart_items = CartItem.objects.filter(user=request.user)
            if not cart_items:
                return redirect('profile_page')
                
            subtotal = sum(item.total_price() for item in cart_items)
            
            promo_discount = 0
            promo_code_str = request.session.get('promo_code')
            if promo_code_str:
                try:
                    promo = PromoCode.objects.get(code=promo_code_str, active=True)
                    if promo.is_valid():
                        if promo.discount_type == 'Percentage':
                            promo_discount = subtotal * (promo.discount_value / 100)
                        else:
                            promo_discount = promo.discount_value
                except PromoCode.DoesNotExist:
                    pass
                    
            total_after_promo = max(0, subtotal - promo_discount)

            profile = getattr(request.user, 'profile', None)
            wallet_discount = 0
            if profile and profile.wallet_balance > 0:
                wallet_discount = min(total_after_promo, profile.wallet_balance)
                profile.wallet_balance -= wallet_discount
                profile.save()
                
            final_total = total_after_promo - wallet_discount
                
            order = Order.objects.create(
                user=request.user, 
                total_price=final_total, 
                is_paid=True,
                shipping_name=request.session.get('shipping_name'),
                shipping_phone=request.session.get('shipping_phone'),
                shipping_address=request.session.get('shipping_address'),
                shipping_city=request.session.get('shipping_city'),
                shipping_pincode=request.session.get('shipping_pincode')
            )
            
            # Clear session
            for key in ['promo_code', 'shipping_name', 'shipping_phone', 'shipping_address', 'shipping_city', 'shipping_pincode']:
                if key in request.session:
                    del request.session[key]
            
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    oil=item.oil,
                    quantity=item.quantity,
                    price_at_purchase=item.price
                )
            
            cart_items.delete()
            
            # Send Email Notification
            send_order_confirmation_email(request, order)
            
            return redirect('profile_page')
            
        except razorpay.errors.SignatureVerificationError:
            return render(request, 'oil_logic/payment.html', {'error': 'Payment Verification Failed'})
            
    return redirect('cart_view')

@login_required
def simulate_payment(request):
    """
    Temporary view to bypass Razorpay and simulate a successful payment.
    """
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items:
        return redirect('shop_page')
        
    subtotal = sum(item.total_price() for item in cart_items)
    
    promo_discount = 0
    promo_code_str = request.session.get('promo_code')
    if promo_code_str:
        try:
            promo = PromoCode.objects.get(code=promo_code_str, active=True)
            if promo.is_valid():
                if promo.discount_type == 'Percentage':
                    promo_discount = subtotal * (promo.discount_value / 100)
                else:
                    promo_discount = promo.discount_value
        except PromoCode.DoesNotExist:
            pass
            
    total_after_promo = max(0, subtotal - promo_discount)

    profile = getattr(request.user, 'profile', None)
    wallet_discount = 0
    if profile and profile.wallet_balance > 0:
        wallet_discount = min(total_after_promo, profile.wallet_balance)
        profile.wallet_balance -= wallet_discount
        profile.save()
        
    final_total = total_after_promo - wallet_discount
    
    # Create Order
    order = Order.objects.create(
        user=request.user, 
        total_price=final_total, 
        is_paid=True,
        shipping_name=request.session.get('shipping_name'),
        shipping_phone=request.session.get('shipping_phone'),
        shipping_address=request.session.get('shipping_address'),
        shipping_city=request.session.get('shipping_city'),
        shipping_pincode=request.session.get('shipping_pincode')
    )
    
    # Clear session
    for key in ['promo_code', 'shipping_name', 'shipping_phone', 'shipping_address', 'shipping_city', 'shipping_pincode']:
        if key in request.session:
            del request.session[key]
    
    # Create OrderItems
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            oil=item.oil,
            quantity=item.quantity,
            price_at_purchase=item.price
        )
    
    # Clear Cart
    cart_items.delete()
    
    # Send Email Notification
    send_order_confirmation_email(request, order)
    
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
            'brand': api_data.get('brand'),
            'model': api_data.get('model'),
            'year': api_data.get('year'),
            'vehicle_type': api_data.get('type', 'Car'),
            'engine_type': api_data.get('engine_type', 'Petrol'),
            'puc_expiry': api_data.get('puc_expiry'),
            'registration_date': api_data.get('reg_date'),
            'owner_name': api_data.get('owner_name'),
            'source': 'API' if api_data.get('is_real') else 'Simulator'
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

        # If it's a new vehicle from API, we might not have a vehicle_id yet
        if not vehicle_id:
            # Try to get or create the base Vehicle object
            brand = data.get('brand')
            model = data.get('model')
            year = int(data.get('year', 2020))
            engine_type = data.get('engine_type', 'Petrol')
            
            # Use rules to find a matching vehicle or create a generic one
            vehicle, created = Vehicle.objects.get_or_create(
                brand=brand, 
                model=model, 
                year=year,
                engine_type=engine_type,
                defaults={'vehicle_type': 'Car', 'oil_capacity': 4.0}
            )
        else:
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
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            
            if not user_message:
                return JsonResponse({'status': 'error', 'message': 'Message is empty'}, status=400)
                
            response_text = AIAgentService.get_response(user_message, request.user)
            return JsonResponse({'status': 'success', 'response': response_text})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON body'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

# AIRecommendationView uses the globally initialized 'recommender'
class AIRecommendationView(generics.GenericAPIView):
    def post(self, request):
        data = request.data
        brand = data.get('brand')
        model = data.get('model')
        year = data.get('year')
        
        if not all([brand, model, year]):
            return Response({"error": "Missing vehicle identification"}, status=400)

        # Log the query
        query = VehicleQuery.objects.create(
            user=request.user if request.user.is_authenticated else None,
            brand=brand,
            model=model,
            year=year,
            engine_type=data.get('engine_type'),
            displacement_cc=data.get('displacement_cc', 0),
            odometer_km=data.get('odometer_km', 0),
            driving_condition=data.get('driving_condition'),
            typical_trip_length=data.get('typical_trip_length'),
            atmosphere_temp=data.get('atmosphere_temp'),
            budget_preference=data.get('budget_preference')
        )

        # AI Prediction
        oil_id, confidence = recommender.predict(data)
        
        # Hybrid Fallback Logic
        use_ai = recommender.is_available() and confidence > 0.6
        explanation = ""
        ai_verdict = ""
        
        if use_ai:
            primary_oil = Oil.objects.filter(id=oil_id).first()
            if primary_oil:
                alternatives = recommender.predict_with_alternatives(data, top_n=3)
                alternative_oils = Oil.objects.filter(id__in=[a['oil_id'] for a in alternatives])
                explanation = recommender.get_explanation(data, primary_oil)
                # LLM Consultation
                oil_ctx = {"brand": primary_oil.brand, "viscosity": primary_oil.viscosity, "oil_type": primary_oil.oil_type}
                ai_verdict = AIAgentService.analyze_recommendation(data, oil_ctx)
            else:
                use_ai = False 
        else:
            # Fallback to rule-based logic
            vehicles = Vehicle.objects.filter(brand__iexact=brand, model__iexact=model, year=year)
            if vehicles.exists():
                v = vehicles.first()
                primary_oil = v.recommended_oil
                alternative_oils = Oil.objects.filter(viscosity=primary_oil.viscosity).exclude(id=primary_oil.id)[:2] if primary_oil else []
                explanation = "Matched with manufacturer specs."
                if primary_oil:
                    oil_ctx = {"brand": primary_oil.brand, "viscosity": primary_oil.viscosity, "oil_type": primary_oil.oil_type}
                    ai_verdict = AIAgentService.analyze_recommendation(data, oil_ctx)
            else:
                primary_oil = Oil.objects.order_by('-rating').first()
                alternative_oils = []
                explanation = "Top-rated versatile oil recommendation."
                ai_verdict = "General-purpose high-performance oil suitable for most modern engines."

        # Log initial recommendation
        if primary_oil:
            RecommendationFeedback.objects.create(
                query=query,
                recommended_oil=primary_oil,
                is_helpful=True
            )

        return Response({
            "query_id": query.id,
            "recommendation": OilSerializer(primary_oil, context={'request': request}).data if primary_oil else None,
            "alternatives": OilSerializer(alternative_oils, many=True, context={'request': request}).data,
            "explanation": explanation,
            "ai_verdict": ai_verdict,
            "system": "AI (Hybrid)" if use_ai else "Rule-based + Expert AI",
            "confidence": round(confidence, 2)
        })

class SubmitFeedbackView(generics.GenericAPIView):
    def post(self, request):
        query_id = request.data.get('query_id')
        selected_oil_id = request.data.get('selected_oil_id')
        rating = request.data.get('rating', 5)
        comment = request.data.get('comment', "")
        
        try:
            query = VehicleQuery.objects.get(id=query_id)
            # Find the feedback record created during recommendation
            feedback = RecommendationFeedback.objects.filter(query=query).first()
            if feedback:
                if selected_oil_id:
                    feedback.selected_oil_id = selected_oil_id
                feedback.rating = rating
                feedback.comment = comment
                feedback.is_helpful = (rating >= 3)
                feedback.save()
                return Response({"status": "success"})
        except VehicleQuery.DoesNotExist:
            pass
            
        return Response({"status": "error", "message": "Query not found"}, status=404)

def search_garages(request):
    query = request.GET.get('q')
    lat = request.GET.get('lat') # From geolocation
    lng = request.GET.get('lng') # From geolocation

    if not query and not (lat and lng):
        return JsonResponse({'status': 'error', 'message': 'Search term or location required'}, status=400)
    
    results = GarageLocatorService.search_best_garages(query, lat, lng)
    return JsonResponse({
        'status': 'success',
        'results': results
    })

@staff_member_required
def ai_dashboard(request):
    return render(request, 'oil_logic/ai_dashboard.html')

@staff_member_required
def get_model_metrics(request):
    import json
    metrics_path = os.path.join(settings.BASE_DIR, 'ml_models', 'metrics.json')
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            data = json.load(f)
        return JsonResponse(data)
    return JsonResponse({'error': 'Metrics not found'}, status=404)

@staff_member_required
def get_dataset_stats(request):
    from django.db.models import Count
    # Feedback distribution
    feedbacks = RecommendationFeedback.objects.filter(is_helpful=True)
    brand_dist = feedbacks.values('query__brand').annotate(count=Count('id')).order_by('-count')[:10]
    oil_dist = feedbacks.values('recommended_oil__brand', 'recommended_oil__viscosity').annotate(count=Count('id')).order_by('-count')[:10]
    
    return JsonResponse({
        'brand_distribution': list(brand_dist),
        'oil_distribution': list(oil_dist),
        'total_samples': feedbacks.count()
    })



from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from .models import OilVariant

@staff_member_required
def admin_dashboard(request):
    # Total Revenue (All Paid Orders)
    total_revenue = Order.objects.filter(is_paid=True).aggregate(Sum('total_price'))['total_price__sum'] or 0

    # Orders Status Distribution
    status_distribution = Order.objects.values('status').annotate(count=Count('id'))
    status_labels = [item['status'] for item in status_distribution]
    status_counts = [item['count'] for item in status_distribution]

    # Top Selling Oils
    top_oils = OrderItem.objects.values('oil__brand', 'oil__viscosity').annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')[:5]
    
    oil_labels = [f"{item['oil__brand']} {item['oil__viscosity']}" for item in top_oils]
    oil_sales = [item['total_sold'] for item in top_oils]

    # Revenue by Month
    revenue_by_month = Order.objects.filter(is_paid=True).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        revenue=Sum('total_price')
    ).order_by('month')
    
    month_labels = [item['month'].strftime('%b %Y') for item in revenue_by_month if item['month']]
    month_revenues = [float(item['revenue']) for item in revenue_by_month]

    context = {
        'total_revenue': total_revenue,
        'status_labels': json.dumps(status_labels),
        'status_counts': json.dumps(status_counts),
        'oil_labels': json.dumps(oil_labels),
        'oil_sales': json.dumps(oil_sales),
        'month_labels': json.dumps(month_labels),
        'month_revenues': json.dumps(month_revenues),
        'recent_orders': Order.objects.order_by('-created_at')[:10],
        'low_stock_oils': Oil.objects.filter(stock_count__lt=10),
        'low_stock_variants': OilVariant.objects.filter(stock_count__lt=10)
    }
    return render(request, 'oil_logic/admin_dashboard.html', context)
    
