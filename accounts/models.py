from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save


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

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

post_save.connect(create_user_profile, sender=User)
post_save.connect(save_user_profile, sender=User)