import pandas as pd


def calcular_conteos_porcentajes(data_filtrada):
    columnas_id = ['fecha', 'especie', 'Grupo_principal']
    columnas_antibioticos = [col for col in data_filtrada.columns if col not in ['fecha', 'SPEC_NUM', 'Tipo de localizacion',
                            'Tipo de muestra', 'Edad', 'especie', 'Grupo_general', 'Grupo_principal']]
    
    df_melted = pd.melt(data_filtrada,
                        id_vars=columnas_id,
                        value_vars=columnas_antibioticos,
                        var_name='antibiotico',
                        value_name='CLSI_categoria')
    
    count_table = pd.pivot_table(df_melted,
                                index=['fecha', 'Grupo_principal','especie', 'antibiotico'],
                                columns='CLSI_categoria',
                                aggfunc='size',
                                fill_value=0)
    
    count_table = count_table.reset_index()
    count_table.index.names = ['Index']
    
    for col in ['I', 'R', 'S', 'Inconcluyente']:
        if col not in count_table.columns:
            count_table[col] = 0
    
    count_table['total'] = count_table['I'] + count_table['R'] + count_table['S'] + count_table['Inconcluyente']
    count_table['I (%)'] = (count_table['I'] / count_table['total'] * 100).round(2)
    count_table['R (%)'] = (count_table['R'] / count_table['total'] * 100).round(2)
    count_table['S (%)'] = (count_table['S'] / count_table['total'] * 100).round(2)
    count_table['Inconcluyente (%)'] = (count_table['Inconcluyente'] / count_table['total'] * 100).round(2)
    
    return count_table


def transformar_datos_para_aislados_barras(data_filtrada):
    # Agrupar y contar aislados por especie
    if "Grupo_principal" in data_filtrada.columns:
        conteo_especies = (
            data_filtrada.groupby(["especie", "Grupo_principal"])
            .size()
            .reset_index(name="aislados")
        )
    else:
        conteo_especies = (
            data_filtrada.groupby("especie")
            .size()
            .reset_index(name="aislados")
        )

    # Ordenar especies de mayor a menor
    conteo_especies = conteo_especies.sort_values("aislados", ascending=False)

    orden_especies = (
        conteo_especies["especie"]
        .astype(str).str.strip()
        .drop_duplicates()
        .tolist()
    )
    return conteo_especies, orden_especies


