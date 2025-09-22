from django.shortcuts import render, get_object_or_404
from proyectos.models import Proyecto, Actividad, ActividadDifusion

# Create your views here.
def vista_gantt(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    # Obtener todas las actividades normales (a través de linea_trabajo)
    actividades_normales = Actividad.objects.filter(linea_trabajo__proyecto=proyecto).order_by('fecha_creacion')
    
    # Obtener todas las actividades de difusión (directamente relacionadas con proyecto)
    actividades_difusion = ActividadDifusion.objects.filter(proyecto=proyecto).order_by('fecha_creacion')
    
    # Combinar todas las actividades en una lista
    todas_actividades = []

    # Agregar actividades normales
    for actividad in actividades_normales:
        # Obtener todas las fechas activas
        fechas = actividad.fechas.filter(estado=True)

        
        todas_actividades.append({
            'id': actividad.id,
            'nombre': actividad.nombre,
            "fechas": [ {"fecha_inicio": fecha.fecha_inicio, "fecha_fin": fecha.fecha_fin} for fecha in fechas ] if fechas.exists() else [],
            'tipo': 'Normal',
            'estado': actividad.get_estado_display(),
            'linea_trabajo': actividad.linea_trabajo.nombre,
        })
    
    # Agregar actividades de difusión
    for actividad in actividades_difusion:

        fechas = actividad.fechas.filter(estado=True)
        
        todas_actividades.append({
            'id': actividad.id,
            'nombre': actividad.nombre,
            'fechas': [ {"fecha_inicio": fecha.fecha_inicio, "fecha_fin": fecha.fecha_fin} for fecha in fechas ] if fechas.exists() else [],
            'tipo': 'Difusión',
            'estado': actividad.get_estado_display(),
            'linea_trabajo': None,  # Las actividades de difusión no tienen línea de trabajo directa
        })

    # Ordenar todas las actividades por fecha de inicio (las que no tienen fecha van al final)
    todas_actividades.sort(key=lambda x: x['fechas'][0]['fecha_inicio'] if x['fechas'] else None)
    
    # convertir cada fecha en una "subtarea" con distinto id pero mismo name
    tareas = []
    for actividad in todas_actividades:
        for i, f in enumerate(actividad["fechas"], start=1):
            tareas.append({
            "id": f"T{actividad['id']}_{i}",
            "name": actividad["nombre"],   # mismo nombre => misma fila
            "start": str(f["fecha_inicio"]),
            "end": str(f["fecha_fin"]),
            "progress": 0,
        })
    
    context = {
        'proyecto': proyecto,
        "len_total_actividades": len(todas_actividades),
        "total_actividades": todas_actividades,
        "tareas": tareas
    }

    return render(request, 'vistas/vista_gantt.html', context)