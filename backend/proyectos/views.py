from django.shortcuts import render, redirect
from .models import *

# Create your views here.

def proyectos(request):
    if request.method == 'POST':
        print(request.POST)
    proyectos = Proyecto.objects.all()
    return render(request,'proyectos/proyectos.html',{
        'proyectos' : proyectos,
        })


def eliminar_proyecto(request):
    if request.method == 'POST':
        proyecto_id = request.POST['proyecto_id']
        try:
            proyecto = Proyecto.objects.get(id=proyecto_id)
            proyecto.delete()
            print(f'Proyecto con ID {proyecto_id} eliminado.')
        except Proyecto.DoesNotExist:
            print(f'No se encontró el proyecto con ID {proyecto_id}.')
    return proyectos(request)
    