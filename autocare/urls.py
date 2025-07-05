from django.urls import path
from .views import HomeView, PricingView, RegisterView, VersionesView, CeroView, ProfileView, VehicleListView, AddServiceView, ServicesView, VehicleServiceListView, VehicleDetailView, VehicleDeleteView
from autocare.views import CustomLoginView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('pricing/', PricingView.as_view(), name='pricing'),
    path('vehicles/', VehicleListView.as_view(), name='vehicle_list'),
    path('vehicles/<int:pk>/', VehicleDetailView.as_view(), name='vehicle_detail'),
    path('vehicles/<int:pk>/crear-servicio', AddServiceView.as_view(), name='add_service'),
    path('register/', RegisterView.as_view(), name='register'),
    path('versiones/', VersionesView.as_view(), name='versiones'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('servicelist/', ServicesView.as_view(), name='servicelist'),
    path('vehicles/<int:pk>/delete/', VehicleDeleteView.as_view(), name='vehicle_delete'),
    path('login/', CustomLoginView.as_view(), name='login'),
]