def transformar_datos_para_heatmap(data_filtrada, conteo_especies):
    # Dividir los datos en Gram positivas y Gram negativas
    gram_positiva = data_filtrada[data_filtrada["Grupo_principal"] == "Gram positiva"]
    gram_negativa = data_filtrada[data_filtrada["Grupo_principal"] == "Gram negativa"]

    # Función auxiliar para procesar cada grupo
    # Agrupar por especie y antibiótico, sumar counts, y calcular todos los porcentajes globales
    def procesar_grupo(df_grupo, orden_especies):
        df_heatmap_grouped = (
            df_grupo.groupby(["especie", "antibiotico"])
            .agg({"R": "sum", "S": "sum", "I": "sum", "Inconcluyente": "sum", "total": "sum"})
            .reset_index()
        )

        # Calcular porcentajes, redondeando a 1 decimal
        df_heatmap_grouped["R (%)"] = (df_heatmap_grouped["R"] / df_heatmap_grouped["total"] * 100).round(1)
        df_heatmap_grouped["S (%)"] = (df_heatmap_grouped["S"] / df_heatmap_grouped["total"] * 100).round(1)
        df_heatmap_grouped["I (%)"] = (df_heatmap_grouped["I"] / df_heatmap_grouped["total"] * 100).round(1)
        df_heatmap_grouped["Inconcluyente (%)"] = (df_heatmap_grouped["Inconcluyente"] / df_heatmap_grouped["total"] * 100).round(1)

        # Pivotar para porcentajes
        pivot_R = df_heatmap_grouped.pivot_table(
            index="especie",
            columns="antibiotico",
            values="R (%)",
            aggfunc="first"
        ).fillna("")  # Blanks para NaN

        pivot_S = df_heatmap_grouped.pivot_table(
            index="especie",
            columns="antibiotico",
            values="S (%)",
            aggfunc="first"
        ).fillna(0)

        pivot_I = df_heatmap_grouped.pivot_table(
            index="especie",
            columns="antibiotico",
            values="I (%)",
            aggfunc="first"
        ).fillna(0)

        pivot_Inconcluyente = df_heatmap_grouped.pivot_table(
            index="especie",
            columns="antibiotico",
            values="Inconcluyente (%)",
            aggfunc="first"
        ).fillna(0)

        # Ordenar las filas del heatmap usando el mismo orden de especies del gráfico de barras
        pivot_R = pivot_R.reindex(index=orden_especies)[sorted(pivot_R.columns)]

        # Asegurar que los otros pivots estén alineados
        pivot_S = pivot_S.reindex(index=pivot_R.index, columns=pivot_R.columns).fillna(0)
        pivot_I = pivot_I.reindex(index=pivot_R.index, columns=pivot_R.columns).fillna(0)
        pivot_Inconcluyente = pivot_Inconcluyente.reindex(index=pivot_R.index, columns=pivot_R.columns).fillna(0)

        # Pivotar los conteos originales
        pivot_R_count = df_heatmap_grouped.pivot_table(
            index="especie",
            columns="antibiotico",
            values="R",
            aggfunc="first"
        ).reindex(index=pivot_R.index, columns=pivot_R.columns).fillna(0)

        pivot_S_count = df_heatmap_grouped.pivot_table(
            index="especie",
            columns="antibiotico",
            values="S",
            aggfunc="first"
        ).reindex(index=pivot_R.index, columns=pivot_R.columns).fillna(0)

        pivot_I_count = df_heatmap_grouped.pivot_table(
            index="especie",
            columns="antibiotico",
            values="I",
            aggfunc="first"
        ).reindex(index=pivot_R.index, columns=pivot_R.columns).fillna(0)

        pivot_Inconcluyente_count = df_heatmap_grouped.pivot_table(
            index="especie",
            columns="antibiotico",
            values="Inconcluyente",
            aggfunc="first"
        ).reindex(index=pivot_R.index, columns=pivot_R.columns).fillna(0)

        return (pivot_R, pivot_S, pivot_I, pivot_Inconcluyente,
                pivot_R_count, pivot_S_count, pivot_I_count, pivot_Inconcluyente_count)
    
    # Obtener el orden de especies por grupo
    orden_positivas = conteo_especies[conteo_especies["Grupo_principal"] == "Gram positiva"]["especie"].drop_duplicates().tolist()
    orden_negativas = conteo_especies[conteo_especies["Grupo_principal"] == "Gram negativa"]["especie"].drop_duplicates().tolist()

    # Procesar ambos grupos
    pivots_positivas = procesar_grupo(gram_positiva, orden_positivas)
    pivots_negativas = procesar_grupo(gram_negativa, orden_negativas)

    return pivots_positivas, pivots_negativas


def trasformar_datos_tipo_de_servicio(data_filtrada):
    # Crear una copia para no modificar el DataFrame original
    df_unicos = data_filtrada.copy()

    # Eliminar duplicados basados en SPEC_NUM, barajando aleatoriamente
    if "SPEC_NUM" in df_unicos.columns:
        df_unicos = df_unicos.sample(frac=1, random_state=42).drop_duplicates("SPEC_NUM", keep="first")

    # Calcular conteo y porcentaje para "Tipo de localización"
    if "Tipo de localizacion" in df_unicos.columns:
        conteo_servicio = df_unicos.groupby("Tipo de localizacion").size().reset_index(name="n")
        conteo_servicio["Porcentaje"] = (conteo_servicio["n"] / conteo_servicio["n"].sum() * 100).round(2)
        conteo_servicio = conteo_servicio.sort_values("Porcentaje", ascending=False)

        # Crear DataFrame para la tabla con la fila de total
        total_row = pd.DataFrame({
            "Tipo de localizacion": ["Total"],
            "n": [conteo_servicio["n"].sum()],
            "Porcentaje": [100.0]
        })
        conteo_servicio_tabla = pd.concat([conteo_servicio, total_row], ignore_index=True)
    else:
        conteo_servicio = pd.DataFrame(columns=["Tipo de localizacion", "n", "Porcentaje"])
        conteo_servicio_tabla = conteo_servicio
    
    return conteo_servicio, conteo_servicio_tabla, df_unicos


