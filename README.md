# Plataforma para el monitoreo de resistencia antimicrobiana

Aplicación web local desarrollada con **Dash/Plotly** para cargar resultados de
susceptibilidad antimicrobiana, analizar muestras y aislados, y generar
predicciones trimestrales de resistencia mediante modelos **ARIMA**, **SARIMA**
y **XGBoost**.

La plataforma normaliza los datos de entrada, clasifica los valores MIC como
**Sensible (S)**, **Intermedio (I)** o **Resistente (R)** usando los puntos de
corte **CLSI 2025**, y presenta los resultados en tableros interactivos.

> **Aviso:** esta herramienta es de carácter académico y de investigación. No es
> un dispositivo médico y sus predicciones no sustituyen el criterio clínico.

## Características

- Carga de archivos Excel (`.xlsx`) organizados por año.
- Normalización de columnas, especies, antibióticos, muestras y servicios.
- Categorización automática S/I/R con puntos de corte CLSI 2025.
- Panel de **muestras analizadas**: frecuencia por tipo de muestra, edad,
  servicio y especies.
- Panel de **aislados analizados**: conteos por especie, heatmaps de resistencia
  y evolución mensual por antibiótico.
- **Predicción trimestral** de resistencia con ARIMA, SARIMA y XGBoost.
- Reportes de procesamiento descargables en HTML y Excel.
- Almacenamiento local por sesión de navegador: cada usuario ve únicamente sus
  propios datos.
- Datos sintéticos de 5 años incluidos para probar la plataforma sin datos
  reales.

## Requisitos

- **Python 3.11**
- Las dependencias están fijadas en `requirements.txt`.

## Instalación

### Windows

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Si `Activate.ps1` está bloqueado por la política de ejecución, usa:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
python3.11 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Ejecución

```bash
python app.py
```

Abre la aplicación en:

```
http://localhost:8053
```

## Datos de ejemplo

La carpeta [`data/sinteticos/`](data/sinteticos/) contiene cinco archivos Excel
ficticios (`datos_2021.xlsx` … `datos_2025.xlsx`) listos para subir desde la
pestaña **“Cargar Datos”**.

1. Abre la pestaña **“Cargar Datos”**.
2. Escribe el año correspondiente.
3. Selecciona el archivo y pulsa **“Procesar datos”**.
4. Repite el proceso para los cinco años.

Con esos datos se generan 25 combinaciones especie–antibiótico válidas y 20
trimestres consecutivos, suficientes para ejecutar las predicciones.

Consulta [`data/sinteticos/README.md`](data/sinteticos/README.md) para el
formato, los códigos y las advertencias.

## Formato de los datos de entrada

Cada fila representa un aislado. El archivo debe contener, como mínimo:

| Columna | Ejemplo | Descripción |
|---|---|---|
| `fecha` | `15/01/2025` | Fecha de toma o recolección de la muestra |
| `SPEC_NUM` | `URO3000051` | Identificador de la muestra |
| `Tipo de localizacion` | `in` / `Internado` | Servicio hospitalario |
| `Tipo de muestra` | `or` / `Orina` | Tipo de muestra |
| `Edad` | `56` | Edad del paciente |
| `especie` | `eco` / `Escherichia coli` | Especie bacteriana |

Las columnas restantes deben ser **antibióticos** (por ejemplo, `Amicacina`,
`Ceftazidima`, `Ciprofloxacino`, `Meropenem`) con valores MIC en texto:

```
<=0,25
<=4
16
32
>=128
```

La aplicación reconoce tanto los códigos de los diccionarios como los nombres
finales en español. Los valores MIC se convierten a S/I/R con los puntos de
corte CLSI 2025.

## Estructura del proyecto

```
PredictionPlatformGitHub/
├── app.py                     # Punto de entrada de la app Dash
├── config.py                  # Rutas, colores y constantes
├── sesion.py                  # Sesión anónima y almacenamiento por navegador
├── callbacks/                 # Callbacks de los paneles
├── datos/                     # Carga, categorización y limpieza de datos
├── graficos/                  # Figuras y tablas del monitoreo
├── layout/                    # Componentes de la interfaz
├── prediccion/                # Preprocesamiento, modelos y generación
├── reportes/                  # Reportes HTML/Excel
├── scripts/
│   └── generar_datos_sinteticos.py
├── assets/                    # CSS y JavaScript
├── data/
│   ├── Lista_antimicrobianos.xlsx
│   ├── Lista_CLSI_completa.xlsx
│   ├── Lista_especie_especifico_general.xlsx
│   └── sinteticos/            # Excel ficticios listos para subir
├── requirements.txt
└── LICENSE
```

## Modelos de predicción

Para cada combinación especie–antibiótico con al menos **15 trimestres
consecutivos válidos** (aproximadamente 5 años), la plataforma entrena y
compara:

- **ARIMA**
- **SARIMA**
- **XGBoost**

El mejor modelo se selecciona según el error (RMSE por defecto) y se usa para
proyectar los siguientes trimestres. El entrenamiento puede tardar varios
minutos; se ejecuta en segundo plano y el estado se muestra en la pestaña de
predicción.

## Privacidad y almacenamiento

- Los datos se guardan **localmente** en `data/<session_id>/`.
- La sesión es anónima y se identifica mediante una cookie del navegador.
- No se envían datos de usuarios a servicios externos ni se incluye telemetría.
- `.gitignore` excluye los pickles de datos y reportes generados, además de las
  carpetas de sesión. Solo se versionan los diccionarios y los datos sintéticos.

## Diccionarios y puntos de corte

Los tres archivos Excel de `data/` son necesarios para el funcionamiento:

- `Lista_antimicrobianos.xlsx`: mapeo de variables, especies, antibióticos,
  muestras y localizaciones.
- `Lista_especie_especifico_general.xlsx`: clasificación de especies en grupos
  generales y principales.
- `Lista_CLSI_completa.xlsx`: puntos de corte **CLSI 2025**.

Están basados en datos públicos adaptados al formato de la plataforma. Consulta
[`data/README.md`](data/README.md) para más detalles.

## Limitaciones

- Las predicciones dependen de la calidad, cantidad y homogeneidad de los datos
  cargados.
- Los datos sintéticos incluidos son ficticios y no deben interpretarse como
  evidencia clínica ni epidemiológica.
- La aplicación no reemplaza el juicio de un profesional de la salud ni un
  sistema de vigilancia antimicrobiana validado.

## Licencia

Distribuido bajo la licencia **MIT**. Consulta [`LICENSE`](LICENSE).

Copyright (c) 2026 **Zahir Zamudio Zea**.
