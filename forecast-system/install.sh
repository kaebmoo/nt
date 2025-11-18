#!/bin/bash
# ติดตั้ง Forecast System พร้อมแก้ปัญหา dependency conflicts

echo "======================================"
echo "🚀 Installing Forecast System"
echo "======================================"

# Step 1: Uninstall problematic packages
echo ""
echo "Step 1: Removing conflicting packages..."
pip uninstall -y polars cmdstanpy prophet 2>/dev/null || true

# Step 2: Install compatible versions
echo ""
echo "Step 2: Installing compatible versions..."
pip install "polars<0.20.0"
pip install "cmdstanpy>=1.2.0"
pip install "prophet>=1.1.5"

# Step 3: Install remaining requirements
echo ""
echo "Step 3: Installing all requirements..."
pip install -r requirements.txt

echo ""
echo "======================================"
echo "✅ Installation complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Run example: python examples/joint_forecast_example.py"
echo "2. Run web app: streamlit run src/web/app.py"
echo ""
