from django.urls import path
from . import views


urlpatterns = [
    path('vista_gantt/<int:proyecto_id>/', views.vista_gantt, name='vista_gantt'),
]