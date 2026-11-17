import pandas as pd

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


def convertir_anio(serie: pd.Series, nombre_col: str) -> pd.Series:
    anio = pd.to_numeric(serie, errors="coerce")
    if anio.isna().any():
        filas = list(anio[anio.isna()].index)
        raise ValueError(f"La columna '{nombre_col}' tiene años vacíos o inválidos en filas: {filas}")
    if ((anio % 1) != 0).any():
        raise ValueError(f"La columna '{nombre_col}' contiene años con decimales.")
    return anio.astype("Int64")


def convertir_numero(serie: pd.Series) -> pd.Series:
    """Convierte cadenas con coma decimal a float64 preservando los NaN originales."""
    if pd.api.types.is_numeric_dtype(serie):
        return pd.to_numeric(serie, errors="coerce")
    texto = serie.astype("string").str.strip().str.replace(",", ".", regex=False)
    return pd.to_numeric(texto, errors="coerce")


def limpiar_y_estandarizar(
    pib_raw: pd.DataFrame, mer_lab_raw: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Aplica limpieza, estandarización de tipos, control de duplicados y
    normalización de escalas poblacionales sin imputar nulos oficiales.
    """
    pib = pib_raw.copy()
    mer_lab = mer_lab_raw.copy()

    # 1. Estandarización de textos
    pib["pib_departamento"] = (
        pib["pib_departamento"].astype("string").str.strip().str.replace(r"\s+", " ", regex=True).str.title()
    )
    mer_lab["mer_departamento"] = (
        mer_lab["mer_departamento"].astype("string").str.strip().str.replace(r"\s+", " ", regex=True).str.title()
    )

    # 2. Homologación de llaves temporales
    pib["año_id"] = convertir_anio(pib["año_id"], "año_id")
    mer_lab["id_año"] = convertir_anio(mer_lab["id_año"], "id_año")

    # 3. Conversión numérica
    pib["pib_constante_2015"] = convertir_numero(pib["pib_constante_2015"])
    if pib["pib_constante_2015"].isna().any():
        raise ValueError("La columna 'pib_constante_2015' tiene valores no numéricos.")

    for col in COLUMNAS_NUMERICAS_MERCADO:
        original = mer_lab[col].copy()
        convertida = convertir_numero(original)
        fallos = original.notna() & convertida.isna()
        if fallos.any():
            ejemplos = original[fallos].astype(str).unique().tolist()
            raise ValueError(f"Error al convertir '{col}' a numérico. Ejemplos: {ejemplos}")
        mer_lab[col] = convertida

    # 4. Normalización de escala de población (miles de personas)
    # En los anexos DANE, valores < 10 (ej. 1.308 o 1.005) representan miles con separador de punto.
    mask_pob = mer_lab["poblacion_total"] < 10
    n_norm_pob = int(mask_pob.sum())
    mer_lab.loc[mask_pob, "poblacion_total"] = mer_lab.loc[mask_pob, "poblacion_total"] * 1000

    mask_pet = mer_lab["pet"] < 10
    n_norm_pet = int(mask_pet.sum())
    mer_lab.loc[mask_pet, "pet"] = mer_lab.loc[mask_pet, "pet"] * 1000

    # 5. Eliminación de duplicados exactos y verificación de unicidad de clave
    dup_exactos_pib = int(pib.duplicated().sum())
    dup_exactos_mer = int(mer_lab.duplicated().sum())
    pib = pib.drop_duplicates().copy()
    mer_lab = mer_lab.drop_duplicates().copy()

    if pib["año_id"].duplicated().any() or mer_lab["id_año"].duplicated().any():
        raise ValueError("Existen años duplicados con valores distintos en las fuentes.")

    # 6. Ordenamiento cronológico (indispensable para variaciones interanuales)
    pib = pib.sort_values("año_id").reset_index(drop=True)
    mer_lab = mer_lab.sort_values("id_año").reset_index(drop=True)

    resumen_limpieza = {
        "normalizados_poblacion_total": n_norm_pob,
        "normalizados_pet": n_norm_pet,
        "duplicados_exactos_pib": dup_exactos_pib,
        "duplicados_exactos_mercado": dup_exactos_mer,
        "nulos_conservados_mercado": int(mer_lab.isna().sum().sum()),
    }

    return pib, mer_lab, resumen_limpieza