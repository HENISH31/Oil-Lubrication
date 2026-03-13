from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VehicleViewSet, MaintenanceViewSet, BrandListView

from django.contrib.auth import views as auth_views
from . import views

router = DefaultRouter()
router.register(r'vehicles', views.VehicleViewSet)
router.register(r'maintenance', views.MaintenanceViewSet, basename='maintenance')

urlpatterns = [
    path('', views.home, name='home'),
    path('recommendations/', views.recommendation_page, name='recommendation_page'),
    path('garage/', views.garage, name='garage'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('shop/', views.shop_page, name='shop_page'),
    path('brands/', views.brands_view, name='brands'),
    path('academy/', views.academy, name='academy'),
    path('showcase/', views.showcase, name='showcase'),
    path('education/', views.academy, name='academy'),
    path('login/', auth_views.LoginView.as_view(template_name='oil_logic/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile_page, name='profile_page'),
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:oil_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('api/lookup-plate/', views.lookup_vehicle_by_plate, name='lookup_vehicle_by_plate'),
    path('api/add-by-plate/', views.add_vehicle_by_plate, name='add_vehicle_by_plate'),
    path('api/ai-chat/', views.ai_chat, name='ai_chat'),
    path('api/recommend-ai/', views.AIRecommendationView.as_view(), name='ai-recommend'),
    path('api/feedback/', views.SubmitFeedbackView.as_view(), name='ai-feedback'),
    path('api/', include(router.urls)),
    path('api/brands/', views.BrandListView.as_view(), name='brand-list'),
    path('api/models/', views.ModelListView.as_view(), name='model-list'),
]
