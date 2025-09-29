from django.urls import path
from . import views


urlpatterns = [
    path('listado/<int:proyecto_id>/', views.listado_alertas,
    name='listado_alertas'), 
]