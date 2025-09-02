#!/usr/bin/env powershell
# Script para mover todos los archivos test_*.py del directorio raíz a tests/

Write-Host "🔄 Moviendo archivos de test al directorio tests/" -ForegroundColor Yellow

# Obtener todos los archivos test_*.py del directorio raíz
$testFiles = Get-ChildItem -Path "." -Name "test_*.py" -File

Write-Host "📁 Archivos encontrados: $($testFiles.Count)" -ForegroundColor Cyan

foreach ($file in $testFiles) {
    $sourcePath = $file
    $destPath = "tests\$file"
    
    Write-Host "➡️  Moviendo: $file" -ForegroundColor Green
    
    # Verificar si el archivo ya existe en tests/
    if (Test-Path $destPath) {
        Write-Host "⚠️  El archivo $destPath ya existe. Creando backup..." -ForegroundColor Yellow
        $backupPath = "tests\$($file).backup"
        Move-Item $destPath $backupPath -Force
        Write-Host "📦 Backup creado: $backupPath" -ForegroundColor Blue
    }
    
    # Mover el archivo
    Move-Item $sourcePath $destPath -Force
    Write-Host "✅ Movido: $file -> tests\$file" -ForegroundColor Green
}

Write-Host "`n🧹 Limpiando archivos __pycache__ relacionados..." -ForegroundColor Yellow

# Limpiar archivos .pyc del __pycache__ del directorio raíz
if (Test-Path "__pycache__") {
    Get-ChildItem -Path "__pycache__" -Name "test_*.pyc" -File | ForEach-Object {
        $pycFile = "__pycache__\$_"
        Remove-Item $pycFile -Force
        Write-Host "🗑️  Eliminado: $pycFile" -ForegroundColor Red
    }
}

Write-Host "`n✨ Limpieza completada!" -ForegroundColor Green
Write-Host "📊 Verificando estructura final..." -ForegroundColor Cyan

# Mostrar resumen
$remainingTests = Get-ChildItem -Path "." -Name "test_*.py" -File
$testsInFolder = Get-ChildItem -Path "tests" -Name "test_*.py" -File

Write-Host "`n📈 RESUMEN:" -ForegroundColor Magenta
Write-Host "  - Archivos test_*.py en raíz: $($remainingTests.Count)" -ForegroundColor White
Write-Host "  - Archivos test_*.py en tests/: $($testsInFolder.Count)" -ForegroundColor White

if ($remainingTests.Count -eq 0) {
    Write-Host "`n🎉 ¡Todos los archivos de test han sido movidos exitosamente!" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  Algunos archivos de test permanecen en el directorio raíz:" -ForegroundColor Yellow
    $remainingTests | ForEach-Object { Write-Host "    - $_" -ForegroundColor Yellow }
}
