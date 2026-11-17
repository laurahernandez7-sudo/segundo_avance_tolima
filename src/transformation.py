import pandas as pd


def calcular_transformaciones_por_fuente(
    pib: pd.DataFrame, mer_lab: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calcula las 3 variaciones porcentuales interanuales sobre cada fuente ordenada:
      1. crec_pib_real
      2. var_ocupados
      3. var_desocupados
    """
    pib_t = pib.sort_values("año_id").copy()
    mer_t = mer_lab.sort_values("id_año").copy()

    pib_t["crec_pib_real"] = ((pib_t["pib_constante_2015"] / pib_t["pib_constante_2015"].shift(1)) - 1) * 100
    mer_t["var_ocupados"] = ((mer_t["poblacion_ocupada"] / mer_t["poblacion_ocupada"].shift(1)) - 1) * 100
    mer_t["var_desocupados"] = (
        (mer_t["poblacion_desocupada"] / mer_t["poblacion_desocupada"].shift(1)) - 1
    ) * 100

    return pib_t, mer_t


def calcular_transformaciones_integradas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula los 3 indicadores derivados que cruzan producción y mercado laboral:
      4. pib_por_ocupado (Millones de pesos de 2015 por ocupado)
      5. ocupados_por_mil_pet (Ocupados por cada 1.000 personas en edad de trabajar)
      6. brecha_tgp_to (Diferencia en puntos porcentuales entre TGP y TO)
    """
    df_out = df.copy()

    df_out["pib_por_ocupado"] = df_out["pib_constante_2015"] / df_out["poblacion_ocupada"]
    df_out["ocupados_por_mil_pet"] = (df_out["poblacion_ocupada"] / df_out["pet"]) * 1000
    df_out["brecha_tgp_to"] = df_out["tgp"] - df_out["to"]

    return df_out