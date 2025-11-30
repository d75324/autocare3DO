from django.db import models
from django.utils import timezone
from django.contrib import admin
from django.contrib.auth.models import User
import datetime

# tipos de usuarios que se pueden registrar
USER_TYPE_CHOICES = [

	('Standard', 'Standard'),
    ('Pro', 'Pro'),

]

# Todas las marcas de autos disponibles. 
BRAND_CHOICES = [
        ('Audi', 'Audi'),
        ('BMW', 'BMW'),
        ('BYD', 'BYD'),
        ('Changan', 'Changan'),
        ('Chery', 'Chery'),
        ('Chevrolet', 'Chevrolet'),
        ('Citroen', 'Citroen'),
        ('DFSK', 'DFSK'),
        ('Dodge', 'Dodge'),
        ('Faw', 'Faw'),
        ('Fiat', 'Fiat'),
        ('Ford', 'Ford'),
        ('Geely', 'Geely'),        
        ('Haima', 'Haima'),
        ('Haval', 'Haval'),
        ('Honda', 'Honda'),
        ('Hyundai', 'Hyundai'),
        ('Jeep', 'Jeep'),
        ('Jetour', 'Jetour'),
        ('JMC', 'JMC'),
        ('Kia', 'Kia'),
        ('Land Rover', 'Land Rover'),
        ('Mazda', 'Mazda'),
        ('Mercedes Benz', 'Mercedes Benz'),
        ('Mitsubishi', 'Mitsubishi'),
        ('Nizzan', 'Nizzan'),
        ('Peugeot', 'Peugeot'),
        ('Renault', 'Renault'),
        ('Seat', 'Seat'),
        ('Subaru', 'Subaru'),
        ('Toyota', 'Toyota'),
        ('Volvo', 'Volvo'),
        ('VW', 'VW'),
        ('Zuzuki', 'Zuzuki'),
]

# todos los servicios que se le pueden hacer a un auto
SERVICE_TYPE_CHOICES = [

('Filtro de aire', 'Filtro de aire'),
('Filtro de aceite', 'Filtro de aceite'),
('Cambio aceite', 'Cambio aceite'),
('Cambio pastillas de freno', 'Cambio pastillas de freno'),
('Filtro de combustible', 'Filtro de combustible'),
('Cambio de lubricación de transmisión', 'Cambio de lubricación de transmisión'),
('Cambio Correa de Distribución ', 'Cambio Correa de Distribución'),
('Cambio de amortiguadores', 'Cambio de amortiguadores'),
('Cambio de cubiertas', 'Cambio de cubiertas'),
('Cambio de batería', 'Cambio de batería'),
('Carga Combustible', 'Carga Combustible'),
('Chapista', 'Chapista'),
('Tren delantero', 'Tren delantero'),
('Electricidad', 'Electricidad'),
('Carga Nafta', 'Carga Nafta'),
('Pinchadura', 'Pinchadura'),
('Me hizo un ruido', 'Me hizo un ruido'),
('Cualquier otra cosa', 'Cualquier otra cosa'),

]

class Vehicle(models.Model):

    def current_year():
        return datetime.date.today().year
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Titular', related_name='vehicle_owner')
    plate = models.CharField(max_length=10, verbose_name='Patente')
    brand = models.CharField(max_length=50, choices=BRAND_CHOICES, verbose_name='Marca')
    moddel = models.CharField(max_length=50, verbose_name='Modelo')
    year = models.IntegerField(default=current_year, verbose_name='Año')
    color = models.CharField(max_length=50, verbose_name='Color')
    mileage = models.IntegerField(verbose_name='Kilometraje')
    car_mechanic = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, verbose_name='Mecánico Asignado', related_name='assigned_mechanic')
    created_at = models.DateField(auto_now_add=True, verbose_name='Fecha Creación')
    
    def __str__(self):
        return self.plate
    
    def save(self, *args, **kwargs):
        self.plate = self.plate.upper()
        super().save(*args, **kwargs)

    def total_service_cost(self):
        from django.db.models import Sum
        return self.service_set.aggregate(total_cost=Sum('cost'))['total_cost'] or 0


# listamos los servicios que puede recibir el vehiculo
class Service(models.Model):
    
    def current_year():
        return datetime.date.today().year
    
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, verbose_name='Patente')
    date = models.DateField(default=timezone.now, verbose_name='Fecha Servicio')
    kilometers = models.IntegerField(default=0, verbose_name='Kilometraje')
    service_type = models.CharField(max_length=500, choices=SERVICE_TYPE_CHOICES, verbose_name='Tipo de Servicio')
    coments = models.TextField(verbose_name='Comentarios', blank=True)
    #coments = models.TextField(verbose_name='Comentarios', blank=True, help_text="Indique cualquier cosa que desee comentar")
    cost = models.IntegerField(verbose_name='Costo del Servicio')
    created_at = models.DateField(auto_now_add=True, verbose_name='Fecha Servicio')

    def __str__(self):
        return self.service_type
    
    def total_service_cost(self):
        return self.service_set.aggregate(total_cost=models.Sum('cost'))['total_cost'] or 0
