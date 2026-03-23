@echo off
echo =========================================
echo  Gerador de Etiquetas Silviaprint
echo =========================================
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo Erro: Python não está instalado ou não está no PATH
    echo Baixe em: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Criar ambiente virtual se não existir
if not exist "venv" (
    echo Criando ambiente virtual...
    python -m venv venv
)

REM Ativar ambiente virtual
echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

REM Instalar dependências
echo.
echo Instalando dependências...
pip install -r requirements.txt -q

REM Executar aplicação
echo.
echo =========================================
echo Iniciando servidor...
echo Acesse: http://localhost:5000
echo Pressione Ctrl+C para parar
echo =========================================
echo.

python app.py
pause
