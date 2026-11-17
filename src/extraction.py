from pathlib import Path
import pandas as pd

COLUMNAS_PIB = ["año_id", "pib_departamento", "pib_constante_2015"]

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


def validar_existencia_archivo(ruta: Path) -> None:
    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo requerido: {ruta}. "
            "Verifica que los Excel originales estén en data/raw/."
        )


def validar_columnas_requeridas(df: pd.DataFrame, requeridas: list[str], nombre_archivo: str) -> None:
    faltantes = [col for col in requeridas if col not in df.columns]
    if faltantes:
        raise ValueError(
            f"Al archivo '{nombre_archivo}' le faltan las columnas: {faltantes}. "
            f"Columnas detectadas: {list(df.columns)}"
        )


def extraer_fuentes(ruta_pib: Path, ruta_mercado: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Lee los archivos Excel originales desde data/raw/ y valida su esquema base."""
    validar_existencia_archivo(ruta_pib)
    validar_existencia_archivo(ruta_mercado)

    pib = pd.read_excel(ruta_pib)
    mer_lab = pd.read_excel(ruta_mercado)

    pib.columns = pib.columns.astype(str).str.strip()
    mer_lab.columns = mer_lab.columns.astype(str).str.strip()

    validar_columnas_requeridas(pib, COLUMNAS_PIB, ruta_pib.name)
    validar_columnas_requeridas(mer_lab, COLUMNAS_MERCADO, ruta_mercado.name)

    return pib, mer_lab


def generar_resumen_extraccion(
    pib: pd.DataFrame,
    mer_lab: pd.DataFrame,
    nombre_pib: str,
    nombre_mercado: str,
) -> pd.DataFrame:
    """Genera tabla comparativa inicial de las dos fuentes extraídas."""
    return pd.DataFrame(
        [
            {
                "Fuente": "Mercado Laboral (GEIH)",
                "Archivo": nombre_mercado,
                "Filas": mer_lab.shape[0],
                "Columnas": mer_lab.shape[1],
                "Valores_faltantes": int(mer_lab.isna().sum().sum()),
                "Filas_duplicadas": int(mer_lab.duplicated().sum()),
            },
            {
                "Fuente": "PIB Departamental",
                "Archivo": nombre_pib,
                "Filas": pib.shape[0],
                "Columnas": pib.shape[1],
                "Valores_faltantes": int(pib.isna().sum().sum()),
                "Filas_duplicadas": int(pib.duplicated().sum()),
            },
        ]
    )