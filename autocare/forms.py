from django import forms
from django.contrib.auth.models import User, Group
from .models import Vehicle, Service
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from accounts.models import Profile
from django.core.exceptions import ValidationError
import re


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='Correo Electrónico')
    
    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError('Esta cuenta está inactiva.', code='inactive')


class RegisterForm(UserCreationForm):
    email = forms.EmailField(label='Correo Electrónico')
    first_name = forms.CharField(label='Nombre')
    last_name = forms.CharField(label='Apellido')
    group = forms.ModelChoiceField(queryset=Group.objects.none(), required=True, label='Tipo de Uso: ')

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cargar los grupos solo cuando se inicializa el formulario
        self.fields['group'].queryset = Group.objects.filter(name__in=['Mecanicos', 'Particulares'])
        try:
            self.fields['group'].initial = Group.objects.get(name='Particulares')
        except Group.DoesNotExist:
            self.fields['group'].initial = None
    
    ## -- VALIDAR LOS CARACTERES QUE SE INGRESAN EN EL FORMULARIO DE REGISTRO -- ##
    
    def clean_first_name(self): # valido first_name
        first_name = self.cleaned_data.get('first_name') 
        return self._validate_name_field(first_name, "Nombre") # _gion bajo para metodos que se usan localmente dentro de la función
    
    def clean_last_name(self): # valido last_name
        last_name = self.cleaned_data.get('last_name') 
        return self._validate_name_field(last_name, "Apellido") 
    
    def _validate_name_field(self, value, field_name): 
        """Método común para validar nombres y apellidos""" 
        if not value: 
            raise ValidationError(f'El {field_name} es obligatorio.') 
        
        # Eliminar espacios al inicio y final 
        value = value.strip() 
        
        # 1. Validar que solo contenga letras, espacios, ñ, tildes y guiones 
        # Permitir caracteres Unicode (para ñ, tildes, etc.) 
        if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑüÜ\s\-]+$', value): 
            raise ValidationError( 
                f'El {field_name} solo debe contener letras, espacios, ñ, tildes y guiones.' 
            ) 
        
        # 2. Validar que no contenga URLs o caracteres sospechosos 
        suspicious_patterns = [ 
            r'https?://',      # URLs 
            r'www\.',          # URLs sin http 
            r'\.com',          # Dominios 
            r'\.org',          # Dominios 
            r'<[^>]+>',        # Tags HTML 
            r'[{}()\[\]]',     # Corchetes y llaves 
            r'[#@$%^&*+=]',    # Caracteres especiales comunes en spam 
            r'código',         # Palabras clave sospechosas 
            r'codigo', 
            r'descuento', 
            r'promoción', 
            r'bugs', 
            r'seguridad', 
        ] 
        
        for pattern in suspicious_patterns: 
            if re.search(pattern, value, re.IGNORECASE): 
                raise ValidationError( 
                    f'El {field_name} contiene caracteres o palabras no permitidas.' 
                ) 
        
        # 3. Validar longitud mínima y máxima 
        if len(value) < 3: 
            raise ValidationError(f'El {field_name} debe tener al menos 3 caracteres.') 
        if len(value) > 30: 
            raise ValidationError(f'El {field_name} no puede exceder los 30 caracteres.') 
        
        # 4. Validar que no sea solo espacios 
        if value.isspace(): 
            raise ValidationError(f'El {field_name} no puede estar vacío.') 
        
        return value.title()  # Capitalizar el nombre

    ## -- FIN validación de caracteres en formulario de registro -- ##
    
    def clean_email(self):
        email_field = self.cleaned_data['email']
        if User.objects.filter(email=email_field).exists():
            raise forms.ValidationError('Este correo electrónico ya se encuentra registrado')
        return email_field

    def save(self, commit=True):
        user = super(RegisterForm, self).save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            group = self.cleaned_data['group']
            user.groups.add(group)
        return user


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(VehicleForm, self).__init__(*args, **kwargs)
        self.fields['car_mechanic'].queryset = User.objects.filter(groups__name='Mecanicos')


# Formulario para editar la información de los usuarios. Como estoy usando
# dos tablas, una parte va a impactar en User y otra parte en Profile
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'address', 'location', 'telephone']


# formulario para carga de vehiculos
class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['plate', 'brand', 'moddel', 'year', 'color', 'mileage', 'car_mechanic']
    
    def __init__(self, *args, **kwargs):
        super(VehicleForm, self).__init__(*args, **kwargs)
        try:
            mecanicos_group = Group.objects.get(name='Mecanicos')
            mecanicos = User.objects.filter(groups=mecanicos_group)
            self.fields['car_mechanic'].queryset = mecanicos
            self.fields['car_mechanic'].label_from_instance = lambda obj: f"{obj.first_name} {obj.last_name} # {obj.email}"
        except Group.DoesNotExist:
            self.fields['car_mechanic'].queryset = User.objects.none()


# formulario para agregar vehiculos. Aca necesito que por default la placa sea la del vehiculo en el cual doy click...
class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['vehicle', 'date', 'kilometers', 'service_type', 'coments', 'cost']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ServiceForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['vehicle'].queryset = Vehicle.objects.filter(owner=user)
            # Inicializa el campo 'coments' con el nombre del usuario
            self.fields['coments'].initial = f"Autor: {user.get_full_name()}"
        else:
            self.fields['vehicle'].queryset = Vehicle.objects.none()
        self.fields['vehicle'].required = True
        self.fields['vehicle'].empty_label = None
