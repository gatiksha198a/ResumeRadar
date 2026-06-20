#!/bin/bash
# Setup script for AI Resume Analyzer on Linux/Mac

echo "========================================"
echo "AI Resume Analyzer - Setup"
echo "========================================"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "[1/5] Creating virtual environment..."
python3 -m venv venv

echo "[2/5] Activating virtual environment..."
source venv/bin/activate

echo "[3/5] Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[4/5] Downloading spaCy model..."
python3 -m spacy download en_core_web_sm

echo "[5/5] Downloading sentence-transformers model..."
python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "To run the Streamlit dashboard:"
echo "   streamlit run app/streamlit_app.py"
echo ""
echo "To run the FastAPI server:"
echo "   uvicorn src.api:app --reload"
echo ""