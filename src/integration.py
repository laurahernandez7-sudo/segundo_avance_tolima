import pandas as pd

COLUMNAS_ORDENADAS_BASE = [
    "id_año",
    "departamento",
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
    "crec_pib_real",
    "var_ocupados",
    "var_desocupados",
]


def integrar_fuentes(pib: pd.DataFrame, mer_lab: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Integra Mercado Laboral (izquierda) y PIB Departamental (derecha) mediante
    LEFT JOIN uno a uno usando la llave anual.
    """
    anios_mer = set(mer_lab["id_año"].dropna().astype(int))
    anios_pib = set(pib["año_id"].dropna().astype(int))

    huerfanos_mer = sorted(anios_mer - anios_pib)
    huerfanos_pib = sorted(anios_pib - anios_mer)

    combinado = pd.merge(
        mer_lab,
        pib,
        left_on="id_año",
        right_on="año_id",
        how="left",
        validate="one_to_one",
        indicator=True,
    )

    sin_coincidencia = int((combinado["_merge"] != "both").sum())
    combinado = combinado.rename(columns={"mer_departamento": "departamento"})

    tabla_integrada = combinado[COLUMNAS_ORDENADAS_BASE].sort_values("id_año").reset_index(drop=True)

    metricas_union = {
        "filas_antes": len(mer_lab),
        "filas_despues": len(tabla_integrada),
        "sin_coincidencia": sin_coincidencia,
        "huerfanos_mercado": huerfanos_mer,
        "huerfanos_pib": huerfanos_pib,
    }

    return tabla_integrada, metricas_union