from pathlib import Path
import pandas as pd

# ============================================================
# SEGUNDO AVANCE - PROYECTO INTEGRADOR
# PIB Y MERCADO LABORAL DEL TOLIMA (2007-2025)
# Los dos archivos Excel deben estar en la misma carpeta que este script.
# ============================================================

CARPETA = Path(__file__).resolve().parent
ARCHIVO_PIB = CARPETA / "pib_departamental.xlsx"
ARCHIVO_MERCADO = CARPETA / "mercado_laboral_tolima.xlsx"
CARPETA_RESULTADOS = CARPETA / "resultados"

COLUMNAS_MERCADO = [
    "id_año",
    "mer_departamento",
    "pct_pet",
    "tgp",
    "to",
    "td",
    "ts",
    "poblacion_total",
    "pet",
    "fuerza_trabajo",
    "poblacion_ocupada",
    "poblacion_desocupada",
    "fuera_fuerza_trabajo",
    "poblacion_subocupada",
    "fuerza_trabajo_potencial",
]

COLUMNAS_PIB = [
    "año_id",
    "pib_departamento",
    "pib_constante_2015",
]

COLUMNAS_NUMERICAS_MERCADO = [
    "pct_pet",
    "tgp",
    "to",
    "td",
    "ts",
    "poblacion_total",
    "pet",
    "fuerza_trabajo",
    "poblacion_ocupada",
    "poblacion_desocupada",
    "fuera_fuerza_trabajo",
    "poblacion_subocupada",
    "fuerza_trabajo_potencial",
]

COLUMNAS_TASAS = ["pct_pet", "tgp", "to", "td", "ts"]


# ------------------------------------------------------------
# Funciones de apoyo
# ------------------------------------------------------------

def revisar_archivo(ruta):
    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {ruta.name}. "
            "Coloca los dos Excel en la misma carpeta que main.py."
        )


def revisar_columnas(df, columnas, nombre):
    faltantes = [col for col in columnas if col not in df.columns]
    if faltantes:
        raise ValueError(
            f"Al archivo {nombre} le faltan estas columnas: {faltantes}. "
            f"Columnas encontradas: {list(df.columns)}"
        )


def convertir_anio(serie, nombre):
    anio = pd.to_numeric(serie, errors="coerce")
    if anio.isna().any():
        filas = list(anio[anio.isna()].index)
        raise ValueError(
            f"La columna {nombre} contiene años vacíos o no numéricos "
            f"en las filas: {filas}"
        )
    if ((anio % 1) != 0).any():
        raise ValueError(f"La columna {nombre} contiene años con decimales.")
    return anio.astype("Int64")


def convertir_numero(serie):
    """Convierte números y decimales escritos con coma, sin rellenar nulos."""
    if pd.api.types.is_numeric_dtype(serie):
        return pd.to_numeric(serie, errors="coerce")

    texto = serie.astype("string").str.strip()
    texto = texto.str.replace(",", ".", regex=False)
    return pd.to_numeric(texto, errors="coerce")


def filas_duplicadas_por_clave(df, clave):
    return int(df[clave].duplicated(keep=False).sum())


# ------------------------------------------------------------
# 1. Cargar las dos bases de datos
# ------------------------------------------------------------
print("\n" + "=" * 65)
print("SEGUNDO AVANCE: PIB Y MERCADO LABORAL DEL TOLIMA")
print("=" * 65)

revisar_archivo(ARCHIVO_PIB)
revisar_archivo(ARCHIVO_MERCADO)

pib = pd.read_excel(ARCHIVO_PIB)
mer_lab = pd.read_excel(ARCHIVO_MERCADO)

# Limpieza básica de encabezados.
pib.columns = pib.columns.astype(str).str.strip()
mer_lab.columns = mer_lab.columns.astype(str).str.strip()

revisar_columnas(pib, COLUMNAS_PIB, ARCHIVO_PIB.name)
revisar_columnas(mer_lab, COLUMNAS_MERCADO, ARCHIVO_MERCADO.name)


print("\nArchivos cargados correctamente.")
print(f"Mercado laboral: {mer_lab.shape[0]} filas y {mer_lab.shape[1]} columnas")
print(f"PIB: {pib.shape[0]} filas y {pib.shape[1]} columnas")


# ------------------------------------------------------------
# 2. Diagnóstico inicial de las fuentes
# ------------------------------------------------------------

