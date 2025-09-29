from django.apps import AppConfig
from django.utils import timezone


class AlertasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'alertas'
    def ready(self):
        from django_q.models import Schedule
        # Solo se crea si no existe
        Schedule.objects.get_or_create(
            name="Enviar alertas diarias",
            defaults={
                "func": "alertas.tasks.enviar_alertas_diarias",
                "schedule_type": Schedule.DAILY,  # todos los días
                "repeats": -1,                     # repetir indefinidamente
                "next_run": timezone.now(),
            }
        )
