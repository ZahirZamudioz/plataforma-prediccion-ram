"""Configuración y constantes compartidas del proyecto."""
import os

# Directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Directorio de datos procesados (pickles)
DATA_DIR = os.path.join(BASE_DIR, "data")

# Raíz de almacenamiento por sesión. Por defecto usa data/; puede apuntarse a
# otro volumen local con la variable de entorno STORAGE_ROOT.
STORAGE_ROOT = os.getenv("STORAGE_ROOT", DATA_DIR)

# Archivos fuente de diccionarios de mapeo y puntos de corte CLSI
RUTA_DICCIONARIOS = os.path.join(BASE_DIR, "data", "Lista_antimicrobianos.xlsx")
RUTA_MAPEO_ESPECIES = os.path.join(BASE_DIR, "data", "Lista_especie_especifico_general.xlsx")
RUTA_CLSI = os.path.join(BASE_DIR, "data", "Lista_CLSI_completa.xlsx")

# Colores fijos por especie para los gráficos
COLORES_ESPECIES = {
    "Acinetobacter baumannii": "blue",
    "Klebsiella pneumoniae": "orange",
    "Escherichia coli": "red",
    "Pseudomonas aeruginosa": "green",
    "Staphylococcus aureus": "black",
}

# Especies de interés para el gráfico de resistencia en el tiempo
ESPECIES_FIJAS = [
    "Acinetobacter baumannii",
    "Klebsiella pneumoniae",
    "Escherichia coli",
    "Pseudomonas aeruginosa",
    "Staphylococcus aureus",
]

# Meses en español (para ordenar el eje temporal)
MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]
