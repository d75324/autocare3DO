# este es un archivo de prueba...
# alternativa a la vista views.py, usando BaseView(TemplateView) en lugar de CustomTemplateView(TemplateView):

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.views.generic import TemplateView, ListView
from .models import Vehicle
from django.views import View
from .forms import RegisterForm
from django.contrib.auth.models import Group

class BaseView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        group_name = None
        if user.is_authenticated:
            group = Group.objects.filter(user=user).first()
            if group:
                group_name = group.name
        context['group_name'] = group_name
        return context    

# pagina de inicio
class HomeView(BaseView):
    template_name = 'home.html'

# pagina de Versiones
class VersionesView(BaseView):
    template_name = 'versiones.html'

# pagina de precios
class PricingView(BaseView):
    template_name = 'pricing.html'

class CarsView(ListView):
    model = Vehicle
    template_name = 'cars.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        # if self.request.user.groups.filter(name='Mecanicos').exists():
        if self.request.user.is_anonymous:
            return queryset.none()
        else:
            queryset = queryset.filter(owner=self.request.user)
        return queryset

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
            user_creation_form.save()
            user = authenticate(username=user_creation_form.cleaned_data['username'], password=user_creation_form.cleaned_data['password1'])
            login(request, user)
            return redirect('home')
        
        data = {
            'form': user_creation_form
        }
        return render(request, 'registration/register.html', data)