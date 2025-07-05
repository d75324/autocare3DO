from django.contrib import admin
from .models import Vehicle, Service
from .forms import VehicleForm

#voy a crear las clases para ver Vehicle y Service desde el admin

class VehicleBE(admin.ModelAdmin):
    form = VehicleForm
    list_display = (
        'created_at',
        'owner',
        'plate',
        'brand',
        'moddel',
        'year',
        'mileage',
        'color',
        'car_mechanic',
    )
    search_fields = (
		'created_at',
		'plate',
		'car_mechanic',
    )

admin.site.register(Vehicle, VehicleBE)

class ServiceBE(admin.ModelAdmin):
	list_display = (
        'vehicle',
        'date',
        'kilometers',
        'service_type',
        'coments',
        'cost',
    )
	search_fields = (
		'vehicle',
		'date',
		'service_type',
    )

admin.site.register(Service, ServiceBE)
