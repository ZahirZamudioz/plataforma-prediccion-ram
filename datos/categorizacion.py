import pandas as pd
import datetime
import re
import os
from typing import Dict, Tuple, Optional, List, Any
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def cargar_datos(ruta: str) -> pd.DataFrame:
    try:
        if not Path(ruta).is_file():
            raise FileNotFoundError(f"El archivo {ruta} no existe.")
        return pd.read_excel(ruta)
    except Exception as e:
        raise ValueError(f"Error al cargar el archivo {ruta}: {str(e)}")

def cargar_diccionario(ruta: str, columnas: list, llave: str, valor: str) -> Dict[str, str]:
    try:
        df = pd.read_excel(ruta, usecols=columnas).dropna()
        return dict(zip(df[llave], df[valor]))
    except Exception as e:
        raise ValueError(f"Error al cargar diccionario desde {ruta}: {str(e)}")
    
def renombrar_columnas(df: pd.DataFrame, diccionario: Dict[str, str]) -> pd.DataFrame:
    return df.rename(columns={k: v for k, v in diccionario.items() if k in df.columns})

def reemplazar_valores(df: pd.DataFrame, columna: str, diccionario: Dict[str, str]) -> pd.DataFrame:
    if columna in df.columns:
        df[columna] = df[columna].replace(diccionario)
    return df

def detectar_columna_antibioticos(df: pd.DataFrame, antibioticos: pd.DataFrame, variantes: list) -> Optional[str]:
    columnas_en_data = set(df.columns)
    for variante in variantes:
        posibles_ab = set(antibioticos[variante].dropna())
        if len(posibles_ab & columnas_en_data) > 0:
            return variante
    # Archivos que ya usan los nombres finales en español (p. ej. "Amicacina").
    finales = set(antibioticos["antibiotico"].dropna())
    if len(finales & columnas_en_data) > 0:
        return "antibiotico"
    return None

def detectar_columna_especies(df: pd.DataFrame, especies: pd.DataFrame, columnas_codigo: list) -> Optional[str]:
    posibles_valores = set(df.values.ravel())
    for col_mapeo in columnas_codigo:
        codigos = set(especies[col_mapeo].dropna())
        if len(codigos & posibles_valores) > 0:
            return col_mapeo
    return None

def corregir_celdas_convertidas_a_fecha(df: pd.DataFrame, columnas: list) -> pd.DataFrame:
    for col in columnas:
        if col in df.columns:
            def corregir_valor(valor):
                if isinstance(valor, (pd.Timestamp, datetime.datetime)):
                    return f"{valor.day}/{valor.month}"
                return valor
            df[col] = df[col].apply(corregir_valor)
    return df

def eliminar_columnas_no_deseadas(df: pd.DataFrame, columnas: List[str]) -> pd.DataFrame:
    columnas_eliminadas = [col for col in columnas if col in df.columns]
    return df.drop(columns=columnas_eliminadas, errors='ignore')

def limpiar_valores_antibioticos(df: pd.DataFrame, columnas_antibioticos: List[str], valores_a_reemplazar: List[str]) -> pd.DataFrame:
    columnas_presentes = [col for col in columnas_antibioticos if col in df.columns]
    df[columnas_presentes] = df[columnas_presentes].replace(valores_a_reemplazar, pd.NA)
    return df

def agregar_columnas_mapeadas(df: pd.DataFrame, ruta_mapeo: str, columna_base: str) -> pd.DataFrame:
    mapeo_especies = cargar_datos(ruta_mapeo)
    dicc_grupo_general = dict(zip(mapeo_especies['Especie_especifica'], mapeo_especies['Grupo_general']))
    dicc_grupo_principal = dict(zip(mapeo_especies['Especie_especifica'], mapeo_especies['Grupo_principal']))
        
    if columna_base in df.columns:
        df['Grupo_general'] = df[columna_base].map(dicc_grupo_general)
        df['Grupo_principal'] = df[columna_base].map(dicc_grupo_principal)

    return df

