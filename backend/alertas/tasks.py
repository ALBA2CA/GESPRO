from django.utils import timezone
from django.core.mail import send_mail
from proyectos.models import Alerta, Actividad_Encargado

def enviar_alertas_diarias():
    hoy = timezone.now().date()
    alertas = Alerta.objects.filter(fecha_envio__date=hoy, enviado=False)

    for alerta in alertas:
        encargados = Actividad_Encargado.objects.filter(
            actividad=alerta.actividad, estado=True
        )
        correos = [e.encargado.correo_electronico for e in encargados]
        if correos:
            send_mail(
                subject=f"Alerta: {alerta.actividad.nombre}",
                message=f"Recuerda que hoy debes realizar la actividad: {alerta.actividad.nombre}",
                from_email=None,  # usa DEFAULT_FROM_EMAIL
                recipient_list=correos,
                fail_silently=False,
            )
        alerta.enviado = True
        alerta.save()