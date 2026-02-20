@echo off
REM ═══════════════════════════════════════════════════════════════════════════
REM OPTIPICK - Lanceur d'application Streamlit
REM ═══════════════════════════════════════════════════════════════════════════

REM Aller au répertoire du projet
cd /d "%~dp0"

REM Lancer Streamlit
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║                    🚀 OPTIPICK - Streamlit App                           ║
echo ║                                                                           ║
echo ║ L'application se lance à http://localhost:8501                           ║
echo ║ Appuyez sur Ctrl+C pour arrêter                                          ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
echo.

streamlit run app_streamlit.py

pause