def limpiar_valores_mic(df: pd.DataFrame, columnas_antibioticos: List[str]) -> pd.DataFrame:
    def transformar_mic(valor):
        if pd.isna(valor):
            return pd.NA
        valor = str(valor).strip()
        # Eliminar fracciones (por ejemplo: 16/4 → 16)
        if '/' in valor:
            valor = valor.split('/')[0].strip()
        try:
            if valor.startswith('>=') or valor.startswith('<=') or valor.startswith('='):
                num = float(valor.replace('>=', '').replace('<=', '').replace('=', '').replace(',', '.'))
                return num
            elif valor.startswith('>'):
                num = float(valor[1:].replace(',', '.'))
                return num * 2
            elif valor.startswith('<'):
                num = float(valor[1:].replace(',', '.'))
                return num / 2
            else:
                return float(valor.replace(',', '.'))
        except (ValueError, TypeError):
            return pd.NA

    columnas_presentes = [col for col in columnas_antibioticos if col in df.columns]
    for col in columnas_presentes:
        df[col] = df[col].apply(transformar_mic)
    return df

def cargar_puntos_corte_clsi(ruta_clsi: str) -> Tuple[Dict, Dict]:
    
    try:
        # Cargar archivo de puntos de corte
        clsi_df = pd.read_excel(
            ruta_clsi,
            usecols=['Antibiotico', 'Grupo_general', 'Grupo/Especie especifica',
                     'CLSI <=S', 'CLSI =I/SDD', 'CLSI >=R',
                     'CLSI >=S', 'CLSI =I', 'CLSI <=R']
        )
        
        # Funciones auxiliares
        def limpiar_mic(valor):
            if pd.isna(valor):
                return None
            valor = str(valor).split('/')[0].strip().replace(',', '.')
            return valor
        
        def es_numero(valor):
            if valor is None:
                return False
            return re.match(r'^\d+(\.\d+)?$', valor) is not None
        
        def limpiar_intermedio(valor):
            if pd.isna(valor):
                return None
            valor = str(valor).strip().replace(',', '.')
            if re.match(r'^\d+(\.\d+)?-\d+(\.\d+)?$', valor):
                return 'rango'
            if es_numero(valor):
                return float(valor)
            return None
        
        # Diccionarios de puntos de corte
        puntos_corte_clasico = {}
        puntos_corte_alterno = {}
        
        for _, fila in clsi_df.iterrows():
            antibiotico = str(fila['Antibiotico']).strip()
            grupo_general = str(fila['Grupo_general']).strip()
            grupo_especifico = str(fila['Grupo/Especie especifica']).strip()
            
            # Detectar si es un caso de exclusión
            modo_exclusion = False
            especies_excluidas = []
            especies_incluidas = []
            if grupo_especifico.lower().startswith("diferente:"):
                modo_exclusion = True
                especies_str = grupo_especifico.split(":", 1)[1].strip()
                especies_excluidas = [e.strip() for e in especies_str.split(",") if e.strip()]
            elif grupo_especifico.lower() != 'nan' and grupo_especifico.strip() != "":
                especies_incluidas = [e.strip() for e in grupo_especifico.split(",") if e.strip()]
            
            # --- Método clásico ---
            s = limpiar_mic(fila['CLSI <=S'])
            i = limpiar_intermedio(fila['CLSI =I/SDD'])
            r = limpiar_mic(fila['CLSI >=R'])
            if es_numero(s) and es_numero(r):
                if modo_exclusion:
                    puntos_corte_clasico[(antibiotico, grupo_general, True, tuple(especies_excluidas))] = (float(s), i, float(r))
                else:
                    for especie in especies_incluidas:
                        puntos_corte_clasico[(antibiotico, especie, False, None)] = (float(s), i, float(r))
                    puntos_corte_clasico[(antibiotico, grupo_general, False, None)] = (float(s), i, float(r))
            
            # --- Método alterno ---
            s_alt = limpiar_mic(fila['CLSI >=S'])
            i_alt = limpiar_intermedio(fila['CLSI =I'])
            r_alt = limpiar_mic(fila['CLSI <=R'])
            if es_numero(s_alt) and es_numero(r_alt):
                if modo_exclusion:
                    puntos_corte_alterno[(antibiotico, grupo_general, True, tuple(especies_excluidas))] = (float(s_alt), i_alt, float(r_alt))
                else:
                    for especie in especies_incluidas:
                        puntos_corte_alterno[(antibiotico, especie, False, None)] = (float(s_alt), i_alt, float(r_alt))
                    puntos_corte_alterno[(antibiotico, grupo_general, False, None)] = (float(s_alt), i_alt, float(r_alt))
        
        return clsi_df, puntos_corte_clasico, puntos_corte_alterno
    
    except Exception as e:
        raise ValueError(f"Error al cargar puntos de corte CLSI desde {ruta_clsi}: {str(e)}")

