# Segundo Avance - Proyecto Integrador: PIB y Mercado Laboral del Tolima (2007–2025)

Pipeline ETL modular en Python para extraer, limpiar, transformar, integrar y auditar las series oficiales del DANE sobre el Producto Interno Bruto (PIB) departamental a precios constantes de 2015 y los indicadores del mercado laboral (GEIH) del departamento del Tolima.

## Estructura del repositorio

```text
├── data/
│   ├── raw/                  # Fuentes originales del DANE (.xlsx)
│   └── processed/            # Dataset integrado final (.csv y .xlsx)
├── docs/                     # Informe técnico del segundo avance
├── outputs/                  # Reportes de validación y detección de atípicos (.csv)
├── src/                      # Módulos del pipeline ETL
│   ├── extraction.py         # Ingesta y verificación de esquemas
│   ├── cleaning.py           # Estandarización de tipos y normalización de escalas
│   ├── transformation.py     # Cálculo de los 6 indicadores analíticos derivados
│   ├── integration.py        # Unión LEFT JOIN 1:1 por llave temporal (año)
│   ├── validation.py         # Controles automáticos de calidad e integridad
│   └── audit.py              # Auditoría de faltantes, matriz de calidad e IQR
├── main.py                   # Orquestador principal del pipeline
├── requirements.txt          # Dependencias del proyecto
└── run.bat                   # Script de ejecución automática en Windows