import os
import django
import pandas as pd
import unicodedata
from datetime import datetime, date
from django.db import transaction

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gespro.settings')
django.setup()

from proyectos.models import *

# =========================
# Excepciones
# =========================
class FormatoInvalidoError(Exception):
    """Error cuando el archivo no cumple con el formato esperado."""
    pass

# =========================
# Map de meses
# =========================
MES_MAP = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
    'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
}

# =========================
# Funciones auxiliares
# =========================
def normalize_str(s):
    """Normaliza string: quita acentos, pasa a ASCII, lower y strip."""
    if s is None:
        return ''
    s = str(s).strip()
    s = unicodedata.normalize('NFKD', s)
    s = s.encode('ASCII', 'ignore').decode('ASCII')
    return s.lower().strip()


def obtener_fechas_reales(date_cols, anio_inicial=None):
    """Convierte columnas de fecha en objetos date, corrigiendo año si hay retroceso de mes."""
    fechas_reales = {}
    anio_actual = anio_inicial or datetime.now().year
    mes_anterior = 0

    for col in date_cols:
        if isinstance(col, tuple):
            mes_str, dia_str = col[0].lower(), col[1]
        else:
            mes_str, dia_str = 'enero', col

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


def separar_tablas_excel(archivo, multiindex=True):
    """
    Lee un Excel Gantt y devuelve dos DataFrames:
    - df_normales: actividades normales
    - df_difusion: actividades de difusión
    """
    header = [0, 1] if multiindex else 0
    df = pd.read_excel(archivo, header=header)

    # Detectar fila "Difusión"
    difusion_idx = None
    for idx, row in df.iterrows():
        if normalize_str(row.iloc[0]) == "difusion":
            difusion_idx = idx
            break
    if difusion_idx is None:
        raise ValueError("No se encontró la sección Difusión en el Excel.")

    # Tabla normales
    df_normales = df.iloc[:difusion_idx].copy().reset_index(drop=True)

    # Tabla difusión
    header_row = df.iloc[difusion_idx + 1]
    df_difusion = df.iloc[difusion_idx + 2:].copy().reset_index(drop=True)
    df_difusion.columns = header_row

    return df_normales, df_difusion


def validar_columnas_normales(df):
    """
    Valida que el DataFrame de actividades normales tenga las columnas mínimas.
    Soporta MultiIndex o columnas planas.
    """
    info_cols = []
    for col in df.columns:
        # Caso MultiIndex
        if isinstance(col, tuple):
            if col[1] in ['Linea de trabajo', 'Actividad', 'Responsable(s)', 'Producto Asociado']:
                info_cols.append(col)
    
    if not info_cols:
        raise FormatoInvalidoError("No se encontraron columnas válidas para actividades normales.")
    
    return info_cols


def validar_columnas_difusion(df):
    """Valida que existan columnas mínimas para actividades de difusión."""
    required_cols = ['Actividad de Difusión', 'Responsable de la Actividad de Difusión', 
                     'Producto(s) Asociado(s)', 'Línea(s) de Trabajo Asociada(s)']
    for col in required_cols:
        if col not in df.columns:
            raise FormatoInvalidoError(f"No se encontró la columna obligatoria: {col}")
    return True

def detectar_bloques_x(filas, date_cols):
    """Devuelve lista de intervalos (fecha_inicio, fecha_fin) según X."""
    bloques = []
    bloque_activo = None
    col_prev = None

    for col in date_cols:
        valor = str(filas[col]).strip().lower()
        if valor == 'x':
            if not bloque_activo:
                bloque_activo = col
        else:
            if bloque_activo:
                bloques.append((bloque_activo, col_prev))
                bloque_activo = None
        col_prev = col

    if bloque_activo:
        bloques.append((bloque_activo, col_prev))

    return bloques