def sigue_patron_dilucion_doble(valor):
    try:
        valor = float(valor)
        if valor <= 0:
            return False
        while valor < 1:
            valor *= 2
        while valor > 1:
            valor /= 2
        return abs(valor - 1) < 0.0001
    except:
        return False

def buscar_puntos_corte(diccionario: Dict, antibiotico: str, especie: str, grupo: str) -> Optional[tuple]:
    if antibiotico is None:
        return None
    ant = str(antibiotico).strip().lower()
    esp = str(especie).strip().lower() if (especie is not None) else ""
    grp = str(grupo).strip().lower() if (grupo is not None) else ""
    # 1) coincidencia exacta por especie (modo_exclusion False, k_excl is None)
    for key, val in diccionario.items():
        k_ant, k_target, k_modo, k_excl = key
        if str(k_ant).strip().lower() != ant:
            continue
        if (not bool(k_modo)) and (k_excl is None):
            if str(k_target).strip().lower() == esp:
                return val
    # 2) reglas de exclusión (modo_exclusion True) para el grupo
    for key, val in diccionario.items():
        k_ant, k_target, k_modo, k_excl = key
        if str(k_ant).strip().lower() != ant:
            continue
        if bool(k_modo) and str(k_target).strip().lower() == grp:
            # k_excl expected to be tuple/list of excluded species
            if k_excl is None:
                return val
            excluded_lower = [e.strip().lower() for e in list(k_excl)]
            if esp not in excluded_lower:
                return val
            # si esp está en excluded_lower -> no aplica esta regla de exclusión (se ignora)
    # 3) coincidencia por grupo general (modo_exclusion False)
    for key, val in diccionario.items():
        k_ant, k_target, k_modo, k_excl = key
        if str(k_ant).strip().lower() != ant:
            continue
        if (not bool(k_modo)) and (k_excl is None) and str(k_target).strip().lower() == grp:
            return val
    return None

def categorizar_mic(valor: any, antibiotico_col: str, especie: str, grupo: str, puntos_corte_clasico: Dict, puntos_corte_alterno: Dict) -> any:
    if pd.isna(valor):
        return valor
    try:
        mic = float(valor)
    except:
        return 'Inconcluyente'
    # decidir método según patrón (diluciones dobles -> clásico)
    es_clasico = sigue_patron_dilucion_doble(mic)
    if es_clasico:
        puntos = buscar_puntos_corte(puntos_corte_clasico, antibiotico_col, especie, grupo)
        if puntos is None:
            return valor  # sin puntos de corte, dejamos el valor original
        s, i, r = puntos
        # Clasificación (método clásico: MIC <= S -> S, MIC >= R -> R, entre -> I si i existe)
        if mic <= s:
            return 'S'
        elif mic >= r:
            return 'R'
        elif (i not in [None, '']):
            if isinstance(i, (int, float)):  # si es un número, comparar igualdad exacta
                if mic == i:
                    return 'I'
            else:  # si no es numérico, usar el rango original
                if s < mic < r:
                    return 'I'
        else:
            return 'Inconcluyente'
    else:
        puntos = buscar_puntos_corte(puntos_corte_alterno, antibiotico_col, especie, grupo)
        if puntos is None:
            return valor
        s, i, r = puntos
        # Clasificación (método alterno: MIC >= S -> S, MIC <= R -> R, entre -> I si i existe)
        if mic >= s:
            return 'S'
        elif mic <= r:
            return 'R'
        elif (i not in [None, '']) and (r < mic < s):
            return 'I'
        else:
            return 'Inconcluyente'

def _normalizar_clave(valor):
    return str(valor).strip().lower() if (valor is not None and not pd.isna(valor)) else ""

