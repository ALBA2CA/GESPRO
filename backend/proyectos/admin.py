from django.contrib import admin
from .models import Proyecto, Actividad, LineaTrabajo, ProductoAsociado, Encargado

# Register your models here.
admin.site.register(Proyecto)
admin.site.register(Actividad)
admin.site.register(LineaTrabajo)
admin.site.register(ProductoAsociado)
admin.site.register(Encargado)