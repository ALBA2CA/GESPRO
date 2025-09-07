from django.urls import path
from . import views


urlpatterns = [
    path('', views.proyectos,name = 'proyectos'),
    path('importar_proyecto/', views.importar_proyecto, name='importar_proyecto'),
    path('descargar_plantilla/', views.descargar_plantilla, name='descargar_plantilla')
]