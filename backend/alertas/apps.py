from django.apps import AppConfig
from django.apps import AppConfig
from django_q.models import Schedule
from django.utils import timezone


class AlertasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'alertas'
    def ready(self):
        # Solo se crea si no existe
        Schedule.objects.get_or_create(
            name="Enviar alertas diarias",
            defaults={
                "func": "miapp.tasks.enviar_alertas_diarias",
                "schedule_type": Schedule.DAILY,  # todos los días
                "repeats": -1,                     # repetir indefinidamente
                "next_run": timezone.now(),
            }
        )
