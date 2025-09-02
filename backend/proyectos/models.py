from django.db import models

# Create your models here.
class Proyecto(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_modificacion = models.DateTimeField(auto_now=True)
    estado = models.BoleanField(default=True)

    def __str__(self):
        return self.nombre
    
class LineaTrabajo(models.Model):
    id = models.AutoField(primary_key=True)
    proyecto = models.ForeignKey(Proyecto, related_name='lineas_trabajo', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_modificacion = models.DateTimeField(auto_now=True)
    estado = models.BooleanField(default=True)
    def __str__(self):
        return self.nombre
    
class ProductoAsociado(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    extension = models.CharField(max_length=10)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_modificacion = models.DateTimeField(auto_now=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Actividad(models.Model):
    id = models.AutoField(primary_key=True)
    linea_trabajo = models.ForeignKey(LineaTrabajo, related_name='actividades', on_delete=models.CASCADE)
    producto_asociado = models.ForeignKey(ProductoAsociado, related_name='actividades', on_delete=models.SET_NULL, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_modificacion = models.DateTimeField(auto_now=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre
    
class Encargado(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    correo_electronico = models.EmailField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_modificacion = models.DateTimeField(auto_now=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre
    
class Actividad_Encargado(models.Model):
    id = models.AutoField(primary_key=True)
    actividad = models.ForeignKey(Actividad, related_name='actividad_encargados', on_delete=models.CASCADE)
    encargado = models.ForeignKey(Encargado, related_name='actividad_encargados', on_delete=models.CASCADE)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    ultima_modificacion = models.DateTimeField(auto_now=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.actividad.nombre} - {self.encargado.nombre}"