def precomputar_puntos_corte(data: pd.DataFrame, columnas_ab: List[str],
                             puntos_corte_clasico: Dict, puntos_corte_alterno: Dict) -> Dict:
    """Construye una sola vez el lookup {col: {especie: (ptos_clasico, ptos_alterno)}}.

    La búsqueda de puntos de corte depende únicamente de (antibiótico, especie,
    grupo general), no del valor MIC. En lugar de recomputarla para cada celda
    (que recorre el diccionario 3 veces), la resolvemos para las combinaciones
    únicas presentes en los datos.
    """
    claves_especie = ["especie", "Grupo_general"]
    combinaciones = data[claves_especie].drop_duplicates().itertuples(index=False)
    lookup = {col: {} for col in columnas_ab}
    for especie, grupo in combinaciones:
        especie_l = _normalizar_clave(especie)
        grupo_l = _normalizar_clave(grupo)
        for col in columnas_ab:
            lookup[col][especie_l] = (
                buscar_puntos_corte(puntos_corte_clasico, col, especie_l, grupo_l),
                buscar_puntos_corte(puntos_corte_alterno, col, especie_l, grupo_l),
            )
    return lookup

def _clasificar_con_puntos(mic, es_clasico, pts_clasico, pts_alterno):
    """Aplica la misma clasificación que categorizar_mic pero con puntos ya resueltos."""
    if es_clasico:
        if pts_clasico is None:
            return mic
        s, i, r = pts_clasico
        if mic <= s:
            return 'S'
        elif mic >= r:
            return 'R'
        elif (i not in [None, '']):
            if isinstance(i, (int, float)):
                if mic == i:
                    return 'I'
            else:
                if s < mic < r:
                    return 'I'
        else:
            return 'Inconcluyente'
    else:
        if pts_alterno is None:
            return mic
        s, i, r = pts_alterno
        if mic >= s:
            return 'S'
        elif mic <= r:
            return 'R'
        elif (i not in [None, '']) and (r < mic < s):
            return 'I'
        else:
            return 'Inconcluyente'

def _categorizar_celda(mic, especie, col_lookup):
    if pd.isna(mic):
        return mic
    try:
        mic_f = float(mic)
    except (ValueError, TypeError):
        return 'Inconcluyente'
    es_clasico = sigue_patron_dilucion_doble(mic_f)
    pts = col_lookup.get(especie, (None, None))
    return _clasificar_con_puntos(mic_f, es_clasico, pts[0], pts[1])

def categorizar_dataframe(data: pd.DataFrame, puntos_corte_clasico: Dict, puntos_corte_alterno: Dict) -> pd.DataFrame:
    df_categorizado = data.copy()
    no_ab = {'Grupo_general', 'fecha', 'especie',
             'Grupo_principal', 'Tipo de localizacion', 'Tipo de muestra',
             'SPEC_NUM', 'Edad'}
    columnas_ab = [col for col in data.columns if col not in no_ab]

    lookup = precomputar_puntos_corte(data, columnas_ab, puntos_corte_clasico, puntos_corte_alterno)

    especies = data['especie'].map(_normalizar_clave).to_numpy()
    valores = df_categorizado[columnas_ab].to_numpy()

    for j, col in enumerate(columnas_ab):
        col_lookup = lookup[col]
        mic_col = valores[:, j]
        df_categorizado[col] = [
            _categorizar_celda(mic, especies[i], col_lookup)
            for i, mic in enumerate(mic_col)
        ]
    return df_categorizado

