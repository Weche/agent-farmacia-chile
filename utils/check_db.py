#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('pharmacy_finder.db')
cursor = conn.cursor()

# Check what tables exist
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('Tablas en la base de datos:')
for table in tables:
    print(f'  - {table[0]}')

# Check if either farmacias or pharmacies exists and their structure
for table_name in ['farmacias', 'pharmacies']:
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        if columns:
            print(f'\nEstructura tabla {table_name}:')
            for col in columns:
                print(f'  - {col[1]} ({col[2]})')
                
            # Count records
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f'  Total registros: {count}')
    except sqlite3.OperationalError as e:
        print(f'\nTabla {table_name}: {e}')

conn.close()