def explorar(nombre, df):
    print("\n" + "-" * 60)
    print(nombre)
    print("-" * 60)
    print("Dimensiones:", df.shape)
    print("Columnas:", list(df.columns))
    print("\nTipos de datos:")
    print(df.dtypes)
    print("\nValores faltantes por columna:")
    print(df.isnull().sum())
    print("\nFilas completamente duplicadas:", df.duplicated().sum())


explorar("FUENTE 1: MERCADO LABORAL", mer_lab)
explorar("FUENTE 2: PIB DEPARTAMENTAL", pib)

comparacion_fuentes = pd.DataFrame(
    [
        {
            "Archivo": ARCHIVO_MERCADO.name,
            "Filas": mer_lab.shape[0],
            "Columnas": mer_lab.shape[1],
            "Valores_faltantes": int(mer_lab.isnull().sum().sum()),
        },
        {
            "Archivo": ARCHIVO_PIB.name,
            "Filas": pib.shape[0],
            "Columnas": pib.shape[1],
            "Valores_faltantes": int(pib.isnull().sum().sum()),
        },
    ]
)

print("\nComparación de las fuentes:")
print(comparacion_fuentes.to_string(index=False))


# ------------------------------------------------------------
# TRANSFORMACIÓN 1. Estandarizar textos y nombres de columnas
# Justificación: evitar diferencias por espacios o mayúsculas.
# ------------------------------------------------------------
for df in (pib, mer_lab):
    df.columns = df.columns.astype(str).str.strip()

for columna in ["mer_departamento"]:
    mer_lab[columna] = (
        mer_lab[columna]
        .astype("string")
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .str.title()
    )

pib["pib_departamento"] = (
    pib["pib_departamento"]
    .astype("string")
    .str.strip()
    .str.replace(r"\s+", " ", regex=True)
    .str.title()
)

print("\nTRANSFORMACIÓN 1: textos y nombres estandarizados.")


# ------------------------------------------------------------
# TRANSFORMACIÓN 2. Homologar las claves temporales
# Justificación: ambas fuentes deben tener el año como entero.
# ------------------------------------------------------------
mer_lab["id_año"] = convertir_anio(mer_lab["id_año"], "id_año")
pib["año_id"] = convertir_anio(pib["año_id"], "año_id")

print("TRANSFORMACIÓN 2: claves de año convertidas a números enteros.")


# ------------------------------------------------------------
# TRANSFORMACIÓN 3. Convertir variables numéricas
# Justificación: poder comparar, calcular y validar las variables.
# La coma decimal se convierte en punto decimal.
# ------------------------------------------------------------
for columna in COLUMNAS_NUMERICAS_MERCADO:
    original = mer_lab[columna].copy()
    convertida = convertir_numero(original)

    valores_no_convertidos = original.notna() & convertida.isna()
    if valores_no_convertidos.any():
        ejemplos = original[valores_no_convertidos].astype(str).unique().tolist()
        raise ValueError(
            f"No se pudieron convertir algunos valores de {columna}: {ejemplos}"
        )

    mer_lab[columna] = convertida

pib["pib_constante_2015"] = convertir_numero(pib["pib_constante_2015"])

if pib["pib_constante_2015"].isna().any():
    raise ValueError("La columna pib_constante_2015 contiene valores no numéricos.")

print("TRANSFORMACIÓN 3: variables numéricas y tasas convertidas correctamente.")


# ------------------------------------------------------------
# TRANSFORMACIÓN 4. Revisar y tratar registros duplicados
# Justificación: quitar filas totalmente repetidas, pero no borrar
# años con información diferente de manera automática.
# ------------------------------------------------------------
duplicados_exactos_mercado = int(mer_lab.duplicated().sum())
duplicados_exactos_pib = int(pib.duplicated().sum())

mer_lab = mer_lab.drop_duplicates().copy()
pib = pib.drop_duplicates().copy()

duplicados_clave_mercado = filas_duplicadas_por_clave(mer_lab, "id_año")
duplicados_clave_pib = filas_duplicadas_por_clave(pib, "año_id")

print("TRANSFORMACIÓN 4: revisión de duplicados completada.")
print("Filas exactas repetidas eliminadas en mercado laboral:", duplicados_exactos_mercado)
print("Filas exactas repetidas eliminadas en PIB:", duplicados_exactos_pib)
print("Registros involucrados en años repetidos del mercado laboral:", duplicados_clave_mercado)
print("Registros involucrados en años repetidos del PIB:", duplicados_clave_pib)

