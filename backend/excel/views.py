from django.shortcuts import render, redirect
from proyectos.models import *
from .forms import UploadExcelForm
import os
from django.http import FileResponse, Http404
from django.conf import settings
from django.contrib import messages
from .import_gantt import importar_gantt, informacion_proyecto, separar_tablas_excel, FormatoInvalidoError


# Create your views here.
def verificar_proyecto(request):
    if request.method == 'POST':
        form = UploadExcelForm(request.POST, request.FILES)
        if form.is_valid():
            nombre_proyecto = form.cleaned_data['nombre_proyecto']
            archivo = request.FILES['archivo']
            if not archivo.name.endswith(('.xls', '.xlsx')):
                raise FormatoInvalidoError("El archivo debe ser Excel (.xls o .xlsx)")

            try:
                ruta_tmp = f"/tmp/{archivo.name}"
                with open(ruta_tmp, 'wb+') as destino:
                    for chunk in archivo.chunks():
                        destino.write(chunk)
                df_normales, df_difusion = separar_tablas_excel(archivo)
                info_proyecto = informacion_proyecto(df_normales, df_difusion)
                info_proyecto['Nombre_del_Proyecto'] = nombre_proyecto
                return render(request, 'excel/importar_proyecto.html', {'info_proyecto': info_proyecto, 'form': form, 'archivo': ruta_tmp, 'mostrar_modal': True})
            # Agregar solo si se usa unique=True en el modelo para el nombre del proyecto
            # except IntegrityError:
            #     messages.error(request, f"Ya existe un proyecto con el nombre '{nombre_proyecto}'")

            except FormatoInvalidoError as e:
                messages.error(request, f"Error de formato: {e}")
            except Exception as e:
                messages.error(request, f"Ocurrió un error al importar: {e}")
    else:
        form = UploadExcelForm()

    return render(request, 'excel/importar_proyecto.html', {'form': form})

def importar_proyecto(request):
    if request.method == 'POST':
        nombre_proyecto = request.POST.get('nombre_proyecto')
        ruta_tmp = request.POST.get('archivo')
        with open(ruta_tmp, 'rb') as archivo:
            if not archivo:
                messages.error(request, "No se ha proporcionado ningún archivo.")
                return redirect('verificar_proyecto')
            try:
                importar_gantt(nombre_proyecto, archivo)
                messages.success(request, f"Proyecto '{nombre_proyecto}' importado exitosamente.")
                return redirect('proyectos')  # Redirigir a la lista de proyectos o a donde sea apropiado
            except Exception as e:
                messages.error(request, f"Ocurrió un error al importar el proyecto: {e}")
                return redirect('verificar_proyecto')
 

def descargar_plantilla(request):
    ruta_archivo = os.path.join(settings.BASE_DIR, 'frontend', 'static', 'plantilla.xlsx')
    if os.path.exists(ruta_archivo):
        return FileResponse(open(ruta_archivo, 'rb'), as_attachment=True, filename='plantilla.xlsx')
    else:
        raise Http404("Archivo no encontrado")