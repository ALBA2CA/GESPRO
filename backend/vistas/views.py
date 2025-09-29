
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from proyectos.models import Proyecto, Actividad, ActividadDifusion, ActividadBase, LineaTrabajo, ActividadDifusion_Linea, Actividad_Encargado
from datetime import datetime, timedelta
from django.contrib import messages
from django.db import models



def obtener_datos(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    
    actividades_normales = Actividad.objects.filter(
        linea_trabajo__proyecto=proyecto
    ).order_by('fecha_creacion')
    
    actividades_difusion = ActividadDifusion.objects.filter(
        proyecto=proyecto
    ).order_by('fecha_creacion')
    
    todas_actividades = []

    # Actividades normales
    for actividad in actividades_normales:
        fechas_lista = []
        for fecha in actividad.fechas.filter(estado=True):
            inicio = fecha.fecha_inicio
            fin = fecha.fecha_fin
            if inicio and fin and inicio == fin:
                fin += timedelta(days=1)
            fechas_lista.append({
                "fecha_inicio": inicio.strftime('%Y-%m-%d') if inicio else None,
                "fecha_fin": fin.strftime('%Y-%m-%d') if fin else None
            })
        consulta_2 = Actividad_Encargado.objects.filter(actividad=actividad).select_related('encargado')
        encargados = [rel.encargado.nombre for rel in consulta_2]
        todas_actividades.append({
            'id': actividad.id,
            'nombre': actividad.nombre or f"Actividad {actividad.id}",
            'fechas': fechas_lista,
            'tipo': 'Normal',
            'encargados': encargados,
            'estado': actividad.get_estado_display() if hasattr(actividad, 'get_estado_display') else 'Sin estado',
            'estado_valor': actividad.estado, 
            'linea_trabajo': actividad.linea_trabajo.nombre if actividad.linea_trabajo else 'Sin línea',
        })

    # Actividades de difusión
    for actividad in actividades_difusion:
        fechas_lista = []
        for fecha in actividad.fechas.filter(estado=True):
            inicio = fecha.fecha_inicio
            fin = fecha.fecha_fin
            if inicio and fin and inicio == fin:
                fin += timedelta(days=1)
            fechas_lista.append({
                "fecha_inicio": inicio.strftime('%Y-%m-%d') if inicio else None,
                "fecha_fin": fin.strftime('%Y-%m-%d') if fin else None
            })

        consulta= ActividadDifusion_Linea.objects.filter(actividad=actividad).select_related('linea_trabajo')
        lineas_trabajo = [rel.linea_trabajo.nombre for rel in consulta]

        consulta_2 = Actividad_Encargado.objects.filter(actividad=actividad).select_related('encargado')
        encargados = [rel.encargado.nombre for rel in consulta_2]


        todas_actividades.append({
            'id': actividad.id,
            'nombre': actividad.nombre or f"Actividad Difusión {actividad.id}",
            'fechas': fechas_lista,
            'tipo': 'Difusión',
            'encargados': encargados,
            'estado': actividad.get_estado_display() if hasattr(actividad, 'get_estado_display') else 'Sin estado',
            'estado_valor': actividad.estado, 
            'linea_trabajo': lineas_trabajo,
        })

    estados = [
        ('PEN', 'Pendiente'),
        ('LPC', 'Listo para comenzar'),
        ('EPR', 'En progreso'),
        ('COM', 'Completada'),
        ('TER', 'Terminada'),
    ]

    context = {
        'proyecto': proyecto,
        'actividades': todas_actividades,
        'estados': estados,
    }

    return context



def vista_gantt(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    actividades_normales = Actividad.objects.filter(linea_trabajo__proyecto=proyecto).order_by('fecha_creacion')
    actividades_difusion = ActividadDifusion.objects.filter(proyecto=proyecto).order_by('fecha_creacion')  
    todas_actividades = []

    for actividad in actividades_normales:
        fechas = actividad.fechas.filter(estado=True)
        
        fechas_lista = []
        for fecha in fechas:
            fecha_inicio = fecha.fecha_inicio
            fecha_fin = fecha.fecha_fin
            
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
    
    for actividad in actividades_difusion:
        fechas = actividad.fechas.filter(estado=True)
        
        fechas_lista = []
        for fecha in fechas:
            fecha_inicio = fecha.fecha_inicio
            fecha_fin = fecha.fecha_fin

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

    todas_actividades.sort(key=lambda x: x['fechas'][0]['fecha_inicio'] if x['fechas'] and x['fechas'][0]['fecha_inicio'] else '9999-12-31')

    
    context = {
        'proyecto': proyecto,
        "len_total_actividades": len(todas_actividades),
        "total_actividades": todas_actividades,
    }

    return render(request, 'vistas/vista_gantt.html', context)



def lista_actividades(request, proyecto_id):
    
    context = obtener_datos(request, proyecto_id)

    return render(request, "vistas/vista_lista.html", context)


def vista_tablero(request, proyecto_id):

    context = obtener_datos(request, proyecto_id)

    return render(request, 'vistas/vista_tablero.html', context)



@csrf_exempt
def actualizar_estado(request):
    if request.method == 'POST':
        actividad_id = request.POST.get('actividad_id')
        nuevo_estado = request.POST.get('nuevo_estado')
        try:
            actividad = ActividadBase.objects.get(id=actividad_id)
            actividad.estado = nuevo_estado
            actividad.save()
            return JsonResponse({'success': True})
        except ActividadBase.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Actividad no encontrada'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})        
    


