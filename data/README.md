# Diccionarios de datos

Esta carpeta contiene los diccionarios de referencia que usa la plataforma para
normalizar los archivos Excel cargados por el usuario. **No contienen datos de
pacientes.**

> Los datos de sesión (`datos_*.pkl`, `reporte_*.pkl`) se generan localmente y
> están excluidos del repositorio mediante `.gitignore`.

## Archivos

### `Lista_antimicrobianos.xlsx`

Catálogo de mapeo entre los nombres originales de las columnas y los nombres
internos de la aplicación, además de los códigos de especies, antibióticos,
tipos de muestra y localizaciones.

| Columna | Contenido |
|---|---|
| `variable_original` / `variable_nueva` | Renombrado de columnas de entrada |
| `especie_1`, `especie_2`, `especie_3` | Variantes de código de especie |
| `especie` | Nombre final de la especie |
| `antibiotico_1` … `antibiotico_4` | Variantes de código/nombre de antibiótico |
| `antibiotico` | Nombre final del antibiótico |
| `codigo_localizacion` / `nombre_localizacion` | Servicio hospitalario |
| `codigo_muestra` / `nombre_muestra` | Tipo de muestra |

La plataforma detecta automáticamente qué variante está presente en el archivo
de entrada. También acepta columnas de antibióticos con el nombre final en
español (por ejemplo, `Amicacina`).

### `Lista_especie_especifico_general.xlsx`

Clasificación de cada especie en dos niveles:

| Columna | Contenido |
|---|---|
| `Especie_especifica` | Nombre de la especie |
| `Grupo_general` | Grupo general (p. ej. `Enterobacterales`) |
| `Grupo_principal` | Grupo principal (p. ej. `Gram negativa`) |

Estos grupos se usan para buscar los puntos de corte correctos y para agrupar
las visualizaciones.

### `Lista_CLSI_completa.xlsx`

Puntos de corte **CLSI 2025** por antibiótico, grupo y especie. La hoja se llama
`completa` e incluye:

| Columna | Contenido |
|---|---|
| `Antibiotico` | Nombre del antibiótico en español |
| `Grupo_general` | Grupo general del microorganismo |
| `Grupo/Especie especifica` | Especie o grupo específico; puede incluir reglas del tipo `Diferente: ...` |
| `CLSI <=S`, `CLSI =I/SDD`, `CLSI >=R` | Puntos de corte por MIC (método clásico) |
| `CLSI >=S`, `CLSI =I`, `CLSI <=R` | Puntos de corte por difusión en disco (método alterno) |
| `Comments` | Notas de la fuente CLSI |

La aplicación elige el método clásico o alterno según el patrón del valor MIC
recibido.

## Origen y alcance

- Los tres archivos provienen de **datos públicos** de referencia, adaptados al
  formato interno de la plataforma.
- La versión de los puntos de corte es **CLSI 2025**.
- No incluyen información de pacientes.
- Si se modifican nombres, códigos o columnas, debe verificarse que el pipeline
  de categorización siga funcionando.

## Datos sintéticos

La carpeta [`sinteticos/`](sinteticos/) contiene cinco Excel ficticios
(2021–2025) listos para subir desde la pestaña **“Cargar Datos”**. Son datos de
prueba, sin validez clínica ni epidemiológica.

Consulta [`sinteticos/README.md`](sinteticos/README.md) para el formato, los
códigos y las instrucciones de carga.
