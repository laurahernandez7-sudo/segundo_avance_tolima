from pathlib import Path
import pandas as pd

from src.extraction import extraer_fuentes, generar_resumen_extraccion
from src.cleaning import limpiar_y_estandarizar
from src.transformation import (
    calcular_transformaciones_por_fuente,
    calcular_transformaciones_integradas,
)
from src.integration import integrar_fuentes
from src.validation import ejecutar_validaciones
from src.audit import auditar_faltantes, detectar_atipicos_iqr, construir_matriz_calidad

# ==============================================================================
# PIPELINE ETL - SEGUNDO AVANCE PROYECTO INTEGRADOR
# PIB Y MERCADO LABORAL DEL TOLIMA (2007 - 2025)
# ==============================================================================

RAIZ = Path(__file__).resolve().parent
RUTA_PIB = RAIZ / "data" / "raw" / "pib_departamental.xlsx"
RUTA_MERCADO = RAIZ / "data" / "raw" / "mercado_laboral_tolima.xlsx"

DIR_PROCESSED = RAIZ / "data" / "processed"
DIR_OUTPUTS = RAIZ / "outputs"


def main() -> None:
    print("\n" + "=" * 70)
    print("PIPELINE ETL: PIB Y MERCADO LABORAL DEL TOLIMA (2007 - 2025)")
    print("=" * 70)

    # 1. Extracción
    pib_raw, mer_raw = extraer_fuentes(RUTA_PIB, RUTA_MERCADO)
    resumen_fuentes = generar_resumen_extraccion(pib_raw, mer_raw, RUTA_PIB.name, RUTA_MERCADO.name)
    print("\n[1/6] Extracción completada:")
    print(resumen_fuentes.to_string(index=False))

    # 2. Limpieza y estandarización
    pib_limpio, mer_limpio, resumen_limpieza = limpiar_y_estandarizar(pib_raw, mer_raw)
    print("\n[2/6] Limpieza y estandarización completada:")
    print(f"  - Valores normalizados en poblacion_total: {resumen_limpieza['normalizados_poblacion_total']}")
    print(f"  - Valores normalizados en pet: {resumen_limpieza['normalizados_pet']}")
    print(f"  - Nulos originales conservados sin imputar: {resumen_limpieza['nulos_conservados_mercado']}")

    # 3. Transformaciones por fuente (variaciones interanuales)
    pib_trans, mer_trans = calcular_transformaciones_por_fuente(pib_limpio, mer_limpio)
    print("\n[3/6] Transformaciones por fuente calculadas (crec_pib_real, var_ocupados, var_desocupados).")

    # 4. Integración de fuentes (LEFT JOIN 1:1 por año)
    tabla_integrada, metricas_union = integrar_fuentes(pib_trans, mer_trans)
    print("\n[4/6] Integración 1:1 completada:")
    print(f"  - Filas antes: {metricas_union['filas_antes']} | Filas después: {metricas_union['filas_despues']}")
    print(f"  - Registros sin coincidencia: {metricas_union['sin_coincidencia']}")

    # 5. Transformaciones integradas (indicadores cruzados)
    tabla_final = calcular_transformaciones_integradas(tabla_integrada)
    print(f"\n[5/6] Transformaciones integradas completadas. Dimensión final: {tabla_final.shape[0]} filas x {tabla_final.shape[1]} columnas.")

    # 6. Validaciones y auditoría
    validaciones = ejecutar_validaciones(tabla_final, pib_limpio, mer_limpio)
    resumen_faltantes, analisis_nulos = auditar_faltantes(tabla_final)
    atipicos_iqr = detectar_atipicos_iqr(tabla_final)
    matriz_calidad = construir_matriz_calidad(tabla_final, resumen_limpieza, validaciones)

    print("\n[6/6] Validaciones automáticas:")
    print(validaciones.to_string(index=False))

    # 7. Exportación de productos finales
    DIR_PROCESSED.mkdir(parents=True, exist_ok=True)
    DIR_OUTPUTS.mkdir(parents=True, exist_ok=True)

    ruta_csv = DIR_PROCESSED / "tabla_final_tolima.csv"
    ruta_excel = DIR_PROCESSED / "segundo_avance_tolima.xlsx"
    ruta_val_csv = DIR_OUTPUTS / "validaciones.csv"
    ruta_iqr_csv = DIR_OUTPUTS / "atipicos_iqr.csv"

    tabla_final.to_csv(ruta_csv, index=False, encoding="utf-8-sig")
    validaciones.to_csv(ruta_val_csv, index=False, encoding="utf-8-sig")
    atipicos_iqr.to_csv(ruta_iqr_csv, index=False, encoding="utf-8-sig")

    with pd.ExcelWriter(ruta_excel, engine="openpyxl") as writer:
        tabla_final.to_excel(writer, sheet_name="Datos_integrados", index=False)
        resumen_fuentes.to_excel(writer, sheet_name="Fuentes", index=False)
        validaciones.to_excel(writer, sheet_name="Validaciones", index=False)
        matriz_calidad.to_excel(writer, sheet_name="Matriz_calidad", index=False)
        resumen_faltantes.to_excel(writer, sheet_name="Valores_faltantes", index=False)
        analisis_nulos.to_excel(writer, sheet_name="Analisis_nulos", index=False)
        atipicos_iqr.to_excel(writer, sheet_name="Atipicos_IQR", index=False)

    print("\n" + "=" * 70)
    print("PROCESO FINALIZADO EXITOSAMENTE")
    print("=" * 70)
    print(f"CSV consolidado : {ruta_csv.relative_to(RAIZ)}")
    print(f"Excel multihoja : {ruta_excel.relative_to(RAIZ)}")
    print(f"Auditoría CSV   : {ruta_val_csv.relative_to(RAIZ)} y {ruta_iqr_csv.relative_to(RAIZ)}\n")


if __name__ == "__main__":
    main()