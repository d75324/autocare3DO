from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.views.generic import TemplateView, ListView, DetailView
from .models import Vehicle, Service
from django.views import View
from .forms import RegisterForm, ProfileForm, UserForm, VehicleForm, ServiceForm
from django.contrib.auth.models import Group, User
from django.urls import reverse_lazy
from django.views.generic.edit import DeleteView
from django.contrib.auth.views import LoginView
from autocare.forms import LoginForm

# pagina de antes de loguearse
class CeroView(TemplateView):
    template_name = 'cero.html'

# pagina de inicio, sin loguearse
class HomeView(TemplateView):
    template_name = 'home.html'

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
