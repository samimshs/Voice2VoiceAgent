#!/usr/bin/env bash
set -e

VENV=".venv"
PYTHON="$VENV/bin/python"

case "$1" in

  setup)
    echo "▶ Creating virtual environment..."
    python3 -m venv "$VENV"
    echo "▶ Installing dependencies..."
    "$VENV/bin/pip" install --upgrade pip -q
    "$VENV/bin/pip" install -r requirements.txt -q
    if [ ! -f ".env" ]; then
      cp .env.example .env
      echo ""
      echo "✅ Setup complete."
      echo "   → Open .env and fill in your OPENAI_API_KEY and TAVILY_API_KEY"
      echo "   → Then run:  ./run.sh app"
    else
      echo "✅ Setup complete (.env already exists)."
      echo "   → Run:  ./run.sh app"
    fi
    ;;

  build-index)
    echo "▶ Building ChromaDB index from products.parquet..."
    "$PYTHON" scripts/build_index.py
    echo "✅ Index built at data/index/"
    ;;

  app)
    echo "▶ Starting Streamlit app at http://localhost:8501"
    "$PYTHON" -m streamlit run app.py
    ;;

  *)
    echo ""
    echo "Usage: ./run.sh <command>"
    echo ""
    echo "Commands:"
    echo "  setup        Create .venv and install all dependencies"
    echo "  build-index  Rebuild the ChromaDB vector index (only needed if you change the dataset)"
    echo "  app          Start the Streamlit UI"
    echo ""
    ;;

esac