if duplicados_clave_mercado > 0 or duplicados_clave_pib > 0:
    raise ValueError(
        "Hay años repetidos con información que puede ser diferente. "
        "No se eliminaron automáticamente para evitar perder datos. "
        "Revisa los registros duplicados en los archivos Excel."
    )


# ------------------------------------------------------------
# TRANSFORMACIÓN 5. Tratamiento de valores faltantes
# Justificación: se conservan como NaN porque no se debe inventar
# información ni reemplazar datos oficiales sin soporte metodológico.
# ------------------------------------------------------------faltantes_antes = mer_lab.isna().sum().add(pib.isna().sum(), fill_value=0)

# No se imputan ni eliminan los valores nulos.
# Se conservan para que el diagnóstico muestre la ausencia real de datos.

print("TRANSFORMACIÓN 5: valores faltantes identificados y conservados sin imputación.")


# ------------------------------------------------------------
# 3. Diagnóstico de claves antes de integrar
# ------------------------------------------------------------
print("\nAños en mercado laboral:")
print(sorted(mer_lab["id_año"].dropna().astype(int).unique().tolist()))

print("\nAños en PIB:")
print(sorted(pib["año_id"].dropna().astype(int).unique().tolist()))

anios_sin_pib = sorted(
    set(mer_lab["id_año"].dropna().astype(int))
    - set(pib["año_id"].dropna().astype(int))
)

anios_sin_mercado = sorted(
    set(pib["año_id"].dropna().astype(int))
    - set(mer_lab["id_año"].dropna().astype(int))
)

print("\nAños del mercado laboral que no aparecen en PIB:", anios_sin_pib)
print("Años del PIB que no aparecen en mercado laboral:", anios_sin_mercado)


# ------------------------------------------------------------
# 4. Integración de las dos fuentes
# Clave común: mercado laboral.id_año = PIB.año_id
# Se usa LEFT JOIN para conservar los registros del mercado laboral.
# ------------------------------------------------------------
df_integrado = pd.merge(
    mer_lab,
    pib,
    left_on="id_año",
    right_on="año_id",
    how="left",
    validate="one_to_one",
    indicator=True,
)

sin_coincidencia = int((df_integrado["_merge"] != "both").sum())

columnas_finales = [
    "id_año",
    "mer_departamento",
    "pct_pet",
    "tgp",
    "to",
    "td",
    "ts",
    "poblacion_total",
    "pet",
    "fuerza_trabajo",
    "poblacion_ocupada",
    "poblacion_desocupada",
    "fuera_fuerza_trabajo",
    "poblacion_subocupada",
    "fuerza_trabajo_potencial",
    "pib_constante_2015",
]

tabla_final = df_integrado[columnas_finales].copy()
tabla_final = tabla_final.rename(columns={"mer_departamento": "departamento"})
tabla_final = tabla_final.sort_values("id_año").reset_index(drop=True)

print("\nIntegración completada.")
print("Filas antes de integrar:", len(mer_lab))
print("Filas después de integrar:", len(tabla_final))
print("Registros sin coincidencia de PIB:", sin_coincidencia)
print("Dimensiones de la tabla final:", tabla_final.shape)


# ------------------------------------------------------------
# 5. Validaciones del resultado
# ------------------------------------------------------------
filas_antes = len(mer_lab)
filas_despues = len(tabla_final)
duplicados_finales = int(tabla_final["id_año"].duplicated().sum())

pib_sin_relacion = int(tabla_final["pib_constante_2015"].isna().sum())

valores_no_positivos = tabla_final[
    (tabla_final["pib_constante_2015"] <= 0)
    | (tabla_final["poblacion_total"] <= 0)
]

condiciones_tasas = []
for columna in COLUMNAS_TASAS:
    condiciones_tasas.append(
        ((tabla_final[columna] < 0) | (tabla_final[columna] > 100)).fillna(False)
    )

if condiciones_tasas:
    tasas_invalidas = pd.concat(condiciones_tasas, axis=1).any(axis=1)
    cantidad_tasas_invalidas = int(tasas_invalidas.sum())
else:
    cantidad_tasas_invalidas = 0

