@echo off
REM Setup script for AI Resume Analyzer on Windows

echo ========================================
echo AI Resume Analyzer - Setup
echo ========================================

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo [1/5] Creating virtual environment...
python -m venv venv

echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/5] Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo [4/5] Downloading spaCy model...
python -m spacy download en_core_web_sm

echo [5/5] Downloading sentence-transformers model...
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To run the Streamlit dashboard:
echo   streamlit run app\streamlit_app.py
echo.
echo To run the FastAPI server:
echo   uvicorn src.api:app --reload
echo.
pause