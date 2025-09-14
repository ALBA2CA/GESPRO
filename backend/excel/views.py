from django.shortcuts import render, redirect
from proyectos.models import *
from .forms import UploadExcelForm
import os
from django.http import FileResponse, Http404
from django.conf import settings
from django.contrib import messages
from .import_gantt import importar_gantt, FormatoInvalidoError


# Create your views here.
def importar_proyecto(request):
    if request.method == 'POST':
        form = UploadExcelForm(request.POST, request.FILES)
        if form.is_valid():
            nombre_proyecto = form.cleaned_data['nombre_proyecto']
            archivo = request.FILES['archivo']

            try:
                importar_gantt(nombre_proyecto, archivo)
                messages.success(request, "Proyecto importado correctamente.")
                return redirect('proyectos')
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

def descargar_plantilla(request):
    ruta_archivo = os.path.join(settings.BASE_DIR, 'frontend', 'static', 'plantilla.xlsx')
    if os.path.exists(ruta_archivo):
        return FileResponse(open(ruta_archivo, 'rb'), as_attachment=True, filename='plantilla.xlsx')
    else:
        raise Http404("Archivo no encontrado")