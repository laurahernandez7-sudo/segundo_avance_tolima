# Segundo avance - PIB y mercado laboral del Tolima

Programa en Python para limpiar, transformar, integrar y validar las fuentes de PIB departamental y mercado laboral del Tolima.

## Archivos de entrada

Copia estos dos archivos Excel en esta misma carpeta, sin cambiar sus nombres:

- `pib_departamental.xlsx`
- `mercado_laboral_tolima.xlsx`

El programa lee la primera hoja de cada archivo.

## Instalación en Windows / VS Code

Abre esta carpeta en Visual Studio Code y abre la terminal integrada. Ejecuta:

```bash
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
py main.py
```

También puedes ejecutar `run.bat` después de instalar las librerías.

## Resultados

El programa crea la carpeta `salida` con:

- `tabla_final_tolima.csv`: tabla integrada.
- `validaciones.csv`: resumen de las comprobaciones.
- `resultados_segundo_avance.xlsx`: libro con datos integrados, fuentes, transformaciones, validaciones, matriz de calidad y faltantes.

## Decisiones de calidad

- Los años son la clave de integración: `id_año` en mercado laboral y `año_id` en PIB.
- Se conserva la información del mercado laboral mediante una integración `LEFT JOIN`.
- Se eliminan únicamente filas completamente idénticas.
- Si un año aparece más de una vez con datos distintos, el programa se detiene y guarda los registros conflictivos para revisión.
- Los valores faltantes se reportan, pero no se imputan automáticamente.
