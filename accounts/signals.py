# cuando recibe el registro de un usuario, va a asignarlo a un grupo automáticamente

from django.contrib.auth.models import Group
from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import Profile

# el decorador receiver va a decorar funciones que se dedican a cumplir tareas específicas

@receiver(post_save, sender=Profile)
def add_user_to_personal_group(sender, instance, created, **kwargs):
    if created:
        try:
            group1 = Group.objects.get(name='Particulares')
        except Group.DoesNotExist:
            group1 = Group.objects.create(name='Particulares')
            group2 = Group.objects.create(name='Mecanicos')
        instance.user.groups.add(group1)