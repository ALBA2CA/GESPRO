from django.shortcuts import render, get_object_or_404
from proyectos.models import Proyecto, Actividad, ActividadDifusion
from datetime import datetime, timedelta

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
        
        fechas_lista = []
        for fecha in fechas:
            # Ajustar fechas para evitar duración 0
            fecha_inicio = fecha.fecha_inicio
            fecha_fin = fecha.fecha_fin
            
            # Si las fechas son iguales, agregar un día a la fecha fin
            if fecha_inicio and fecha_fin and fecha_inicio == fecha_fin:
                fecha_fin = fecha_fin + timedelta(days=1)
            
            fecha_dict = {
                "fecha_inicio": fecha_inicio.strftime('%Y-%m-%d') if fecha_inicio else None,
                "fecha_fin": fecha_fin.strftime('%Y-%m-%d') if fecha_fin else None
            }
            fechas_lista.append(fecha_dict)
        
        todas_actividades.append({
            'id': actividad.id,
            'nombre': actividad.nombre or f"Actividad {actividad.id}",
            "fechas": fechas_lista,
            'tipo': 'Normal',
            'estado': actividad.get_estado_display() if hasattr(actividad, 'get_estado_display') else 'Sin estado',
            'linea_trabajo': actividad.linea_trabajo.nombre if actividad.linea_trabajo else 'Sin línea',
        })
    
    # Agregar actividades de difusión
    for actividad in actividades_difusion:
        fechas = actividad.fechas.filter(estado=True)
        
        fechas_lista = []
        for fecha in fechas:
            # Ajustar fechas para evitar duración 0
            fecha_inicio = fecha.fecha_inicio
            fecha_fin = fecha.fecha_fin
            
            # Si las fechas son iguales, agregar un día a la fecha fin
            if fecha_inicio and fecha_fin and fecha_inicio == fecha_fin:
                fecha_fin = fecha_fin + timedelta(days=1)
            
            fecha_dict = {
                "fecha_inicio": fecha_inicio.strftime('%Y-%m-%d') if fecha_inicio else None,
                "fecha_fin": fecha_fin.strftime('%Y-%m-%d') if fecha_fin else None
            }
            fechas_lista.append(fecha_dict)
        
        todas_actividades.append({
            'id': actividad.id,
            'nombre': actividad.nombre or f"Actividad Difusión {actividad.id}",
            'fechas': fechas_lista,
            'tipo': 'Difusión',
            'estado': actividad.get_estado_display() if hasattr(actividad, 'get_estado_display') else 'Sin estado',
            'linea_trabajo': None,
        })

    # Ordenar todas las actividades por fecha de inicio
    todas_actividades.sort(key=lambda x: x['fechas'][0]['fecha_inicio'] if x['fechas'] and x['fechas'][0]['fecha_inicio'] else '9999-12-31')

    
    context = {
        'proyecto': proyecto,
        "len_total_actividades": len(todas_actividades),
        "total_actividades": todas_actividades,
    }

    return render(request, 'vistas/vista_gantt.html', context)