def procesar_dataset(df: pd.DataFrame, ruta_diccionarios: str) -> Tuple[pd.DataFrame, Dict[str, Dict]]:
    
    # Diccionarios para almacenar resultados
    diccionarios = {}
    
    # 1. Renombrar columnas principales
    dicc_variables = cargar_diccionario(
        ruta_diccionarios, 
        columnas=['variable_original', 'variable_nueva'],
        llave='variable_original',
        valor='variable_nueva'
    )
    data = renombrar_columnas(df, dicc_variables)
    
    # 2. Reemplazar valores de tipo de muestra
    dicc_muestras = cargar_diccionario(
        ruta_diccionarios,
        columnas=['codigo_muestra', 'nombre_muestra'],
        llave='codigo_muestra',
        valor='nombre_muestra'
    )
    data = reemplazar_valores(data, 'Tipo de muestra', dicc_muestras)
    diccionarios['dicc_muestras'] = dicc_muestras
    
    # 3. Reemplazar valores de tipo de servicio
    dicc_localizacion = cargar_diccionario(
        ruta_diccionarios,
        columnas=['codigo_localizacion', 'nombre_localizacion'],
        llave='codigo_localizacion',
        valor='nombre_localizacion'
    )
    data = reemplazar_valores(data, 'Tipo de localizacion', dicc_localizacion)
    diccionarios['dicc_localizacion'] = dicc_localizacion
    
    # 4. Procesar antibióticos
    antibioticos = cargar_datos(ruta_diccionarios)[['antibiotico_1', 'antibiotico_2', 'antibiotico_3', 'antibiotico_4', 'antibiotico']]
    variantes = ['antibiotico_1', 'antibiotico_2', 'antibiotico_3', 'antibiotico_4']
    columna_usada = detectar_columna_antibioticos(data, antibioticos, variantes)
    
    dicc_antibioticos = {}
    if columna_usada:
        if columna_usada == "antibiotico":
            # El archivo ya trae los nombres finales; el mapeo es identidad.
            dicc_antibioticos = {
                ab: ab for ab in antibioticos["antibiotico"].dropna().unique()
            }
        else:
            dicc_antibioticos = cargar_diccionario(
                ruta_diccionarios,
                columnas=[columna_usada, 'antibiotico'],
                llave=columna_usada,
                valor='antibiotico'
            )
        data = renombrar_columnas(data, dicc_antibioticos)
    diccionarios['dicc_antibioticos'] = dicc_antibioticos
    
    # 5. Procesar especies
    especies = cargar_datos(ruta_diccionarios)[['especie_1', 'especie_2', 'especie_3', 'especie']]
    columnas_codigo = ['especie_1', 'especie_2', 'especie_3']
    columna_usada = detectar_columna_especies(data, especies, columnas_codigo)
    
    dicc_especies = {}
    if columna_usada:
        dicc_especies = cargar_diccionario(
            ruta_diccionarios,
            columnas=[columna_usada, 'especie'],
            llave=columna_usada,
            valor='especie'
        )
        data = reemplazar_valores(data, 'especie', dicc_especies)
    diccionarios['dicc_especies'] = dicc_especies
    
    return data, diccionarios

