#!/usr/bin/env python3
"""
Buscar medicamento Viadil o similares en la base de datos
"""

import sqlite3

def search_medications():
    conn = sqlite3.connect('pharmacy_finder.db')
    cursor = conn.cursor()

    print('🔍 Buscando medicamentos similares a "Viadil"...')
    
    # Buscar medicamentos que contengan 'via' o similares
    cursor.execute("""
        SELECT DISTINCT nombre, principio_activo, laboratorio 
        FROM medicamentos 
        WHERE LOWER(nombre) LIKE '%via%' 
        OR LOWER(principio_activo) LIKE '%via%'
        LIMIT 10
    """)

    results = cursor.fetchall()
    print(f'📊 Encontrados {len(results)} medicamentos con "via":')
    for i, (nombre, principio, lab) in enumerate(results, 1):
        print(f'{i}. {nombre} ({principio}) - {lab}')

    print('\n🔍 Medicamentos que empiezan con "V":')
    cursor.execute("""
        SELECT DISTINCT nombre, principio_activo 
        FROM medicamentos 
        WHERE LOWER(nombre) LIKE 'v%'
        ORDER BY nombre
        LIMIT 15
    """)

    results = cursor.fetchall()
    for i, (nombre, principio) in enumerate(results, 1):
        print(f'{i}. {nombre} ({principio})')

    # Buscar por nombres que suenen similar a "viadil"
    print('\n🔍 Búsqueda más amplia (contenga "dil", "dial", etc.):')
    cursor.execute("""
        SELECT DISTINCT nombre, principio_activo, laboratorio 
        FROM medicamentos 
        WHERE LOWER(nombre) LIKE '%dil%'
        OR LOWER(nombre) LIKE '%dial%'
        OR LOWER(principio_activo) LIKE '%dil%'
        ORDER BY nombre
        LIMIT 10
    """)

    results = cursor.fetchall()
    for i, (nombre, principio, lab) in enumerate(results, 1):
        print(f'{i}. {nombre} ({principio}) - {lab}')

    # Verificar total de medicamentos en DB
    cursor.execute("SELECT COUNT(*) FROM medicamentos")
    total = cursor.fetchone()[0]
    print(f'\n📊 Total medicamentos en base de datos: {total}')

    conn.close()

if __name__ == "__main__":
    search_medications()
