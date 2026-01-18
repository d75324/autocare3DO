from asyncio.log import logger
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, get_user_model
from django.views.generic import TemplateView, ListView, DetailView
from .models import Vehicle, Service
from django.views import View
from .forms import RegisterForm, ProfileForm, UserForm, VehicleForm, ServiceForm
from django.contrib.auth.models import Group, User
from django.urls import reverse_lazy
from django.views.generic.edit import DeleteView
from django.contrib.auth.views import LoginView
from autocare.forms import LoginForm
import csv, logging
from django.http import HttpResponse, HttpResponseRedirect

# importo estos recursos para crear una vista personalizada de restablecimiento de contraseña
#from django.contrib.auth.views import PasswordResetView
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings


# importo estos recursos para crear una vista personalizada de restablecimiento de contraseña
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

# pagina de antes de loguearse
class CeroView(TemplateView):
    template_name = 'cero.html'


# pagina de inicio, sin loguearse
class HomeView(TemplateView):
    template_name = 'home.html'
    logger = logging.getLogger(__name__)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Contar la cantidad de vehículos registrados
        context['total_vehicles'] = Vehicle.objects.count()

        # Contar la cantidad de servicios registrados
        context['total_services'] = Service.objects.count()

        # Contar la cantidad de mecánicos (usuarios en el grupo "Mecanicos")
        try:
            mecanicos_group = Group.objects.get(name='Mecanicos')
            context['total_mechanics'] = User.objects.filter(groups=mecanicos_group).count()
        except Group.DoesNotExist:
            context['total_mechanics'] = 0
        
        # Contar todos los usuarios registrados
        context['total_users'] = User.objects.count()

        # Contar usuarios en el grupo "Particulares"
        try:
            particulares_group = Group.objects.get(name='Particulares')
            context['total_particulares'] = User.objects.filter(groups=particulares_group).count()
        except Group.DoesNotExist:
            context['total_particulares'] = 0

        return context


# pagina de Features
class VersionesView(TemplateView):
    template_name = 'versiones.html'



class PricingView(TemplateView):
    template_name = 'pricing.html'


# registro de usuarios
class RegisterView(View):

    def get(self, request):
        data = {
            'form' : RegisterForm()
        }
        return render(request, 'registration/register.html', data)

    def post(self, request):
        user_creation_form = RegisterForm(data=request.POST)
        if user_creation_form.is_valid():
            user = user_creation_form.save()
            user = authenticate(username=user.email, password=request.POST['password1'])
            if user is not None:
                login(request, user)
                return redirect('profile')
        else:
            data = {
                'form': user_creation_form
            }
            return render(request, 'registration/register.html', data)


# pagina de perfil
class ProfileView(TemplateView):
    template_name = 'profile/profile.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        # if self.request.user.groups.filter(name='Mecanicos').exists():
        if self.request.user.is_anonymous:
            return queryset.none()
        else:
            return queryset.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['assigned_vehicles'] = Vehicle.objects.filter(owner=user)

        # lógica para la vista de estado de asignación
        context['vehicles'] = Vehicle.objects.filter(owner=user)
        context['assignment_status'] = [
            {'plate': vehicle.plate, 'status': 'A' if vehicle.car_mechanic else 'U'}
            for vehicle in context['vehicles']
        ]

        if self.request.user.is_anonymous:
            context['object_list'] = Vehicle.objects.none()
        else:
            context['object_list'] = Vehicle.objects.filter(owner=self.request.user)
            #para contar la cantidad de vehiculos, cuento la cantidad de object_list de la linea anterior:
            context['cantidad_vehiculos'] = context['object_list'].count()
            # Vehículos asignados al mecánico
            if user.profile.is_mechanic:
                assigned_vehicles = Vehicle.objects.filter(car_mechanic=user)
                print("query de vehiculos asignados: ", assigned_vehicles)
                print("usuario: ", user)
                print("contador de vehiculos asignados: ", assigned_vehicles.count())
                context['assigned_vehicles'] = assigned_vehicles

        context ['user_form'] = UserForm(instance=user)
        context ['profile_form'] = ProfileForm(instance=user.profile)
        return context

    def post(self, request, *args, **kwargs):
        user = self.request.user
        user_form = UserForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            # si todo está ok, redirecciono a la página de perfil actualizada
            return redirect('profile')

        #si alguno de los datos no es válido
        context = self.get_context_data
        context['user_form'] = user_form
        context['profile_form'] = profile_form
        return render(request, 'profile/profile.html', context)


