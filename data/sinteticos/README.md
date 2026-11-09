# Datos sintéticos (2021–2025)

> **Aviso:** estos archivos son **ficticios**. Se generaron únicamente para
> probar la plataforma (carga, visualizaciones y predicciones). No describen
> pacientes reales y **no deben usarse para decisiones clínicas,
> epidemiológicas ni de salud pública**.

## Contenido

| Archivo | Año | Filas aproximadas |
|---|---|---|
| `datos_2021.xlsx` | 2021 | 1.821 |
| `datos_2022.xlsx` | 2022 | 1.878 |
| `datos_2023.xlsx` | 2023 | 1.842 |
| `datos_2024.xlsx` | 2024 | 1.885 |
| `datos_2025.xlsx` | 2025 | 1.815 |

Total: **9.241 aislados** y **20 trimestres** (2021-T1 a 2025-T4). El mínimo
que exige la plataforma para predecir es de 15 trimestres consecutivos.

## Cómo cargarlos en la app

1. Ejecuta la aplicación (`python app.py`) y abre `http://localhost:8053`.
2. Ve a la pestaña **“Cargar Datos”**.
3. Escribe el año correspondiente (por ejemplo, `2021`).
4. Selecciona `datos_2021.xlsx` y pulsa **“Procesar datos”**.
5. Repite los pasos 3 y 4 para 2022, 2023, 2024 y 2025.

Cuando estén cargados los cinco años, entra a la pestaña de predicciones y
genera el análisis. Con estos datos se obtienen **25 combinaciones
especie–antibiótico** válidas (todas con 20 trimestres consecutivos).

## Formato de las columnas

Cada fila representa un aislado:

| Columna | Ejemplo | Descripción |
|---|---|---|
| `fecha` | `15/01/2025` | Fecha de toma de la muestra |
| `SPEC_NUM` | `URO3000051` | Identificador único de la muestra |
| `Tipo de localizacion` | `in` | Código de servicio (ver abajo) |
| `Tipo de muestra` | `or` | Código de muestra (ver abajo) |
| `Edad` | `56` | Edad del paciente (0–95) |
| `especie` | `eco` | Código de especie (ver abajo) |
| `Amicacina` … `Vancomicina` | `<=0,25`, `16`, `>=128` | MIC en texto |

### Códigos de localización

`in` = Internado, `out` = Ambulatorio, `eme` = Urgencias,
`icu` = Unidad de cuidado intensivo, `int` = Unidad de cuidado intermedio,
`inx` = Internado (no-UCI). La app los traduce automáticamente a su nombre.

### Códigos de muestra

`or` = Orina, `sa` = Sangre, `es` = Esputo, `br` = Bronquial,
`ha` = Herida, `ab` = Líquido abdominal, `tq` = Aspirado traqueal,
`pi` = Piel, `ca` = Catéter, `as` = Absceso, `te` = Tejido.

### Especies y antibióticos

| Código | Especie | Antibióticos con punto de corte CLSI 2025 |
|---|---|---|
| `eco` | *Escherichia coli* | Amicacina, Ceftazidima, Ceftriaxona, Ciprofloxacino, Meropenem |
| `kpn` | *Klebsiella pneumoniae* | Amicacina, Ceftazidima, Ceftriaxona, Ciprofloxacino, Meropenem |
| `pae` | *Pseudomonas aeruginosa* | Amicacina, Aztreonam, Ceftazidima, Ciprofloxacino, Meropenem |
| `aba` | *Acinetobacter baumannii* | Amicacina, Ceftazidima, Ceftriaxona, Ciprofloxacino, Meropenem |
| `sau` | *Staphylococcus aureus* | Clindamicina, Ciprofloxacino, Gentamicina, Oxacilina, Vancomicina |

Los valores MIC se generan solo en diluciones dobles (`0,0625` a `256`) y se
expresan como texto con prefijos `<=` o `>=` cuando corresponde. Cada valor
vuelve a clasificarse como **S**, **I** o **R** con los mismos puntos de corte
que usa la aplicación.

### Sobre la coherencia especie–antibiótico

No se incluyeron antibióticos sin punto de corte CLSI 2025 para estas
especies:

- **Caspofungina** es un antifúngico; las cinco especies son bacterias.
- **Cefalotina** no tiene puntos de corte CLSI 2025 para estas especies. En su
  lugar se usan cefalosporinas con punto de corte válido (Ceftazidima,
  Ceftriaxona).

Por eso cada fila tiene valores solo en los antibióticos de su especie; el
resto queda vacío, igual que ocurre con un panel de laboratorio real.

## Regenerar los archivos

```bash
python scripts/generar_datos_sinteticos.py --validar
```

Opciones: `--desde`, `--hasta`, `--seed`, `--salida`, `--validar`.
El script usa los tres diccionarios Excel de `data/` y valida que el pipeline
real produzca combinaciones aptas para predecir.
