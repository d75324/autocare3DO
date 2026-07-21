from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from .utils import validate_name_field, validate_email_username
from django.core.exceptions import ValidationError

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='Usuario')
    email = models.EmailField(max_length=254, unique=True, blank=True, null=True,verbose_name='Correo Electrónico')
    image = models.ImageField(default='default.jpg', upload_to='users/', verbose_name='Imagen')
    telephone = models.CharField(max_length=15, blank=True, null=True, verbose_name='Teléfono')
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name='Dirección')
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name='Ciudad')
    zip_code = models.CharField(max_length=10, blank=True, null=True, verbose_name='Código Postal')
    location = models.CharField(max_length=100, blank=True, null=True, verbose_name='Barrio')
    created_at = models.DateField(auto_now_add=True)
    # Campos específicos para Profesionales
    garage = models.CharField(max_length=255, blank=True, null=True, verbose_name='Nombre del Taller')
    professional_license = models.CharField(max_length=50, blank=True, null=True)
    website = models.URLField(max_length=200, blank=True, null=True, verbose_name='Sitio Web')

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfiles'
        #también se podría ordenar en base al id: ordering = ['-id']
        ordering = ['-created_at']

    # probar cambiar el username por el first_name en general        
    def __str__(self):
        return f"{self.user.username} - {self.email}"

    # voy a dejar lista este metodo por si necesito traer el nombre completo del usuario en algún momento.
    def get_full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    def is_mechanic(self):
        return self.user.groups.filter(name='Mecanicos').exists()

    def is_particular(self):
        return self.user.groups.filter(name='Particulares').exists()


    def clean(self):
        """Validación a nivel de modelo para el email (username), nombre y apellido"""
        super().clean()
        
        if self.user:
            # Traemos el estado actual del usuario en la Base de Datos para comparar.
            # No voy a validar usuarios que ya se registraron.
            db_user = User.objects.filter(pk=self.user.pk).first()
            # 1. Validar el username (una dirección de correo) SOLO SI ES NUEVO O CAMBIÓ
            if self.user.username:
                if not db_user or db_user.username != self.user.username:
                    try:
                        # Valida formato (usando utils.py), limpia espacios y lo pasa a minúsculas
                        self.user.username = validate_email_username(self.user.username)
                        
                        # Opcional: Mantener el campo email de Profile sincronizado con el username del User
                        self.email = self.user.username
                    except ValidationError as e:
                        raise ValidationError({'user': f"Error en el Correo de Usuario: {e.message}"})

            # 2. Validar first_name (Nombre)
            if self.user.first_name and self.user.first_name.strip():
                if not db_user or db_user.first_name != self.user.first_name:
                # if self.user.first_name:
                    try:
                        self.user.first_name = validate_name_field(self.user.first_name, "Nombre")
                    except ValidationError as e:
                        raise ValidationError({'user': f"Error en el Nombre: {e.message}"})

            # 3. Validar last_name (Apellido)
            # if self.user.last_name:
            if self.user.last_name and self.user.last_name.strip():
                if not db_user or db_user.last_name != self.user.last_name:                
                    try:
                        self.user.last_name = validate_name_field(self.user.last_name, "Apellido")
                    except ValidationError as e:
                        raise ValidationError({'user': f"Error en el Apellido: {e.message}"})


    def save(self, *args, **kwargs):
        """Ejecuta la validación total y guarda tanto el usuario como el perfil"""
        # Ejecuta el método clean() definido mas arriba
        self.full_clean()
        
        # Guardamos primero los cambios del usuario (por si utils.py modificó la capitalización)
        if self.user:
            # Desconectamos temporalmente la señal save_user_profile para evitar bucles infinitos
            post_save.disconnect(save_user_profile, sender=User)
            self.user.save()
            post_save.connect(save_user_profile, sender=User)

        super().save(*args, **kwargs)

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

# -- SIGNALS -- # 
# automatiza la relación entre los usuarios (User) y sus perfiles (Profile): Cuando pasa algo importante en un modelo, Django "grita" un aviso a todo el proyecto, y si hay funciones escuchando ese grito, se ejecutan automáticamente.

# Tan pronto como un usuario se guarde (post_save), si la orden vino del modelo User (sender=User), ejecuta inmediatamente la función create_user_profile".
# esta señal se activa cuando un cliente se registra en la app y se guarda en la tabla User. La función create_user_profile chequea si se trata de un nuevo usuario; si la respuesta es sí (created=True), el sistema crea automáticamente una fila en la tabla Profile enlazada a ese nuevo usuario.
post_save.connect(create_user_profile, sender=User)

# cada vez que un usuario se guarde (post_save), si la orden vino del modelo User, ejecuta inmediatamente la función save_user_profile.
# sincronización y actualización.
# esta signal no solo corre cuando el usuario es nuevo, sino cada vez que el usuario se modifica en el futuro (por ejemplo, cuando cambia su contraseña, cuando actualiza su email, cuando Django actualiza su last_login al iniciar sesión). La función save_user_profile toma el perfil de ese usuario y le hace un .save().
post_save.connect(save_user_profile, sender=User)