# Ejecución principal
def procesar_categorizacion(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict, pd.DataFrame, Dict, Dict, Dict[str, Any]]:
    RUTA_DICCIONARIOS = os.path.join(BASE_DIR, "data", "Lista_antimicrobianos.xlsx")
    RUTA_MAPEO_ESPECIES = os.path.join(BASE_DIR, "data", "Lista_especie_especifico_general.xlsx")
    RUTA_CLSI = os.path.join(BASE_DIR, "data", "Lista_CLSI_completa.xlsx")

    reporte = {
        'total_registros_inicial': len(df),
        'registros_eliminados': 0,
        'columnas_eliminadas': [],
        'antibiotico_no_renombrados': [],
        'especies_no_renombradas': [],
        'combinaciones_sin_punto_corte': [],
        'observaciones': [],
        'valores_invalidos_reemplazados': 0,
    }

    # Procesar dataset
    data_procesado, diccionarios = procesar_dataset(df, RUTA_DICCIONARIOS)

    reporte['observaciones'].append("Renombramiento de columnas principales completado")
    
    # Corregir fechas en columnas de antibióticos
    columnas_antibioticos = [c for c in diccionarios['dicc_antibioticos'].values() if c in data_procesado.columns]
    data_corregido = corregir_celdas_convertidas_a_fecha(data_procesado, columnas_antibioticos)
    
    # Filtrar columnas finales
    columnas_a_conservar = ['fecha', 'SPEC_NUM', 'Tipo de localizacion', 'Tipo de muestra', 'Edad', 'especie'] + columnas_antibioticos
    columnas_existentes = [col for col in columnas_a_conservar if col in data_corregido.columns]
    data_filtrada = data_corregido[columnas_existentes]

    reporte['columnas_eliminadas'] = list(set(data_corregido.columns) - set(columnas_existentes))
    
    # Eliminar columnas no deseadas
    columnas_a_eliminar = [
        'BLEE',
        #'Gentamicina de nivel alto (sinergia)',
        #'Estreptomicina de nivel alto (sinergia)',
        'Resistencia inducible a clindamicina',
        'Deteccion de cefoxitina'
    ]
    
    # Solo eliminamos las que realmente existen → evita KeyError
    columnas_realmente_eliminadas = [col for col in columnas_a_eliminar if col in data_filtrada.columns]

    if columnas_realmente_eliminadas:
        data_filtrada = data_filtrada.drop(columns=columnas_realmente_eliminadas)
        reporte['observaciones'].append(
            f"Columnas de exclusión eliminadas: {', '.join(columnas_realmente_eliminadas)}"
        )
    else:
        reporte['observaciones'].append("No se encontraron columnas de exclusión para eliminar")

    data_filtrada = eliminar_columnas_no_deseadas(data_filtrada, columnas_a_eliminar)

    #eliminadas_final = [col for col in columnas_a_eliminar if col in data_corregido.columns]
    #if eliminadas_final:
        #reporte['observaciones'].append(f"Columnas específicas eliminadas: {', '.join(eliminadas_final)}")

    # Limpiar valores no deseados en columnas de antibióticos
    valores_a_reemplazar = ['TRM', 'R/N', 'NEG']
    data_filtrada = limpiar_valores_antibioticos(data_filtrada, columnas_antibioticos, valores_a_reemplazar)
    
    # Contar reemplazos
    reporte['valores_invalidos_reemplazados'] = data_filtrada[columnas_antibioticos].isna().sum().sum()

    # Agregar columnas mapeadas
    data_filtrada = agregar_columnas_mapeadas(data_filtrada, RUTA_MAPEO_ESPECIES, 'especie')

    # Registrar especies no mapeadas
    especies_no_mapeadas = data_filtrada[data_filtrada['Grupo_general'].isna()]['especie'].unique()
    if len(especies_no_mapeadas) > 0:
        reporte['observaciones'].append(f"Especies sin grupo mapeado: {', '.join(especies_no_mapeadas[:10])} {'(... y más)' if len(especies_no_mapeadas)>10 else ''}")

    # Limpiar valores MIC en columnas de antibióticos
    data_filtrada = limpiar_valores_mic(data_filtrada, columnas_antibioticos)

    # Cargar puntos de corte CLSI
    clsi_df, puntos_corte_clasico, puntos_corte_alterno = cargar_puntos_corte_clsi(RUTA_CLSI)
    
    # Registrar combinaciones sin punto de corte (misma lógica de categorización).
    # La búsqueda de puntos de corte solo depende de (antibiótico, especie, grupo),
    # por lo que basta con revisar las combinaciones únicas en lugar de cada celda.
    sin_corte = set()

    # Para cada especie, conservar su grupo general (primer valor no nulo).
    mapa_grupo = (
        data_filtrada[['especie', 'Grupo_general']]
        .dropna(subset=['especie'])
        .drop_duplicates(subset=['especie'])
    )
    grupo_por_especie = dict(zip(mapa_grupo['especie'], mapa_grupo['Grupo_general']))

    for col in columnas_antibioticos:
        present_col = data_filtrada[data_filtrada[col].notna()]
        for especie in present_col['especie'].unique():
            grupo = grupo_por_especie.get(especie)
            pts_clasico = buscar_puntos_corte(puntos_corte_clasico, col, especie, grupo)
            pts_alterno = buscar_puntos_corte(puntos_corte_alterno, col, especie, grupo)
            if pts_clasico is None and pts_alterno is None:
                sin_corte.add(f"{especie} → {col}")

    reporte['combinaciones_sin_punto_corte'] = sorted(sin_corte)

    
    # Categorizar valores MIC
    data_filtrada = categorizar_dataframe(data_filtrada, puntos_corte_clasico, puntos_corte_alterno)

    # Final
    reporte['registros_eliminados'] = reporte['total_registros_inicial'] - len(data_filtrada)

    return data_filtrada, diccionarios, clsi_df, puntos_corte_clasico, puntos_corte_alterno, reporte