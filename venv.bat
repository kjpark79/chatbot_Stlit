@echo off
chcp 65001 > nul
:: 한글 깨짐 방지
:: .venv 폴더 확인
if not exist ".venv" (
    echo [.venv] folder not found. Creating virtual environment...
    python -m venv .venv
    echo Virtual environment created.
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo [.venv] folder found. Activating virtual environment...
    call .venv\Scripts\activate.bat
)

:: 커맨드 창 유지
cmd /k