def transformar_datos_para_frecuencia_tipo_muestra(df_unicos):
    # Calcular conteo y porcentaje para "Tipo de muestra"
    if "Tipo de muestra" in df_unicos.columns:
        conteo_muestra = df_unicos.groupby("Tipo de muestra").size().reset_index(name="n")
        conteo_muestra["Porcentaje"] = (conteo_muestra["n"] / conteo_muestra["n"].sum() * 100).round(2)
        conteo_muestra = conteo_muestra.sort_values("Porcentaje", ascending=False)

        # Identificar categorías infrecuentes (porcentaje < 1%)
        infrecuentes = conteo_muestra[(conteo_muestra["Porcentaje"] < 1.0) & (conteo_muestra["Tipo de muestra"] != "Otros")]

        if not infrecuentes.empty:
            # Calcular total de muestras y porcentaje de categorías infrecuentes
            total_infrecuentes_n = infrecuentes["n"].sum()
            total_infrecuentes_pct = infrecuentes["Porcentaje"].sum()
            
            # Crear fila para "Muestras infrecuentes"
            muestras_infrecuentes_row = pd.DataFrame({
                "Tipo de muestra": ["Muestras infrecuentes"],
                "n": [total_infrecuentes_n],
                "Porcentaje": [round(total_infrecuentes_pct, 2)]
            })
            
            # Filtrar solo categorías frecuentes (>= 1%)
            categorias_frecuentes = conteo_muestra[(conteo_muestra["Porcentaje"] >= 1.0) | (conteo_muestra["Tipo de muestra"] == "Otros")]
            
            # Combinar categorías frecuentes con "Muestras infrecuentes"
            conteo_muestra = pd.concat([categorias_frecuentes, muestras_infrecuentes_row], ignore_index=True)

        # Ordenar por porcentaje descendente
        conteo_muestra = conteo_muestra.sort_values("Porcentaje", ascending=False).reset_index(drop=True)

        # Crear DataFrame para la tabla (misma lógica que para el gráfico)
        conteo_muestra_tabla = conteo_muestra.copy()

        # Crear DataFrame para la tabla con la fila de total
        total_row = pd.DataFrame({
            "Tipo de muestra": ["Total"],
            "n": [conteo_muestra["n"].sum()],
            "Porcentaje": [100.0]
        })
        conteo_muestra_tabla = pd.concat([conteo_muestra, total_row], ignore_index=True)
    else:
        conteo_muestra = pd.DataFrame(columns=["Tipo de muestra", "n", "Porcentaje"])
        conteo_muestra_tabla = conteo_muestra

    return conteo_muestra, conteo_muestra_tabla


