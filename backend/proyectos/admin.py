from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Proyecto)
admin.site.register(LineaTrabajo)
admin.site.register(Actividad)
admin.site.register(ProductoAsociado)
admin.site.register(Encargado)
admin.site.register(Actividad_Encargado)


