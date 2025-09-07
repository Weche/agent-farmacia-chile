from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json
import csv
import os

app = FastAPI()

@app.get("/")
async def vademecum_explorer():
    """Simple table to explore vademecum data"""
    
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>📊 Explorador de Vademécum</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            
            .header {
                text-align: center;
                margin-bottom: 30px;
                padding: 20px;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .controls {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
                flex-wrap: wrap;
                align-items: center;
            }
            
            .search-box {
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-width: 200px;
            }
            
            .btn {
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-weight: 500;
            }
            
            .btn-primary {
                background: #007bff;
                color: white;
            }
            
            .btn-secondary {
                background: #6c757d;
                color: white;
            }
            
            .btn:hover {
                opacity: 0.8;
            }
            
            .table-container {
                background: white;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                overflow-x: auto;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                min-width: 800px;
            }
            
            th {
                background: #f8f9fa;
                padding: 12px 8px;
                text-align: left;
                font-weight: 600;
                border-bottom: 2px solid #dee2e6;
                cursor: pointer;
                white-space: nowrap;
            }
            
            th:hover {
                background: #e9ecef;
            }
            
            td {
                padding: 10px 8px;
                border-bottom: 1px solid #dee2e6;
                max-width: 200px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            
            tr:nth-child(even) {
                background: #f8f9fa;
            }
            
            tr:hover {
                background: #e3f2fd !important;
            }
            
            .loading {
                text-align: center;
                padding: 40px;
                color: #666;
            }
            
            .status {
                margin: 10px 0;
                padding: 10px;
                border-radius: 4px;
                background: #f8f9fa;
                border-left: 4px solid #007bff;
            }
            
            .pagination {
                display: flex;
                justify-content: center;
                gap: 10px;
                margin: 20px 0;
            }
            
            .page-btn {
                padding: 8px 12px;
                border: 1px solid #ddd;
                background: white;
                border-radius: 4px;
                cursor: pointer;
            }
            
            .page-btn.active {
                background: #007bff;
                color: white;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 Explorador de Vademécum</h1>
            <p>Base de datos interactiva de medicamentos</p>
        </div>
        
        <div class="controls">
            <input type="text" class="search-box" id="searchBox" placeholder="Buscar medicamentos...">
            <button class="btn btn-primary" onclick="searchMedicines()">🔍 Buscar</button>
            <button class="btn btn-secondary" onclick="loadAllData()">📋 Ver Todo</button>
            <button class="btn btn-secondary" onclick="exportData()">💾 Exportar</button>
        </div>
        
        <div class="status" id="status">
            Listo para buscar medicamentos...
        </div>
        
        <div class="table-container">
            <div class="loading" id="loading" style="display: none;">
                Cargando datos...
            </div>
            <table id="dataTable" style="display: none;">
                <thead id="tableHead">
                </thead>
                <tbody id="tableBody">
                </tbody>
            </table>
        </div>
        
        <div class="pagination" id="pagination"></div>
        
        <script>
            let currentData = [];
            let currentPage = 1;
            let pageSize = 25;
            
            async function loadAllData() {
                try {
                    document.getElementById('loading').style.display = 'block';
                    document.getElementById('dataTable').style.display = 'none';
                    document.getElementById('status').innerHTML = 'Cargando datos...';
                    
                    const response = await fetch('/medicamentos');
                    const data = await response.json();
                    
                    if (data && data.length > 0) {
                        currentData = data;
                        displayData();
                        document.getElementById('status').innerHTML = 
                            `${data.length} medicamentos cargados`;
                    } else {
                        document.getElementById('status').innerHTML = 'No se encontraron datos.';
                    }
                } catch (error) {
                    console.error('Error:', error);
                    document.getElementById('status').innerHTML = 'Error al cargar datos: ' + error.message;
                } finally {
                    document.getElementById('loading').style.display = 'none';
                }
            }
            
            function searchMedicines() {
                const searchTerm = document.getElementById('searchBox').value.trim().toLowerCase();
                
                if (!searchTerm) {
                    loadAllData();
                    return;
                }
                
                if (currentData.length === 0) {
                    document.getElementById('status').innerHTML = 'Primero carga los datos con "Ver Todo"';
                    return;
                }
                
                const filtered = currentData.filter(item => 
                    Object.values(item).some(value => 
                        value && value.toString().toLowerCase().includes(searchTerm)
                    )
                );
                
                const originalData = currentData;
                currentData = filtered;
                currentPage = 1;
                displayData();
                
                document.getElementById('status').innerHTML = 
                    `${filtered.length} medicamentos encontrados (de ${originalData.length} totales)`;
                    
                currentData = originalData;
            }
            
            function displayData() {
                if (currentData.length === 0) return;
                
                // Create table headers
                const headers = Object.keys(currentData[0]);
                const tableHead = document.getElementById('tableHead');
                tableHead.innerHTML = '<tr>' + 
                    headers.map(header => 
                        `<th onclick="sortByColumn('${header}')">${header} ↕️</th>`
                    ).join('') + 
                    '</tr>';
                
                // Create table body
                const startIndex = (currentPage - 1) * pageSize;
                const endIndex = Math.min(startIndex + pageSize, currentData.length);
                const pageData = currentData.slice(startIndex, endIndex);
                
                const tableBody = document.getElementById('tableBody');
                tableBody.innerHTML = pageData.map(row => 
                    '<tr>' + 
                    headers.map(header => {
                        const cellValue = row[header] || '';
                        const displayValue = cellValue.toString().length > 50 ? 
                            cellValue.toString().substring(0, 50) + '...' : 
                            cellValue;
                        return `<td title="${cellValue}">${displayValue}</td>`;
                    }).join('') + 
                    '</tr>'
                ).join('');
                
                document.getElementById('dataTable').style.display = 'table';
                updatePagination();
            }
            
            function updatePagination() {
                const totalPages = Math.ceil(currentData.length / pageSize);
                const paginationDiv = document.getElementById('pagination');
                
                if (totalPages <= 1) {
                    paginationDiv.innerHTML = '';
                    return;
                }
                
                let paginationHTML = '';
                
                if (currentPage > 1) {
                    paginationHTML += `<button class="page-btn" onclick="changePage(${currentPage - 1})">← Anterior</button>`;
                }
                
                const startPage = Math.max(1, currentPage - 2);
                const endPage = Math.min(totalPages, currentPage + 2);
                
                for (let i = startPage; i <= endPage; i++) {
                    const activeClass = i === currentPage ? 'active' : '';
                    paginationHTML += `<button class="page-btn ${activeClass}" onclick="changePage(${i})">${i}</button>`;
                }
                
                if (currentPage < totalPages) {
                    paginationHTML += `<button class="page-btn" onclick="changePage(${currentPage + 1})">Siguiente →</button>`;
                }
                
                paginationDiv.innerHTML = paginationHTML;
            }
            
            function changePage(newPage) {
                currentPage = newPage;
                displayData();
            }
            
            function sortByColumn(column) {
                currentData.sort((a, b) => {
                    const aVal = (a[column] || '').toString();
                    const bVal = (b[column] || '').toString();
                    
                    if (!isNaN(parseFloat(aVal)) && !isNaN(parseFloat(bVal))) {
                        return parseFloat(aVal) - parseFloat(bVal);
                    } else {
                        return aVal.localeCompare(bVal);
                    }
                });
                
                currentPage = 1;
                displayData();
            }
            
            function exportData() {
                if (currentData.length === 0) {
                    alert('No hay datos para exportar');
                    return;
                }
                
                const headers = Object.keys(currentData[0]);
                let csvContent = headers.join(',') + '\\n';
                
                currentData.forEach(row => {
                    const values = headers.map(header => {
                        const value = row[header] || '';
                        return `"${value.toString().replace(/"/g, '""')}"`;
                    });
                    csvContent += values.join(',') + '\\n';
                });
                
                const blob = new Blob([csvContent], { type: 'text/csv' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'vademecum_data.csv';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            }
            
            document.getElementById('searchBox').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    searchMedicines();
                }
            });
            
            window.addEventListener('load', function() {
                document.getElementById('status').innerHTML = 'Página cargada. Haz clic en "Ver Todo" para cargar los medicamentos.';
            });
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

@app.get("/medicamentos")
async def get_medicamentos():
    """Load vademecum data from CSV file"""
    try:
        # Try to load from comprehensive CSV first
        csv_path = "data/comprehensive_vademecum.csv"
        if os.path.exists(csv_path):
            medicamentos = []
            with open(csv_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    medicamentos.append(row)
            return medicamentos
        
        # Fallback to JSON if CSV not available
        json_path = "data/vademecum_sample.json"
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                return data.get('medicamentos', [])
        
        # If neither exists, return sample data
        return [
            {
                "nombre": "Paracetamol 500mg",
                "principio_activo": "Paracetamol",
                "categoria": "Analgésico",
                "indicaciones": "Dolor y fiebre",
                "forma": "Comprimido",
                "concentracion": "500mg",
                "precio": "$2.500",
                "fabricante": "Lab. Chile"
            },
            {
                "nombre": "Ibuprofeno 400mg", 
                "principio_activo": "Ibuprofeno",
                "categoria": "Antiinflamatorio",
                "indicaciones": "Dolor, inflamación, fiebre",
                "forma": "Cápsula",
                "concentracion": "400mg",
                "precio": "$3.200",
                "fabricante": "Lab. Andromaco"
            }
        ]
        
    except Exception as e:
        return {"error": f"Error loading data: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
