
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from proyectos.models import Proyecto, Actividad, ActividadDifusion
from datetime import datetime, timedelta
from django.contrib import messages




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


def lista_actividades(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    actividades_normales = Actividad.objects.filter(
        linea_trabajo__proyecto=proyecto
    ).select_related('linea_trabajo').prefetch_related('actividad_encargados__encargado')

    actividades_difusion = ActividadDifusion.objects.filter(
        proyecto=proyecto
    ).prefetch_related('actividad_difusion_encargados__encargado')

    todas_actividades = []
    for a in actividades_normales:
        encargados = [ae.encargado.nombre for ae in a.actividad_encargados.all()]
        todas_actividades.append({
            'id': a.id,
            'nombre': a.nombre or f"Actividad {a.id}",
            'tipo': 'Normal',
            'estado': a.get_estado_display(),
            'estado_valor': a.estado,
            'linea_trabajo': a.linea_trabajo.nombre if a.linea_trabajo else 'Sin línea',
            'encargados': encargados if encargados else ["No asignado"],
        })

    for a in actividades_difusion:
        encargados = [ade.encargado.nombre for ade in a.actividad_difusion_encargados.all()]
        todas_actividades.append({
            'id': a.id,
            'nombre': a.nombre or f"Actividad Difusión {a.id}",
            'tipo': 'Difusión',
            'estado': a.get_estado_display(),
            'estado_valor': a.estado,
            'linea_trabajo': None,
            'encargados': encargados if encargados else ["No asignado"],
        })

    context = {
        'proyecto': proyecto,
        'actividades': todas_actividades,
        'estado_choices': Actividad._meta.get_field('estado').choices,  
    }
    return render(request, "vistas/vista_lista.html", context)




def vista_tablero(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    actividades_normales = Actividad.objects.filter(linea_trabajo__proyecto=proyecto).select_related('linea_trabajo')
    actividades_difusion = ActividadDifusion.objects.filter(proyecto=proyecto)

    todas_actividades = list(actividades_normales) + list(actividades_difusion)

    estados = [
        ('PEN', 'Pendiente'),
        ('LPC', 'Listo para comenzar'),
        ('EPR', 'En progreso'),
        ('COM', 'Completada'),
        ('TER', 'Terminada'),
    ]

    return render(request, 'vistas/vista_tablero.html', {
        'proyecto': proyecto,
        'actividades': todas_actividades,
        'estados': estados,
    })


@csrf_exempt
def actualizar_estado(request):
    if request.method == 'POST':
        actividad_id = request.POST.get('actividad_id')
        nuevo_estado = request.POST.get('nuevo_estado')
        try:
            actividad = Actividad.objects.get(id=actividad_id)
            actividad.estado = nuevo_estado
            actividad.save()
            return JsonResponse({'success': True})
        except Actividad.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Actividad no encontrada'})

def actualizar_estado_actividad(request, actividad_id):
    # Intentar primero como Actividad normal
    actividad = Actividad.objects.filter(id=actividad_id).first()
    
    if not actividad:
        # Intentar como ActividadDifusion
        actividad = get_object_or_404(ActividadDifusion, id=actividad_id)

    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')

        if nuevo_estado in dict(EstadoActividad.choices):
            actividad.estado = nuevo_estado
            actividad.save()

            # Mensaje de éxito
            messages.success(request, f"Estado de '{actividad.nombre}' actualizado correctamente.")

            # Redirigir según tipo
            if isinstance(actividad, Actividad):
                return redirect('lista_actividades', proyecto_id=actividad.linea_trabajo.proyecto.id)
            elif isinstance(actividad, ActividadDifusion):
                return redirect('lista_actividades_difusion', proyecto_id=actividad.proyecto.id)

    # Por si entra por GET accidentalmente
    if isinstance(actividad, Actividad):
        return redirect('lista_actividades', proyecto_id=actividad.linea_trabajo.proyecto.id)
    else:
        return redirect('lista_actividades_difusion', proyecto_id=actividad.proyecto.id)
