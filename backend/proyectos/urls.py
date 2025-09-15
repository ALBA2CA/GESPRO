from django.urls import path
from . import views


urlpatterns = [
    path('', views.proyectos,name = 'proyectos'),
    path('eliminar/', views.eliminar_proyecto, name='eliminar_proyecto'),
    ]
