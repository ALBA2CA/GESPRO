import os
import django
import pandas as pd
from datetime import datetime, date

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gespro.settings')
django.setup()

from proyectos.models import Proyecto, LineaTrabajo, Actividad, ProductoAsociado, Encargado, Actividad_Encargado

# Mapeo de meses en español a número
MES_MAP = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
    'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
}

def generar_fechas_reales(date_cols, anio_inicial=None):
    """
    Devuelve un diccionario col -> fecha real,
    sumando años si hay retroceso de mes.
    Ignora columnas que no tengan un día válido.
    """
    fechas_reales = {}
    anio_actual = anio_inicial or datetime.now().year
    mes_anterior = 0

    for col in date_cols:
        mes_str, dia_str = col[0].lower(), col[1]

        try:
            dia = int(dia_str)
        except (ValueError, TypeError):
            # Si la columna no tiene un número válido, la ignoramos
            continue

        mes = MES_MAP.get(mes_str, 1)

        # Si hay retroceso de mes, incrementamos año
        if mes < mes_anterior:
            anio_actual += 1
        mes_anterior = mes

        fechas_reales[col] = date(anio_actual, mes, dia)

    return fechas_reales

def importar_gantt(nombre_proyecto, archivo_excel, anio_inicial=None):
    df = pd.read_excel(archivo_excel, header=[0, 1])

    info_cols = [
        ('Unnamed: 0_level_0', 'Linea de trabajo'),
        ('Unnamed: 3_level_0', 'Actividad'),
        ('Unnamed: 4_level_0', 'Responsable(s)'),
        ('Unnamed: 5_level_0', 'Producto Asociado')
    ]

    date_cols = [col for col in df.columns if col not in info_cols]

    # Generar mapping de columnas a fechas reales
    fechas_reales = generar_fechas_reales(date_cols, anio_inicial)

    # Crear proyecto con fechas temporales
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
            producto_obj, _ = ProductoAsociado.objects.get_or_create(
                nombre=producto_nombre,
                extension=''
            )

        # Actividad
        actividad_nombre = row[('Unnamed: 3_level_0', 'Actividad')]
        if pd.isna(actividad_nombre):
            continue

        # Fechas activas
        fechas_activas = [fechas_reales[col] for col in date_cols if str(row[col]).strip().lower() == 'x']

        if not fechas_activas:
            continue

        fecha_inicio_act = min(fechas_activas)
        fecha_fin_act = max(fechas_activas)

        # Actualizar min y max del proyecto
        if (min_fecha is None) or (fecha_inicio_act < min_fecha):
            min_fecha = fecha_inicio_act
        if (max_fecha is None) or (fecha_fin_act > max_fecha):
            max_fecha = fecha_fin_act

        # Crear actividad
        actividad_obj = Actividad.objects.create(
            linea_trabajo=linea_obj,
            producto_asociado=producto_obj,
            nombre=actividad_nombre,
            fecha_inicio=fecha_inicio_act,
            fecha_fin=fecha_fin_act
        )

        # Encargados
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
    
    

    # -------------------------
    # Procesar sección Difusión
    # -------------------------
    # Localizar el inicio de Difusión (fila con "Difusión")
    idx_difusion = df[df[('Unnamed: 0_level_0', 'Linea de trabajo')]
                      .astype(str).str.strip().str.lower() == 'difusión'].index

    if not idx_difusion.empty:
        start_idx = idx_difusion[0] + 2  # saltamos "Difusión" y la fila de subtítulos
        df_difusion = df.loc[start_idx:]

        ultima_linea = "Difusión"
        for _, row in df_difusion.iterrows():
            actividad_nombre = row[('Unnamed: 1_level_0', 'Linea de trabajo')]  # col de Actividad en Difusión
            responsables = row[('Unnamed: 3_level_0', 'Actividad')]            # col de Responsable en Difusión
            producto_nombre = row[('Unnamed: 4_level_0', 'Responsable(s)')]    # col de Producto asociado en Difusión
            
            # Fechas activas
            if pd.isna(actividad_nombre):
                continue

            # LineaTrabajo
            linea_obj, _ = LineaTrabajo.objects.get_or_create(
                proyecto=proyecto,
                nombre=ultima_linea
            )

            # Producto Asociado
            producto_obj = None
            if pd.notna(producto_nombre):
                producto_obj, _ = ProductoAsociado.objects.get_or_create(
                    nombre=str(producto_nombre).strip(),
                    extension=''
                )

            # Fechas activas
            fechas_activas = [fechas_reales[col] for col in date_cols if str(row[col]).strip().lower() == 'x']
            if not fechas_activas:
                continue
            
            fecha_inicio_act = min(fechas_activas)
            fecha_fin_act = max(fechas_activas)

            # Crear actividad
            actividad_obj = Actividad.objects.create(
                linea_trabajo=linea_obj,
                producto_asociado=producto_obj,
                nombre=str(actividad_nombre).strip(),
                fecha_inicio=fecha_inicio_act,
                fecha_fin=fecha_fin_act
            )

            # Encargados
            if pd.notna(responsables):
                for r in str(responsables).split('y'):
                    r = r.strip().lower()
                    if r:
                        encargado_obj, _ = Encargado.objects.get_or_create(nombre=r, correo_electronico='')
                        Actividad_Encargado.objects.get_or_create(
                            actividad=actividad_obj,
                            encargado=encargado_obj
                        )

    # Actualizar proyecto con fechas finales
    if min_fecha and max_fecha:
        proyecto.fecha_inicio = min_fecha
        proyecto.fecha_fin = max_fecha
        proyecto.save()

    return proyecto
