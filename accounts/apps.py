from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'perfiles'

# esta función es la encargada de que cuando la app se ejecute, se cargue el archivo signals.

    def ready(self):
        import accounts.signals
