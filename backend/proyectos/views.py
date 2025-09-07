from django.shortcuts import render, redirect
from .models import *
from .forms import UploadExcelForm
import pandas as pd
import os
from django.http import FileResponse, Http404
from django.conf import settings
from proyectos.import_gantt import importar_gantt

# Create your views here.

def proyectos(request):
    if request.method == 'POST':
        print(request.POST)
    proyectos = Proyecto.objects.all()
    return render(request,'proyectos/proyectos.html',{
        'proyectos' : proyectos,
        })
    

def importar_proyecto(request):
    if request.method == 'POST':
        form = UploadExcelForm(request.POST, request.FILES)
        if form.is_valid():
            nombre_proyecto = form.cleaned_data['nombre_proyecto']
            archivo = request.FILES['archivo']
            
            # Llamamos a la función que importa el Excel
            proyecto = importar_gantt(nombre_proyecto, archivo)     

            return redirect('proyectos')  # o donde quieras redirigir
    else:
        form = UploadExcelForm()
    
    return render(request, 'proyectos/importar_proyecto.html', {'form': form})

def descargar_plantilla(request):
    ruta_archivo = os.path.join(settings.BASE_DIR, 'backend', 'media', 'plantilla.xlsx')
    if os.path.exists(ruta_archivo):
        return FileResponse(open(ruta_archivo, 'rb'), as_attachment=True, filename='plantilla.xlsx')
    else:
        raise Http404("Archivo no encontrado")