import pandas as pd

COLUMNAS_TASAS = ["pct_pet", "tgp", "to", "td", "ts"]


def ejecutar_validaciones(
    tabla_final: pd.DataFrame, pib_origen: pd.DataFrame, mer_origen: pd.DataFrame
) -> pd.DataFrame:
    """
    Ejecuta controles automáticos de calidad, consistencia contable,
    preservación de datos originales y validez de los 6 indicadores derivados.
    """
    filas_antes = len(mer_origen)
    filas_despues = len(tabla_final)
    duplicados_anio = int(tabla_final["id_año"].duplicated().sum())
    pib_nulos = int(tabla_final["pib_constante_2015"].isna().sum())

    # Preservación exacta de la masa económica del PIB y valores originales
    pib_suma_antes = float(pib_origen["pib_constante_2015"].sum())
    pib_suma_despues = float(tabla_final["pib_constante_2015"].sum())
    pib_intacto = (pib_origen["pib_constante_2015"].reset_index(drop=True) == tabla_final["pib_constante_2015"]).all()

    # Magnitudes positivas y escalas normalizadas (> 100 miles)
    no_positivos = int(
        ((tabla_final["pib_constante_2015"] <= 0) | (tabla_final["poblacion_total"] <= 0) | (tabla_final["pet"] <= 0)).sum()
    )
    escalas_ok = bool((tabla_final["poblacion_total"] > 100).all() and (tabla_final["pet"] > 100).all())

    # Tasas porcentuales en [0, 100]
    tasas_fuera = 0
    for col in COLUMNAS_TASAS:
        tasas_fuera += int(((tabla_final[col] < 0) | (tabla_final[col] > 100)).fillna(False).sum())

    # Consistencia del departamento
    deptos = tabla_final["departamento"].dropna().unique().tolist()
    depto_ok = len(deptos) == 1 and deptos[0] == "Tolima"

    # Identidad laboral: fuerza_trabajo = ocupados + desocupados (tolerancia ±1 mil por redondeo DANE)
    diff_ft = (tabla_final["fuerza_trabajo"] - (tabla_final["poblacion_ocupada"] + tabla_final["poblacion_desocupada"])).abs()
    exactos_ft = int((diff_ft == 0).sum())
    tolerancia_ft = int((diff_ft == 1).sum())
    fuera_tolerancia_ft = int((diff_ft > 1).sum())

    # Identidad PET: pet = fuerza_trabajo + fuera_fuerza_trabajo (tolerancia ±1 mil)
    diff_pet = (tabla_final["pet"] - (tabla_final["fuerza_trabajo"] + tabla_final["fuera_fuerza_trabajo"])).abs()
    fuera_tolerancia_pet = int((diff_pet > 1).sum())

    # Consistencia de los 6 indicadores derivados
    indicadores_ok = (
        int(tabla_final["crec_pib_real"].isna().sum()) == 1
        and int(tabla_final["var_ocupados"].isna().sum()) == 1
        and int(tabla_final["var_desocupados"].isna().sum()) == 1
        and (tabla_final["pib_por_ocupado"] > 0).all()
        and ((tabla_final["ocupados_por_mil_pet"] > 0) & (tabla_final["ocupados_por_mil_pet"] < 1000)).all()
        and (tabla_final["brecha_tgp_to"] >= 0).all()
    )

    # Aserciones críticas (detienen el flujo si la integridad falla)
    assert filas_antes == filas_despues == 19, "Error crítico: se perdió o duplicó algún registro anual."
    assert duplicados_anio == 0, "Error crítico: existen años duplicados en la tabla final."
    assert pib_suma_antes == pib_suma_despues and pib_intacto, "Error crítico: se alteró la serie original del PIB."
    assert escalas_ok, "Error crítico: las escalas de población no quedaron normalizadas."
    assert indicadores_ok, "Error crítico: inconsistencia en los 6 indicadores derivados."

    validaciones = pd.DataFrame(
        [
            {
                "Validacion": "Conservación de filas (cobertura 2007-2025)",
                "Resultado": "Cumple" if filas_antes == filas_despues else "No cumple",
                "Detalle": f"Antes: {filas_antes}; después: {filas_despues}",
            },
            {
                "Validacion": "Unicidad de la llave temporal (id_año)",
                "Resultado": "Cumple" if duplicados_anio == 0 else "No cumple",
                "Detalle": f"Años duplicados: {duplicados_anio}",
            },
            {
                "Validacion": "Integridad de cruce con PIB",
                "Resultado": "Cumple" if pib_nulos == 0 else "No cumple",
                "Detalle": f"Registros sin PIB asociado: {pib_nulos}",
            },
            {
                "Validacion": "Preservación de masa económica y valores PIB",
                "Resultado": "Cumple" if (pib_suma_antes == pib_suma_despues and pib_intacto) else "No cumple",
                "Detalle": f"Suma PIB antes: {pib_suma_antes:,.0f}; después: {pib_suma_despues:,.0f}",
            },
            {
                "Validacion": "Magnitudes positivas y escalas normalizadas",
                "Resultado": "Cumple" if (no_positivos == 0 and escalas_ok) else "No cumple",
                "Detalle": f"No positivos: {no_positivos}; escalas en miles verificadas: {escalas_ok}",
            },
            {
                "Validacion": "Rango lógico de tasas porcentuales [0, 100]",
                "Resultado": "Cumple" if tasas_fuera == 0 else "No cumple",
                "Detalle": f"Valores fuera de rango: {tasas_fuera}",
            },
            {
                "Validacion": "Consistencia entidad territorial",
                "Resultado": "Cumple" if depto_ok else "No cumple",
                "Detalle": f"Departamentos detectados: {deptos}",
            },
            {
                "Validacion": "Identidad Fuerza de Trabajo (±1 mil redondeo DANE)",
                "Resultado": "Cumple" if fuera_tolerancia_ft == 0 else "Revisar",
                "Detalle": f"Exactos: {exactos_ft}; dif ±1 mil: {tolerancia_ft}; fuera tolerancia: {fuera_tolerancia_ft}",
            },
            {
                "Validacion": "Identidad PET (±1 mil redondeo DANE)",
                "Resultado": "Cumple" if fuera_tolerancia_pet == 0 else "Revisar",
                "Detalle": f"Registros fuera de tolerancia ±1 mil: {fuera_tolerancia_pet}",
            },
            {
                "Validacion": "Consistencia de los 6 indicadores derivados",
                "Resultado": "Cumple" if indicadores_ok else "No cumple",
                "Detalle": "6/6 indicadores verificados (3 nulos esperados en 2007 por rezago t-1)",
            },
        ]
    )

    return validaciones