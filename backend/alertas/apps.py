from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.utils import timezone

class AlertasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "alertas"

    def ready(self):
        from django_q.models import Schedule

        def crear_schedule(sender, **kwargs):
            Schedule.objects.get_or_create(
                name="Enviar alertas diarias",
                defaults={
                    "func": "alertas.tasks.enviar_alertas_diarias",
                    "schedule_type": Schedule.DAILY,
                    "repeats": -1,
                    "next_run": timezone.now(),
                },
            )
            print(" Schedule verificado/creado")

        post_migrate.connect(crear_schedule)
