import os
import django
import pandas as pd
from datetime import datetime, date

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gespro.settings')
django.setup()

from proyectos.models import Proyecto, LineaTrabajo, Actividad, ProductoAsociado, Encargado, Actividad_Encargado

class FormatoInvalidoError(Exception):
    """Error cuando el archivo no cumple con el formato esperado."""
    pass


MES_MAP = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
    'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
}


def generar_fechas_reales(date_cols, anio_inicial=None):
    """Devuelve un diccionario col -> fecha real, sumando años si hay retroceso de mes."""
    fechas_reales = {}
    anio_actual = anio_inicial or datetime.now().year
    mes_anterior = 0

    for col in date_cols:
        mes_str, dia_str = col[0].lower(), col[1]

        try:
            dia = int(dia_str)
        except (ValueError, TypeError):
            continue

        mes = MES_MAP.get(mes_str, 1)

        if mes < mes_anterior:
            anio_actual += 1
        mes_anterior = mes

        fechas_reales[col] = date(anio_actual, mes, dia)

    return fechas_reales


def validar_excel(df):
    """Valida que el DataFrame tenga todas las columnas y fechas correctas."""
    info_cols = [
        ('Unnamed: 0_level_0', 'Linea de trabajo'),
        ('Unnamed: 3_level_0', 'Actividad'),
        ('Unnamed: 4_level_0', 'Responsable(s)'),
        ('Unnamed: 5_level_0', 'Producto Asociado')
    ]

    for col in info_cols:
        if col not in df.columns:
            raise FormatoInvalidoError(f"Falta la columna requerida: {col[1]}")

    date_cols = [col for col in df.columns if col not in info_cols]
    fechas_reales = generar_fechas_reales(date_cols)

    if not fechas_reales:
        raise FormatoInvalidoError("No se encontraron columnas de fechas válidas en el archivo.")

    return fechas_reales, info_cols, date_cols

def crear_proyecto(nombre_proyecto, df, fechas_reales, info_cols, date_cols):
    """Crea Proyecto, Lineas, Actividades, Productos y Encargados."""
    proyecto = Proyecto.objects.create(
        nombre=nombre_proyecto,
        fecha_inicio=datetime.now().date(),
        fecha_fin=None
    )

    ultima_linea = None
    min_fecha = None
    max_fecha = None

    for _, row in df.iterrows():
        linea = row[('Unnamed: 0_level_0', 'Linea de trabajo')]

        # Detenerse antes de "Difusión"
        if str(linea).strip().lower() == 'difusión':
            break
        if pd.notna(linea):
            ultima_linea = linea
        if not ultima_linea:
            continue

        # LineaTrabajo
        linea_obj, _ = LineaTrabajo.objects.get_or_create(
            proyecto=proyecto,
            nombre=ultima_linea
        )
        # Producto Asociado
        producto_nombre = row[('Unnamed: 5_level_0', 'Producto Asociado')]
        producto_obj = None
        if pd.notna(producto_nombre):
            # Buscar producto existente ignorando mayúsculas/minúsculas
            producto_obj = ProductoAsociado.objects.filter(nombre__iexact=producto_nombre).first()
            if not producto_obj:
                # Si no existe, crear uno nuevo usando capitalización original
                producto_obj = ProductoAsociado.objects.create(nombre=producto_nombre, extension='')


        actividad_nombre = row[('Unnamed: 3_level_0', 'Actividad')]
        if pd.isna(actividad_nombre):
            continue

        fechas_activas = [fechas_reales[col] for col in date_cols if str(row[col]).strip().lower() == 'x']
        if not fechas_activas:
            continue

        fecha_inicio_act = min(fechas_activas)
        fecha_fin_act = max(fechas_activas)

        if fecha_inicio_act > fecha_fin_act:
            raise FormatoInvalidoError(f"Fechas incoherentes en la actividad {actividad_nombre}")

        if (min_fecha is None) or (fecha_inicio_act < min_fecha):
            min_fecha = fecha_inicio_act
        if (max_fecha is None) or (fecha_fin_act > max_fecha):
            max_fecha = fecha_fin_act

        actividad_obj = Actividad.objects.create(
            linea_trabajo=linea_obj,
            producto_asociado=producto_obj,
            nombre=actividad_nombre,
            fecha_inicio=fecha_inicio_act,
            fecha_fin=fecha_fin_act
        )

        responsables = row[('Unnamed: 4_level_0', 'Responsable(s)')]
        if pd.notna(responsables):
            for r in str(responsables).split('y'):
                r = r.strip().lower()
                if r:
                    encargado_obj, _ = Encargado.objects.get_or_create(nombre=r, correo_electronico='')
                    Actividad_Encargado.objects.get_or_create(
                        actividad=actividad_obj,
                        encargado=encargado_obj
                    )

    if min_fecha and max_fecha:
        proyecto.fecha_inicio = min_fecha
        proyecto.fecha_fin = max_fecha
        proyecto.save()
    return proyecto

def importar_gantt(nombre_proyecto, archivo_excel):
    """Función principal para importar un Excel Gantt a Django."""
    if not archivo_excel.name.endswith(('.xls', '.xlsx')):
        raise FormatoInvalidoError("El archivo debe ser Excel (.xls o .xlsx)")

    try:
        df = pd.read_excel(archivo_excel, header=[0, 1])
    except Exception:
        raise FormatoInvalidoError("No se pudo leer el archivo como Excel válido.")

    fechas_reales, info_cols, date_cols = validar_excel(df)
    proyecto = crear_proyecto(nombre_proyecto, df, fechas_reales, info_cols, date_cols)
    return proyecto
