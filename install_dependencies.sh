#!/bin/bash
# install_dependencies.sh
# Script to install all missing dependencies

echo "🚀 Installing missing dependencies for Pharmacy Finder MVP..."
echo "============================================================"

echo "📦 Installing core web framework..."
pip install fastapi>=0.115.0 uvicorn>=0.32.0

echo "📦 Installing database and caching..."
pip install redis>=5.0.1

echo "📦 Installing data processing..."
pip install pandas>=1.5.0 numpy>=1.20.0

echo "📦 Installing location services..."
pip install geopy>=2.3.0 googlemaps>=4.7.0

echo "📦 Installing text processing..."
pip install unidecode>=1.3.0

echo "📦 Installing AI/ML services..."
pip install langfuse>=2.0.0 kagglehub>=0.1.0

echo "📦 Installing optional ML features..."
pip install sentence-transformers>=2.0.0

echo "✅ All dependencies installed!"
echo "📋 To verify installation, run: pip freeze | grep -E 'fastapi|redis|pandas'"