inconsistencia_laboral = (
    tabla_final["fuerza_trabajo"]
    != tabla_final["poblacion_ocupada"] + tabla_final["poblacion_desocupada"]
)

inconsistencia_laboral = inconsistencia_laboral.fillna(False)
cantidad_inconsistencias_laborales = int(inconsistencia_laboral.sum())

unicos_departamento = tabla_final["departamento"].dropna().unique().tolist()
departamentos_consistentes = (
    len(unicos_departamento) == 1
    and unicos_departamento[0].casefold() == "tolima"
    and tabla_final["departamento"].notna().all()
)

pib_total_antes = pd.to_numeric(pib["pib_constante_2015"], errors="coerce").sum()
pib_total_despues = tabla_final["pib_constante_2015"].sum()

validaciones = pd.DataFrame(
    [
        {
            "Validacion": "Conservación de filas",
            "Resultado": "Cumple" if filas_antes == filas_despues else "Revisar",
            "Detalle": f"Antes: {filas_antes}; después: {filas_despues}",
        },
        {
            "Validacion": "Unicidad del año",
            "Resultado": "Cumple" if duplicados_finales == 0 else "No cumple",
            "Detalle": f"Años duplicados en tabla final: {duplicados_finales}",
        },
        {
            "Validacion": "Relación con el PIB",
            "Resultado": "Cumple" if pib_sin_relacion == 0 else "Revisar",
            "Detalle": f"Registros sin PIB relacionado: {pib_sin_relacion}",
        },
        {
            "Validacion": "Valores positivos",
            "Resultado": "Cumple" if len(valores_no_positivos) == 0 else "Revisar",
            "Detalle": f"Registros con PIB o población menor o igual a cero: {len(valores_no_positivos)}",
        },
        {
            "Validacion": "Rango de tasas",
            "Resultado": "Cumple" if cantidad_tasas_invalidas == 0 else "Revisar",
            "Detalle": f"Registros con tasas fuera del rango 0 a 100: {cantidad_tasas_invalidas}",
        },
        {
            "Validacion": "Consistencia del departamento",
            "Resultado": "Cumple" if departamentos_consistentes else "Revisar",
            "Detalle": f"Departamentos encontrados: {unicos_departamento}",
        },
        {
            "Validacion": "Consistencia de fuerza de trabajo",
            "Resultado": "Cumple" if cantidad_inconsistencias_laborales == 0 else "Revisar",
            "Detalle": f"Registros donde fuerza_trabajo no coincide con ocupados + desocupados: {cantidad_inconsistencias_laborales}",
        },
        {
            "Validacion": "Conservación del total del PIB",
            "Resultado": "Cumple" if pib_total_antes == pib_total_despues else "Revisar",
            "Detalle": f"Antes: {pib_total_antes}; después: {pib_total_despues}",
        },
    ]
)

print("\nVALIDACIONES DEL RESULTADO")
print(validaciones.to_string(index=False))


# ------------------------------------------------------------
# 6. Diagnóstico de calidad y completitud
# ------------------------------------------------------------
resumen_faltantes = pd.DataFrame(
    {
        "Columna": tabla_final.columns,
        "Valores_faltantes": [int(tabla_final[c].isna().sum()) for c in tabla_final.columns],
        "Porcentaje_faltantes": [round(float(tabla_final[c].isna().mean() * 100), 2) for c in tabla_final.columns],
    }
)

