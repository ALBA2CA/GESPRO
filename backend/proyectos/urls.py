from django.urls import path
from . import views


urlpatterns = [
    path('', views.proyectos,name = 'proyectos'),
]