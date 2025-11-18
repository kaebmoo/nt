#!/bin/bash
# Fix polars version conflict in existing venv

echo "======================================"
echo "🔧 Fixing Prophet/Polars conflict in venv"
echo "======================================"

# Activate venv
source venv/bin/activate

# Uninstall problematic packages
echo ""
echo "Step 1: Removing conflicting packages..."
pip uninstall -y polars cmdstanpy prophet

# Install compatible versions
echo ""
echo "Step 2: Installing compatible versions..."
pip install "polars<0.20.0"
pip install "cmdstanpy>=1.2.0"
pip install "prophet>=1.1.5"

# Install other requirements
echo ""
echo "Step 3: Installing remaining requirements..."
cd forecast-system
pip install -r requirements.txt

echo ""
echo "======================================"
echo "✅ Fix complete!"
echo "======================================"
echo ""
echo "Now run:"
echo "  cd forecast-system"
echo "  streamlit run src/web/app.py"
echo ""