# =========================
# Función principal: Actividades normales
# =========================
def crear_proyecto_con_actividades_normales(nombre_proyecto, df_normales):
    """Crea Proyecto y actividades normales, actualizando fecha inicio y fin del proyecto."""
    info_cols = validar_columnas_normales(df_normales)
    date_cols = [c for c in df_normales.columns if c not in info_cols]
    fechas_reales = obtener_fechas_reales(date_cols)
    if not fechas_reales:
        raise FormatoInvalidoError("No se encontraron columnas de fechas válidas en el archivo.")

    proyecto = Proyecto.objects.create(
        nombre=nombre_proyecto,
        fecha_inicio=datetime.now().date(),
        fecha_fin=None
    )

    ultima_linea = None
    primera_fecha = None
    ultima_fecha = None

    multiindex = isinstance(df_normales.columns, pd.MultiIndex)

    for idx, row in df_normales.iterrows():
        # Línea de trabajo

        linea = row.get(('Unnamed: 0_level_0', 'Linea de trabajo'))
        producto_nombre = row.get(('Unnamed: 5_level_0', 'Producto Asociado'))
        actividad_nombre = row.get(('Unnamed: 3_level_0', 'Actividad'))
        responsables = row.get(('Unnamed: 4_level_0', 'Responsable(s)'))


        if pd.notna(linea):
            ultima_linea = linea
        if not ultima_linea:
            continue

        linea_obj, _ = LineaTrabajo.objects.get_or_create(
            proyecto=proyecto,
            nombre=ultima_linea
        )

        # Producto asociado
        producto_obj = None
        if pd.notna(producto_nombre):
            producto_obj = ProductoAsociado.objects.filter(nombre__iexact=producto_nombre).first()
            if not producto_obj:
                producto_obj = ProductoAsociado.objects.create(nombre=producto_nombre, extension='', proyecto=proyecto)

        # Actividad
        if pd.isna(actividad_nombre):
            continue

        bloques = detectar_bloques_x(row, date_cols)
        if not bloques:
            continue

        actividad_obj = Actividad.objects.create(
            linea_trabajo=linea_obj,
            producto_asociado=producto_obj,
            nombre=actividad_nombre
        )

        # Fechas de la actividad
        for inicio_col, fin_col in bloques:
            fecha_inicio = fechas_reales.get(inicio_col)
            fecha_fin = fechas_reales.get(fin_col)
            if fecha_inicio and fecha_fin:
                Fecha.objects.create(actividad=actividad_obj, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

                # Actualizamos fechas de proyecto
                if primera_fecha is None or fecha_inicio < primera_fecha:
                    primera_fecha = fecha_inicio
                if ultima_fecha is None or fecha_fin > ultima_fecha:
                    ultima_fecha = fecha_fin

        # Encargados
        if pd.notna(responsables):
            for r in str(responsables).split('y'):
                r = r.strip()
                if r:
                    encargado_obj = Encargado.objects.filter(nombre__iexact=r).first()
                    if not encargado_obj:
                        encargado_obj = Encargado.objects.create(nombre=r, correo_electronico='')
                    Actividad_Encargado.objects.get_or_create(
                        actividad=actividad_obj,
                        encargado=encargado_obj
                    )

    # Actualizar fechas del proyecto
    proyecto.fecha_inicio = primera_fecha
    proyecto.fecha_fin = ultima_fecha
    proyecto.save()

    return proyecto, date_cols, fechas_reales


def crear_actividades_difusion(proyecto, df_difusion, date_cols, fechas_reales):
    """
    Crea las actividades de difusión de un proyecto ya creado.
    Reutiliza date_cols y fechas_reales de las actividades normales.
    """
    COL_ACTIVIDAD = 'Actividad de Difusión'
    COL_RESPONSABLE = 'Responsable de la Actividad de Difusión'
    COL_PRODUCTO = 'Producto(s) Asociado(s)'
    COL_LINEA = 'Línea(s) de Trabajo Asociada(s)'

    for idx, row in df_difusion.iterrows():
        actividad_nombre = row.get(COL_ACTIVIDAD)
        if pd.isna(actividad_nombre) or not str(actividad_nombre).strip():
            continue

        actividad_obj = ActividadDifusion.objects.create(
            nombre=str(actividad_nombre).strip(),
            proyecto=proyecto
        )

        # Productos asociados
        productos_str = row.get(COL_PRODUCTO, '')
        productos = [p.strip() for p in str(productos_str).split(';') if p.strip()]
        for p_nombre in productos:
            producto_obj = ProductoAsociado.objects.filter(nombre__iexact=p_nombre, proyecto=proyecto).first()
            if not producto_obj:
                producto_obj = ProductoAsociado.objects.create(
                    nombre=p_nombre,
                    extension='',
                    proyecto=proyecto
                )
            ActividadDifusion_Producto.objects.get_or_create(
                actividad=actividad_obj,
                producto_asociado=producto_obj
            )

        # Líneas de trabajo asociadas
        lineas_str = row.get(COL_LINEA, '')
        lineas = [l.strip() for l in str(lineas_str).split(';') if l.strip()]
        for l_nombre in lineas:
            linea_obj, _ = LineaTrabajo.objects.get_or_create(
                proyecto=proyecto,
                nombre=l_nombre
            )
            ActividadDifusion_Linea.objects.get_or_create(
                actividad=actividad_obj,
                linea_trabajo=linea_obj
            )

        # Fechas según X: reutilizamos date_cols y fechas_reales
        bloques = detectar_bloques_x(row, date_cols)
        for inicio_col, fin_col in bloques:
            fecha_inicio = fechas_reales.get(inicio_col)
            fecha_fin = fechas_reales.get(fin_col)
            if fecha_inicio and fecha_fin:
                Fecha.objects.create(
                    actividad=actividad_obj,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin
                )

                # Actualizar fechas del proyecto si corresponde
                if proyecto.fecha_inicio is None or fecha_inicio < proyecto.fecha_inicio:
                    proyecto.fecha_inicio = fecha_inicio
                if proyecto.fecha_fin is None or fecha_fin > proyecto.fecha_fin:
                    proyecto.fecha_fin = fecha_fin
                proyecto.save()

        # Encargados
        responsables = row.get(COL_RESPONSABLE, '')
        if pd.notna(responsables):
            for r in str(responsables).split('y'):
                r = r.strip()
                if r:
                    encargado_obj = Encargado.objects.filter(nombre__iexact=r).first()
                    if not encargado_obj:
                        encargado_obj = Encargado.objects.create(nombre=r, correo_electronico='')
                    ActividadDifusion_Encargado.objects.get_or_create(
                        actividad=actividad_obj,
                        encargado=encargado_obj
                    )

# =========================
# Función de importación general
# =========================
def importar_gantt(nombre_proyecto, archivo_excel):
    """Importa un Excel Gantt a Django."""
    if not archivo_excel.name.endswith(('.xls', '.xlsx')):
        raise FormatoInvalidoError("El archivo debe ser Excel (.xls o .xlsx)")

    df_normales, df_difusion = separar_tablas_excel(archivo_excel)

    with transaction.atomic():
        proyecto, date_cols, fechas_reales = crear_proyecto_con_actividades_normales(nombre_proyecto, df_normales)
        # ---- Aquí conviertes fechas_reales a formato plano para difusión ----
        fechas_reales_planas = {}
        for k, v in fechas_reales.items():
            if isinstance(k, tuple):
                fechas_reales_planas[k[1]] = v  # usamos solo el nombre de columna
            else:
                fechas_reales_planas[k] = v
        date_cols_normales = list(fechas_reales_planas.keys())
        validar_columnas_difusion(df_difusion)
        crear_actividades_difusion(proyecto, df_difusion, date_cols_normales, fechas_reales_planas)