#class VehicleListView(ListView):
class VehicleListView(ListView):
    model = Vehicle
    template_name = 'cars.html'
    context_object_name = 'vehicles'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['form'] = VehicleForm()
        # pruebo inicializar assigned_vehicles para que el template lo tome
        context['assigned_vehicles'] = Vehicle.objects.none()

        if user.is_anonymous:
            context['object_list'] = Vehicle.objects.none()
            context['cantidad_vehiculos'] = 0
        else:
            user_vehicles = Vehicle.objects.filter(owner=user)
            context['object_list'] = user_vehicles
            context['cantidad_vehiculos'] = user_vehicles.count()
            
            # Vehículos asignados al mecánico
            if user.profile.is_mechanic:
                assigned_vehicles = Vehicle.objects.filter(car_mechanic=user)
                print("query de vehiculos asignados: ", assigned_vehicles)
                print("usuario: ", user)
                print("contador de vehiculos asignados: ", assigned_vehicles.count())
                context['assigned_vehicles'] = assigned_vehicles
        
        print("Context: ", context) # Imprimir el contexto para comprobar su contenido
        return context

    def post(self, request, *args, **kwargs):
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.owner = request.user
            vehicle.save()
            return redirect('profile')
        else:
            context = self.get_context_data()
            context['form'] = form
            return self.render_to_response(context)


# Aquí vamos a agregar un botón para descargar en CSV todos los servicios hechos al auto.
class VehicleDetailView(DetailView):
    model = Vehicle
    template_name = 'vehicle_detail.html'

    def get_context_data(self, **kwargs): 
        context = super().get_context_data(**kwargs) 
        vehicle = self.get_object() 
        context['total_cost'] = vehicle.total_service_cost() 
        return context



class AddServiceView(TemplateView):
    #model = Service
    template_name = 'service.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ServiceForm(user=self.request.user)
        return context

    def get(self, request, pk, *args, **kwargs):
        context = self.get_context_data()
        vehicle = get_object_or_404(Vehicle, pk=pk)
        last_service = Service.objects.filter(vehicle=vehicle).order_by('-date').first() # ultimo kilometraje
        initial_kilometers = last_service.kilometers if last_service else vehicle.mileage

        context['form'] = ServiceForm(
            initial={'vehicle': vehicle, 'kilometers': initial_kilometers},
            user=request.user
        )
        return self.render_to_response(context)

    def post(self, request, pk, *args, **kwargs):
        vehicle = get_object_or_404(Vehicle, pk=pk)
        form = ServiceForm(request.POST, user=request.user)  # Paso el usuario al formulario
        if form.is_valid():
            service = form.save(commit=False)
            service.owner = request.user
            service.save()
            # voy a actualizar el kilometraje del vehículo y después lo guardo
            vehicle.mileage = service.kilometers
            vehicle.save() # guardado!
            return redirect('profile')
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)


# vista del histórico de servicios - nop!
class ServicesView(ListView):
    model = Service
    template_name = 'servicelist.html'
    context_object_name = 'object_list'

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return Service.objects.none()
        else:
            return Service.objects.filter(vehicle__owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user_form'] = UserForm(instance=user)
        context['profile_form'] = ProfileForm(instance=user.profile)
        return context


class VehicleServiceListView(TemplateView):
    pass


class VehicleDeleteView(DeleteView):
    model = Vehicle
    template_name = 'vehicle_confirm_delete.html'
    success_url = reverse_lazy('profile')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.service_set.all().delete()  # acá se borran también los servicios asociados
        return super().delete(request, *args, **kwargs)


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'registration/login.html'


# vista para descargar el CSV con el listado de los servicios realizados a un vehículo.
class DownloadCSVView(View):
    def get(self, request, *args, **kwargs):
        # obtenemos el ID del vehículo desde el argumento de la URL
        vehicle_id = self.kwargs['vehicle_id']
        vehicle = Vehicle.objects.get(id=vehicle_id)

        # creamos respuesta HTTP con el tipo de contenido CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="Servicios_{vehicle.plate}.csv"'

        # creamos el CSV, definimos las cabeceras
        writer = csv.writer(response)
        writer.writerow(['Patente', 'Fecha Servicio', 'Kilometraje', 'Costo del Servicio', 'Tipo de Servicio', 'Comentarios'])

        # agregamos los datos de cada servicio
        services = Service.objects.filter(vehicle=vehicle)
        for service in services:
            writer.writerow([
                vehicle.plate,
                service.date.strftime('%Y-%m-%d'),
                service.kilometers,
                service.cost,
                service.service_type,
                service.coments
            ])

        return response


CustomUser = get_user_model()

class MechanicsView(TemplateView):
    template_name = 'mechanics.html'

    def get_context_data(self, **kwargs):
        # contexto inicial
        context = super().get_context_data(**kwargs)
        
        # obtener la lista de usuarios del grupo 'Mecánicos'
        mecanicos_list = CustomUser.objects.filter(groups__name='Mecanicos').order_by('username')
        
        # 3. Agregar los datos al contexto
        context['mecanicos_list'] = mecanicos_list
        context['total_mechanics'] = mecanicos_list.count()
        
        return context


