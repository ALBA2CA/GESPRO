from django.shortcuts import render, get_object_or_404
from proyectos.models import Proyecto, Actividad, ActividadDifusion
from django.db.models import Prefetch


# Create your views here.


def listado_alertas(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    actividades_normales = Actividad.objects.filter(
        linea_trabajo__proyecto=proyecto,
    ).prefetch_related(
        Prefetch('actividad_encargados__encargado'),
        'alertas',
        'fechas'
    ).distinct()

    actividades_difusion = ActividadDifusion.objects.filter(
        proyecto=proyecto,
    ).prefetch_related(
        Prefetch('actividad_encargados__encargado'),
        'alertas',
        'fechas'
    ).distinct()


    actividades = list(actividades_normales) + list(actividades_difusion)

    for actividad in actividades:
        fecha_activa = actividad.fechas.filter(estado=True).order_by('-fecha_fin').first()
        actividad.fecha_limite = fecha_activa.fecha_fin if fecha_activa else None

    return render(request, "alertas/listado_alertas.html", {
        "proyecto": proyecto,
        "actividades": actividades
    })