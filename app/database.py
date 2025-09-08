"""
Database models and schema for Pharmacy Finder
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, time
import sqlite3
import json
import os

@dataclass
class Pharmacy:
    """Pharmacy data model"""
    local_id: str
    nombre: str
    direccion: str
    comuna: str
    localidad: str
    region: str
    telefono: Optional[str]
    lat: float
    lng: float
    hora_apertura: str
    hora_cierre: str
    dia_funcionamiento: str
    fecha_actualizacion: str
    es_turno: bool = False

    @classmethod
    def from_api_data(cls, data: dict, es_turno: bool = False) -> 'Pharmacy':
        """Create Pharmacy instance from API data"""
        # Handle empty or invalid coordinate values
        lat_str = data.get('local_lat', '').strip()
        lng_str = data.get('local_lng', '').strip()

        try:
            lat = float(lat_str) if lat_str and lat_str != '0' else 0.0
        except (ValueError, TypeError):
            lat = 0.0

        try:
            lng = float(lng_str) if lng_str and lng_str != '0' else 0.0
        except (ValueError, TypeError):
            lng = 0.0

        return cls(
            local_id=data.get('local_id', ''),
            nombre=data.get('local_nombre', ''),
            direccion=data.get('local_direccion', ''),
            comuna=data.get('comuna_nombre', ''),
            localidad=data.get('localidad_nombre', ''),
            region=data.get('fk_region', ''),
            telefono=data.get('local_telefono'),
            lat=lat,
            lng=lng,
            hora_apertura=data.get('funcionamiento_hora_apertura', ''),
            hora_cierre=data.get('funcionamiento_hora_cierre', ''),
            dia_funcionamiento=data.get('funcionamiento_dia', ''),
            fecha_actualizacion=data.get('fecha', datetime.now().strftime('%Y-%m-%d')),
            es_turno=es_turno
        )

@dataclass
class LocationBounds:
    """Geographic bounds for filtering"""
    north: float
    south: float
    east: float
    west: float

class PharmacyDatabase:
    """SQLite database manager for pharmacies"""

    def __init__(self, db_path: str = "pharmacy_finder.db"):
        # Allow overriding via environment (e.g., when using a mounted volume on Fly)
        self.db_path = os.getenv("DATABASE_URL", db_path)
        self.init_database()

    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Pharmacies table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pharmacies (
                    local_id TEXT PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    direccion TEXT,
                    comuna TEXT,
                    localidad TEXT,
                    region TEXT,
                    telefono TEXT,
                    lat REAL,
                    lng REAL,
                    hora_apertura TEXT,
                    hora_cierre TEXT,
                    dia_funcionamiento TEXT,
                    fecha_actualizacion TEXT,
                    es_turno BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Regions table for reference
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS regions (
                    id TEXT PRIMARY KEY,
                    nombre TEXT
                )
            ''')

            # Communes table for reference
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS communes (
                    id TEXT PRIMARY KEY,
                    nombre TEXT,
                    region_id TEXT,
                    FOREIGN KEY (region_id) REFERENCES regions(id)
                )
            ''')

            # Search index for better performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_pharmacies_location
                ON pharmacies(lat, lng)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_pharmacies_comuna
                ON pharmacies(comuna)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_pharmacies_turno
                ON pharmacies(es_turno)
            ''')

            conn.commit()

    def save_pharmacy(self, pharmacy: Pharmacy):
        """Save or update pharmacy in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO pharmacies
                (local_id, nombre, direccion, comuna, localidad, region,
                 telefono, lat, lng, hora_apertura, hora_cierre,
                 dia_funcionamiento, fecha_actualizacion, es_turno)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pharmacy.local_id, pharmacy.nombre, pharmacy.direccion,
                pharmacy.comuna, pharmacy.localidad, pharmacy.region,
                pharmacy.telefono, pharmacy.lat, pharmacy.lng,
                pharmacy.hora_apertura, pharmacy.hora_cierre,
                pharmacy.dia_funcionamiento, pharmacy.fecha_actualizacion,
                pharmacy.es_turno
            ))
            conn.commit()

    def save_multiple_pharmacies(self, pharmacies: List[Pharmacy]):
        """Save multiple pharmacies efficiently"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            data = [(
                p.local_id, p.nombre, p.direccion, p.comuna, p.localidad,
                p.region, p.telefono, p.lat, p.lng, p.hora_apertura,
                p.hora_cierre, p.dia_funcionamiento, p.fecha_actualizacion,
                p.es_turno
            ) for p in pharmacies]

            cursor.executemany('''
                INSERT OR REPLACE INTO pharmacies
                (local_id, nombre, direccion, comuna, localidad, region,
                 telefono, lat, lng, hora_apertura, hora_cierre,
                 dia_funcionamiento, fecha_actualizacion, es_turno)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', data)
            conn.commit()

    def find_nearby_pharmacies(self, lat: float, lng: float,
                              radius_km: float = 10.0,
                              only_open: bool = False) -> List[Pharmacy]:
        """Find pharmacies within radius of a location using Haversine distance"""
        import math
        
        # Use a broader bounding box to get candidate pharmacies
        lat_range = radius_km / 111.0 * 1.5  # Expand by 50% to ensure we don't miss any
        lng_range = radius_km / (111.0 * math.cos(math.radians(abs(lat)))) * 1.5 if lat != 0 else radius_km / 111.0 * 1.5

        query = '''
            SELECT * FROM pharmacies
            WHERE lat BETWEEN ? AND ?
              AND lng BETWEEN ? AND ?
              AND lat != 0 AND lng != 0
        '''
        params = [lat - lat_range, lat + lat_range,
                 lng - lng_range, lng + lng_range]

        if only_open:
            query += " AND es_turno = 1"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        # Convert to pharmacy objects and filter by actual distance
        candidates = [self._row_to_pharmacy(row) for row in rows]
        
        def haversine_distance(lat1, lon1, lat2, lon2):
            """Calculate the great circle distance between two points on Earth"""
            R = 6371  # Earth's radius in kilometers
            
            # Convert latitude and longitude from degrees to radians
            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
            
            # Haversine formula
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            
            return R * c
        
        # Filter by actual distance and sort
        nearby_pharmacies = []
        for pharmacy in candidates:
            distance = haversine_distance(lat, lng, pharmacy.lat, pharmacy.lng)
            if distance <= radius_km:
                nearby_pharmacies.append((pharmacy, distance))
        
        # Sort by distance and return pharmacies only
        nearby_pharmacies.sort(key=lambda x: x[1])
        return [pharmacy for pharmacy, distance in nearby_pharmacies]

    def find_by_comuna(self, comuna: str, only_open: bool = False) -> List[Pharmacy]:
        """Find pharmacies in a specific commune"""
        query = '''
            SELECT * FROM pharmacies
            WHERE LOWER(comuna) LIKE LOWER(?)
              AND lat != 0 AND lng != 0
        '''
        params = [f'%{comuna}%']

        if only_open:
            query += " AND es_turno = 1"

        query += " ORDER BY nombre"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [self._row_to_pharmacy(row) for row in rows]

    def get_all_communes(self) -> List[str]:
        """Get list of all communes"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT comuna FROM pharmacies
                WHERE comuna IS NOT NULL AND comuna != ''
                ORDER BY comuna
            ''')
            return [row[0] for row in cursor.fetchall()]

    def get_pharmacy_count(self) -> dict:
        """Get count statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM pharmacies')
            total = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM pharmacies WHERE es_turno = 1')
            turno = cursor.fetchone()[0]

            return {
                'total': total,
                'turno': turno,
                'regular': total - turno
            }

    def _row_to_pharmacy(self, row) -> Pharmacy:
        """Convert database row to Pharmacy object"""
        return Pharmacy(
            local_id=row[0],
            nombre=row[1],
            direccion=row[2],
            comuna=row[3],
            localidad=row[4],
            region=row[5],
            telefono=row[6],
            lat=row[7],
            lng=row[8],
            hora_apertura=row[9],
            hora_cierre=row[10],
            dia_funcionamiento=row[11],
            fecha_actualizacion=row[12],
            es_turno=bool(row[13])
        )

    def clear_old_data(self, days_old: int = 7):
        """Remove data older than specified days"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM pharmacies
                WHERE created_at < datetime('now', '-{} days')
            '''.format(days_old))
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count

    def is_pharmacy_currently_open(self, pharmacy: Pharmacy) -> bool:
        """Check if a pharmacy is currently open based on time and day"""
        try:
            now = datetime.now()
            current_time = now.time()
            
            # PRIORITY 1: If it's a turno pharmacy, it should be available 24/7
            if pharmacy.es_turno:
                return True
            
            # PRIORITY 2: Check regular schedule for non-turno pharmacies
            # Map English day names to Spanish for consistency with database
            day_mapping = {
                'monday': 'lunes',
                'tuesday': 'martes', 
                'wednesday': 'miercoles',
                'thursday': 'jueves',
                'friday': 'viernes',
                'saturday': 'sabado',
                'sunday': 'domingo'
            }
            
            current_day_english = now.strftime('%A').lower()
            current_day_spanish = day_mapping.get(current_day_english, current_day_english)

            # Parse operating days
            operating_days = pharmacy.dia_funcionamiento.lower() if pharmacy.dia_funcionamiento else ""

            # Check if current day is in operating days
            day_match = False
            
            # Check for exact Spanish day match
            if current_day_spanish in operating_days:
                day_match = True
            # Check for "todos" or "all" (all days)
            elif 'todos' in operating_days or 'all' in operating_days:
                day_match = True
            # Check for English day names as fallback
            elif current_day_english in operating_days:
                day_match = True

            if not day_match:
                return False

            # Parse opening and closing times
            if not pharmacy.hora_apertura or not pharmacy.hora_cierre:
                return pharmacy.es_turno  # Fall back to turno status if no times

            try:
                # Handle various time formats (HH:MM, H:MM, etc.)
                apertura_str = pharmacy.hora_apertura.strip()
                cierre_str = pharmacy.hora_cierre.strip()

                # Remove any non-numeric characters except :
                apertura_str = ''.join(c for c in apertura_str if c.isdigit() or c == ':')
                cierre_str = ''.join(c for c in cierre_str if c.isdigit() or c == ':')

                if ':' not in apertura_str:
                    # Assume HH format
                    apertura_str += ':00'
                if ':' not in cierre_str:
                    # Assume HH format
                    cierre_str += ':00'

                apertura_time = datetime.strptime(apertura_str, '%H:%M').time()
                cierre_time = datetime.strptime(cierre_str, '%H:%M').time()

                # Check if current time is within operating hours
                if apertura_time <= cierre_time:
                    # Same day operation
                    return apertura_time <= current_time <= cierre_time
                else:
                    # Overnight operation (closes next day)
                    return current_time >= apertura_time or current_time <= cierre_time

            except (ValueError, AttributeError):
                # If time parsing fails, fall back to turno status
                return pharmacy.es_turno

        except Exception:
            # If anything fails, fall back to turno status
            return pharmacy.es_turno

    def find_nearby_pharmacies_open_now(self, lat: float, lng: float,
                                       radius_km: float = 10.0) -> List[Pharmacy]:
        """Find pharmacies within radius that are currently open"""
        pharmacies = self.find_nearby_pharmacies(lat, lng, radius_km, False)
        return [p for p in pharmacies if self.is_pharmacy_currently_open(p)]

    def find_by_comuna_open_now(self, comuna: str) -> List[Pharmacy]:
        """Find pharmacies in a commune that are currently open"""
        pharmacies = self.find_by_comuna(comuna, False)
        return [p for p in pharmacies if self.is_pharmacy_currently_open(p)]


# ---------------------------------------------------------------------------
# Backwards-compatible module-level API
# Some tests and legacy code import functions directly from `app.database`.
# Provide thin wrappers around a module-level default database instance.
# ---------------------------------------------------------------------------


_default_db = PharmacyDatabase()


def find_nearby_pharmacies(lat: float, lng: float, radius_km: float = 10.0, only_open: bool = False):
    return _default_db.find_nearby_pharmacies(lat, lng, radius_km, only_open)


def find_nearby_pharmacies_open_now(lat: float, lng: float, radius_km: float = 10.0):
    return _default_db.find_nearby_pharmacies_open_now(lat, lng, radius_km)


def find_by_comuna(comuna: str, only_open: bool = False):
    return _default_db.find_by_comuna(comuna, only_open)


def find_by_comuna_open_now(comuna: str):
    return _default_db.find_by_comuna_open_now(comuna)


def get_pharmacy_count():
    return _default_db.get_pharmacy_count()


def get_all_communes():
    return _default_db.get_all_communes()