matriz_calidad = pd.DataFrame(
    [
        {
            "Campo": "id_año",
            "Regla": "El año debe ser único",
            "Hallazgo": f"{duplicados_finales} años duplicados",
            "Dimension": "Unicidad",
            "Estado": "Cumple" if duplicados_finales == 0 else "No cumple",
            "Accion": "Mantener el año como clave para integrar las fuentes.",
        },
        {
            "Campo": "ts / poblacion_subocupada / fuerza_trabajo_potencial",
            "Regla": "Identificar y revisar los valores faltantes",
            "Hallazgo": "; ".join(
                f"{c}: {int(tabla_final[c].isna().sum())} faltantes"
                for c in ["ts", "poblacion_subocupada", "fuerza_trabajo_potencial"]
            ),
            "Dimension": "Completitud",
            "Estado": "Revisar" if tabla_final[["ts", "poblacion_subocupada", "fuerza_trabajo_potencial"]].isna().any().any() else "Cumple",
            "Accion": "Conservar los nulos sin imputar para no inventar información.",
        },
        {
            "Campo": "pib_constante_2015 / poblacion_total",
            "Regla": "Los valores deben ser mayores que cero",
            "Hallazgo": f"{len(valores_no_positivos)} registros con valores no positivos",
            "Dimension": "Validez",
            "Estado": "Cumple" if len(valores_no_positivos) == 0 else "No cumple",
            "Accion": "Revisar cualquier valor igual o inferior a cero.",
        },
        {
            "Campo": "pct_pet, tgp, to, td, ts",
            "Regla": "Las tasas deben estar entre 0 y 100",
            "Hallazgo": f"{cantidad_tasas_invalidas} registros con tasas fuera del rango",
            "Dimension": "Validez",
            "Estado": "Cumple" if cantidad_tasas_invalidas == 0 else "No cumple",
            "Accion": "Comprobar los valores porcentuales fuera del rango permitido.",
        },
        {
            "Campo": "departamento",
            "Regla": "El departamento debe estar estandarizado como Tolima",
            "Hallazgo": f"Valores encontrados: {unicos_departamento}",
            "Dimension": "Consistencia",
            "Estado": "Cumple" if departamentos_consistentes else "Revisar",
            "Accion": "Estandarizar la escritura del nombre del departamento.",
        },
        {
            "Campo": "fuerza_trabajo",
            "Regla": "Debe coincidir con ocupados + desocupados",
            "Hallazgo": f"{cantidad_inconsistencias_laborales} registros con diferencias",
            "Dimension": "Consistencia",
            "Estado": "Cumple" if cantidad_inconsistencias_laborales == 0 else "Revisar",
            "Accion": "Revisar las sumas de población laboral que no coincidan.",
        },
    ]
)

print("\nPORCENTAJE DE VALORES FALTANTES")
print(resumen_faltantes.to_string(index=False))

print("\nMATRIZ DE CALIDAD")
print(matriz_calidad.to_string(index=False))


# ------------------------------------------------------------
# 7. Análisis de variables con datos faltantes
# ------------------------------------------------------------
variables_con_faltantes = [
    "ts",
    "poblacion_subocupada",
    "fuerza_trabajo_potencial",
]

analisis_faltantes = []
for columna in variables_con_faltantes:
    serie = tabla_final[columna]
    analisis_faltantes.append(
        {
            "Variable": columna,
            "Media": serie.mean(),
            "Mediana": serie.median(),
            "Faltantes": int(serie.isna().sum()),
            "Porcentaje_faltantes": round(float(serie.isna().mean() * 100), 2),
            "Tratamiento": "Conservar sin imputar",
        }
    )

analisis_faltantes = pd.DataFrame(analisis_faltantes)

print("\nANÁLISIS DE VARIABLES CON VALORES FALTANTES")
print(analisis_faltantes.to_string(index=False))


# ------------------------------------------------------------
# 8. Exportar los resultados
# ------------------------------------------------------------
CARPETA_RESULTADOS.mkdir(exist_ok=True)

ruta_excel = CARPETA_RESULTADOS / "segundo_avance_tolima.xlsx"
ruta_csv = CARPETA_RESULTADOS / "tabla_final_tolima.csv"

with pd.ExcelWriter(ruta_excel, engine="openpyxl") as escritor:
    tabla_final.to_excel(escritor, sheet_name="Datos_integrados", index=False)
    comparacion_fuentes.to_excel(escritor, sheet_name="Fuentes", index=False)
    resumen_faltantes.to_excel(escritor, sheet_name="Valores_faltantes", index=False)
    validaciones.to_excel(escritor, sheet_name="Validaciones", index=False)
    matriz_calidad.to_excel(escritor, sheet_name="Matriz_calidad", index=False)
    analisis_faltantes.to_excel(escritor, sheet_name="Analisis_nulos", index=False)

tabla_final.to_csv(ruta_csv, index=False, encoding="utf-8-sig")

print("\n" + "=" * 65)
print("PROCESO TERMINADO")
print("=" * 65)
print("Tabla integrada:", ruta_excel)
print("Archivo CSV:", ruta_csv)
print("Filas finales:", len(tabla_final))
print("Columnas finales:", len(tabla_final.columns))
print("Los valores faltantes se conservaron sin reemplazarlos.")
