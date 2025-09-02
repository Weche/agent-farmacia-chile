# install_dependencies.ps1
# PowerShell script to install all missing dependencies

Write-Host "🚀 Installing missing dependencies for Pharmacy Finder MVP..." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green

Write-Host "📦 Installing core web framework..." -ForegroundColor Yellow
pip install "fastapi>=0.115.0" "uvicorn>=0.32.0"

Write-Host "📦 Installing database and caching..." -ForegroundColor Yellow
pip install "redis>=5.0.1"

Write-Host "📦 Installing data processing..." -ForegroundColor Yellow
pip install "pandas>=1.5.0" "numpy>=1.20.0"

Write-Host "📦 Installing location services..." -ForegroundColor Yellow
pip install "geopy>=2.3.0" "googlemaps>=4.7.0"

Write-Host "📦 Installing text processing..." -ForegroundColor Yellow
pip install "unidecode>=1.3.0"

Write-Host "📦 Installing AI/ML services..." -ForegroundColor Yellow
pip install "langfuse>=2.0.0" "kagglehub>=0.1.0"

Write-Host "📦 Installing optional ML features..." -ForegroundColor Yellow
pip install "sentence-transformers>=2.0.0"

Write-Host "✅ All dependencies installed!" -ForegroundColor Green
Write-Host "📋 To verify installation, run: pip freeze" -ForegroundColor Cyan