def transformar_datos_para_edad(df_unicos):
    # Función para convertir edades a años
    def convertir_edad(edad):
        if pd.isna(edad):
            return None
        edad_str = str(edad).strip().upper()
        if 'M' in edad_str:
            try:
                meses = float(edad_str.replace('M', ''))
                return meses / 12
            except ValueError:
                return None
        elif 'D' in edad_str:
            try:
                dias = float(edad_str.replace('D', ''))
                return dias / 365
            except ValueError:
                return None
        else:
            try:
                return float(edad_str)
            except ValueError:
                return None

    # Aplicar la conversión a la columna "Edad"
    df_unicos['Edad_num'] = df_unicos['Edad'].apply(convertir_edad)

    # Definir rangos de edad
    rangos_edad = [
        "Neonatal", "1-5 meses", "6-11 meses", "1-2 años", "2-4 años", "5-9 años",
        "10-14 años", "15-19 años", "20-24 años", "25-29 años", "30-34 años",
        "35-39 años", "40-44 años", "45-49 años", "50-54 años", "55-59 años",
        "60-64 años", "65-69 años", "70-74 años", "75-79 años", "80-84 años",
        "85-89 años", "90-94 años", "≥95 años"
    ]

    # Función para asignar rango de edad
    def asignar_rango(edad):
        if pd.isna(edad):
            return None
        elif edad <= 1/12:  # Menos de 1 mes (aprox. 28 días)
            return "Neonatal"
        elif 1/12 < edad <= 5/12:
            return "1-5 meses"
        elif 5/12 < edad <= 11/12:
            return "6-11 meses"
        elif 1 <= edad <= 2:
            return "1-2 años"
        elif 2 < edad <= 4:
            return "2-4 años"
        elif 5 <= edad <= 9:
            return "5-9 años"
        elif 10 <= edad <= 14:
            return "10-14 años"
        elif 15 <= edad <= 19:
            return "15-19 años"
        elif 20 <= edad <= 24:
            return "20-24 años"
        elif 25 <= edad <= 29:
            return "25-29 años"
        elif 30 <= edad <= 34:
            return "30-34 años"
        elif 35 <= edad <= 39:
            return "35-39 años"
        elif 40 <= edad <= 44:
            return "40-44 años"
        elif 45 <= edad <= 49:
            return "45-49 años"
        elif 50 <= edad <= 54:
            return "50-54 años"
        elif 55 <= edad <= 59:
            return "55-59 años"
        elif 60 <= edad <= 64:
            return "60-64 años"
        elif 65 <= edad <= 69:
            return "65-69 años"
        elif 70 <= edad <= 74:
            return "70-74 años"
        elif 75 <= edad <= 79:
            return "75-79 años"
        elif 80 <= edad <= 84:
            return "80-84 años"
        elif 85 <= edad <= 89:
            return "85-89 años"
        elif 90 <= edad <= 94:
            return "90-94 años"
        elif edad >= 95:
            return "≥95 años"
        return None

    # Asignar rangos de edad
    df_unicos['Rango_edad'] = df_unicos['Edad_num'].apply(asignar_rango)

    # Calcular conteo por rango de edad
    conteo_edad = df_unicos.groupby('Rango_edad').size().reset_index(name='n')
    # Ordenar por rango de edad (de menor a mayor edad) corrigiendo el error
    conteo_edad['Orden'] = conteo_edad['Rango_edad'].apply(lambda x: rangos_edad.index(x) if x in rangos_edad else len(rangos_edad))
    conteo_edad = conteo_edad.sort_values('Orden').drop(columns=['Orden'])

    return conteo_edad


def transformar_datos_para_muestras_por_servicio(df_unicos):
    # Crear una copia para no modificar el DataFrame original
    df_temp = df_unicos.copy()

    # Identificar tipos de muestra poco frecuentes (<1%)
    conteo_muestras = df_temp.groupby('Tipo de muestra').size().reset_index(name='Conteo')
    conteo_muestras['Porcentaje'] = (conteo_muestras['Conteo'] / conteo_muestras['Conteo'].sum() * 100).round(2)
    muestras_infrecuentes = conteo_muestras[conteo_muestras['Porcentaje'] < 1]['Tipo de muestra'].tolist()
    df_temp['Tipo de muestra'] = df_temp['Tipo de muestra'].replace(muestras_infrecuentes, 'muestras infrecuentes')

    # Crear tabla pivot para conteo por servicio y tipo de muestra
    conteo_servicio_muestras = df_temp.pivot_table(
        index=['Tipo de localizacion', 'Tipo de muestra'],
        aggfunc='size'
    ).reset_index(name='Conteo')

    # Calcular porcentajes por grupo de 'Tipo de localizacion'
    totales_por_servicio = conteo_servicio_muestras.groupby('Tipo de localizacion')['Conteo'].transform('sum')
    conteo_servicio_muestras['Porcentaje'] = (conteo_servicio_muestras['Conteo'] / totales_por_servicio * 100).round(2)

    # Ordenar 'Tipo de localizacion' por conteo total
    totales_servicios = conteo_servicio_muestras.groupby('Tipo de localizacion')['Conteo'].sum().sort_values(ascending=False)
    orden_servicios = totales_servicios.index.tolist()

    # Ordenar 'Tipo de muestra' por conteo total
    totales_tipos_muestra = conteo_servicio_muestras.groupby('Tipo de muestra')['Conteo'].sum().sort_values(ascending=False)
    orden_tipos_muestra = totales_tipos_muestra.index.tolist()

    # Convertir a tipos categóricos para ordenar la tabla
    conteo_servicio_muestras['Tipo de localizacion'] = pd.Categorical(
        conteo_servicio_muestras['Tipo de localizacion'],
        categories=orden_servicios,
        ordered=True
    )
    conteo_servicio_muestras['Tipo de muestra'] = pd.Categorical(
        conteo_servicio_muestras['Tipo de muestra'],
        categories=orden_tipos_muestra,
        ordered=True
    )
    conteo_servicio_muestras = conteo_servicio_muestras.sort_values(by=['Tipo de localizacion', 'Tipo de muestra'])

    return conteo_servicio_muestras, orden_servicios, orden_tipos_muestra, muestras_infrecuentes


