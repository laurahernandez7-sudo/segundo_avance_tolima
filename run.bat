@echo off
cd /d "%~dp0"
py main.py
if errorlevel 1 (
    echo.
    echo El programa encontro un problema. Revisa el mensaje anterior.
) else (
    echo.
    echo Ejecucion terminada. Revisa la carpeta salida.
)
pause
