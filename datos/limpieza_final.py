import pandas as pd

# Convierte la columna 'fecha' a formato datetime
def convertir_fechas_a_datetime(df):
    df = df.copy()
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
    return df

# Reordena las columnas del DataFrame colocando las columnas de inicio al principio
def reordenar_columnas(df, columnas_inicio):
    otras_columnas = [col for col in df.columns if col not in columnas_inicio]
    return df[columnas_inicio + otras_columnas]

# Formatea la columna 'fecha' a string con meses en español
def formatear_fechas(df):
    df = df.copy()
    df['fecha'] = df['fecha'].apply(lambda x: x.strftime('%B-%Y') if pd.notna(x) else pd.NA)
    meses_traduccion = {
        'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo', 'April': 'Abril',
        'May': 'Mayo', 'June': 'Junio', 'July': 'Julio', 'August': 'Agosto',
        'September': 'Septiembre', 'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre'
    }
    df['fecha'] = df['fecha'].replace(meses_traduccion, regex=True)
    return df

# Limpia las columnas de antibióticos reemplazando valores numéricos y vacíos por NA, 
# y elimina columnas completamente vacías y filas sin datos en antibióticos
def limpiar_datos_antibioticos(df, columnas_fijas):
    
    # Identificar columnas de antibióticos
    antibioticos = [col for col in df.columns if col not in columnas_fijas]
    
    # Reemplazar valores numéricos por NA
    for col in antibioticos:
        df[col] = df[col].apply(lambda x: pd.NA if isinstance(x, (int, float)) or 
                               (isinstance(x, str) and x.replace('.', '', 1).isdigit()) else x)
    
    # Reemplazar valores vacíos por NA
    df[antibioticos] = df[antibioticos].replace('', pd.NA)
    
    # Detectar columnas completamente vacías
    columnas_vacias = [col for col in antibioticos if df[col].isna().all()]
    
    # Eliminar filas sin datos en ninguna columna de antibióticos (excluyendo vacías)
    df_limpio = df.dropna(subset=[col for col in antibioticos if col not in columnas_vacias], how='all')
    
    # Eliminar columnas vacías
    df_limpio = df_limpio.drop(columns=columnas_vacias)
    
    return df_limpio, columnas_vacias

def procesar_limpieza_final(df):
    # Configuración inicial
    columnas_inicio = ['fecha', 'SPEC_NUM', 'Tipo de localizacion', 
                       'Tipo de muestra', 'Edad', 'especie', 'Grupo_general', 'Grupo_principal']
    columnas_fijas = ['fecha', 'Tipo de localizacion', 'Tipo de muestra', 
                      'especie', 'Grupo_general', 'Grupo_principal', 'SPEC_NUM', 'Edad']
    
    reporte_limpieza = {
        "registros_eliminados_anio": 0,
        "registros_eliminados_sin_antibioticos": 0,
        "columnas_antibioticos_vacias": []
    }

    # Pipeline de procesamiento
    df = convertir_fechas_a_datetime(df)
    df = reordenar_columnas(df, columnas_inicio)

    # Filtro por el año
    total_antes_anio = len(df)
    anio_predominante = df['fecha'].dt.year.mode()[0]
    df = df[df['fecha'].dt.year == anio_predominante]
    total_despues_anio = len(df)
    reporte_limpieza["registros_eliminados_anio"] = total_antes_anio - total_despues_anio

    df = formatear_fechas(df)

    # --- limpieza antibióticos ---
    total_antes_antibioticos = len(df)
    df_limpio, columnas_vacias = limpiar_datos_antibioticos(df, columnas_fijas)
    total_despues_antibioticos = len(df_limpio)
    reporte_limpieza["registros_eliminados_sin_antibioticos"] = (
        total_antes_antibioticos - total_despues_antibioticos
    )
    reporte_limpieza["columnas_antibioticos_vacias"] = columnas_vacias
    
    return df_limpio, reporte_limpieza
