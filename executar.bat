@echo off
chcp 65001 >nul
echo ============================================================
echo   MAPEADOR DE COMÉRCIOS - DUQUE DE CAXIAS
echo   Setup e Execução
echo ============================================================
echo.

:: Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python não encontrado. Instale em https://python.org
    pause
    exit /b 1
)

:: Instala dependências
echo [1/2] Instalando dependências...
pip install -r requirements.txt -q
echo [2/2] Instalando navegador Playwright...
python -m playwright install chromium

echo.
echo Tudo pronto! Iniciando busca...
echo.

:: Executa o script
python mapear_comercios.py

echo.
echo ============================================================
echo   Concluído! Verifique a pasta /output para os resultados.
echo ============================================================
pause