def transformar_datos_para_especies_por_muestra(df_actual, muestras_infrecuentes):
    # Crear una copia para no modificar el DataFrame original
    df_temp = df_actual.copy()

    # Identificar tipos de muestra poco frecuentes (<3%)
    conteo_especie = df_temp.groupby('especie').size().reset_index(name='Conteo')
    conteo_especie['Porcentaje'] = (conteo_especie['Conteo'] / conteo_especie['Conteo'].sum() * 100).round(2)
    #conteo_especies = conteo_especies.sort_values(by="Conteo", ascending=False)
    especies_infrecuentes = conteo_especie[conteo_especie['Porcentaje'] < 3]['especie'].tolist()

    # Reemplazar especies poco frecuentes
    df_temp['especie'] = df_temp['especie'].replace(especies_infrecuentes, 'otras especies')

    # Reemplazar tipos de muestra poco frecuentes
    df_temp['Tipo de muestra'] = df_temp['Tipo de muestra'].replace(muestras_infrecuentes, 'muestras infrecuentes')

    # Crear tabla pivote para conteo por tipo de muestra por especies
    conteo_muestra_especies = df_temp.pivot_table(
        index=['Tipo de muestra', 'especie'],
        aggfunc='size'
    ).reset_index(name='Conteo')

    # Calcular porcentajes por grupo de 'Tipo de muestra'
    totales_por_muestra = conteo_muestra_especies.groupby('Tipo de muestra')['Conteo'].transform('sum')
    conteo_muestra_especies['Porcentaje'] = (conteo_muestra_especies['Conteo'] / totales_por_muestra * 100).round(2)

    # Ordenar 'Tipo de muestra' por conteo total
    totales_muestras = conteo_muestra_especies.groupby('Tipo de muestra')['Conteo'].sum().sort_values(ascending=False)
    orden_muestras = totales_muestras.index.tolist()

    # Ordenar 'especies' por conteo total
    totales_especies = conteo_muestra_especies.groupby('especie')['Conteo'].sum().sort_values(ascending=False)
    orden_de_especies = totales_especies.index.tolist()

    # Convertir a tipos categóricos para ordenar la tabla
    conteo_muestra_especies['Tipo de muestra'] = pd.Categorical(
        conteo_muestra_especies['Tipo de muestra'],
        categories=orden_muestras,
        ordered=True
    )
    conteo_muestra_especies['especie'] = pd.Categorical(
        conteo_muestra_especies['especie'],
        categories=orden_de_especies,
        ordered=True
    )
    conteo_muestra_especies = conteo_muestra_especies.sort_values(by=['Tipo de muestra', 'Porcentaje'], ascending=[True, False])

    return conteo_muestra_especies, orden_muestras, orden_de_especies
