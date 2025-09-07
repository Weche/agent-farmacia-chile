"""
Automatic database update service
Ensures pharmacy data is always fresh
"""
import os
import sys
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any
import asyncio

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from data.import_data import MINSALDataImporter
from app.database import PharmacyDatabase


class DataUpdateService:
    """Service to manage automatic database updates"""
    
    def __init__(self, db_path: str = "pharmacy_finder.db", max_age_hours: int = None):
        self.db_path = db_path
        # Get max age from environment or use default
        if max_age_hours is None:
            max_age_hours = int(os.getenv('AUTO_UPDATE_DB_HOURS', '1'))  # 1 hour default
        self.max_age_hours = max_age_hours
        self.db = PharmacyDatabase(db_path)
        print(f"📊 DataUpdateService initialized (max age: {self.max_age_hours}h)")
    
    def get_database_age(self) -> Dict[str, Any]:
        """Get database age and freshness info"""
        try:
            # Check database file modification time
            if os.path.exists(self.db_path):
                file_mod_time = datetime.fromtimestamp(os.path.getmtime(self.db_path))
                age_hours = (datetime.now() - file_mod_time).total_seconds() / 3600
                
                # Also check actual data age from database
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM pharmacies")
                pharmacy_count = cursor.fetchone()[0]
                conn.close()
                
                return {
                    'exists': True,
                    'file_modified': file_mod_time,
                    'age_hours': age_hours,
                    'pharmacy_count': pharmacy_count,
                    'is_fresh': age_hours < self.max_age_hours,
                    'needs_update': age_hours >= self.max_age_hours or pharmacy_count == 0
                }
            else:
                return {
                    'exists': False,
                    'needs_update': True,
                    'pharmacy_count': 0
                }
        except Exception as e:
            print(f"❌ Error checking database age: {e}")
            return {
                'exists': False,
                'needs_update': True,
                'pharmacy_count': 0,
                'error': str(e)
            }
    
    async def update_if_needed(self) -> Dict[str, Any]:
        """Update database if needed, return status"""
        # Check if auto-updates are disabled
        if self.max_age_hours <= 0:
            print(f"🚫 Auto-updates disabled (max_age_hours: {self.max_age_hours})")
            info = self.get_database_age()
            return {
                'updated': False,
                'reason': 'Auto-updates disabled',
                'pharmacy_count': info.get('pharmacy_count', 0)
            }
        
        info = self.get_database_age()
        
        print(f"🔍 Database status:")
        print(f"   Exists: {info.get('exists', False)}")
        print(f"   Pharmacies: {info.get('pharmacy_count', 0)}")
        if info.get('age_hours'):
            print(f"   Age: {info['age_hours']:.1f} hours")
        
        if info.get('needs_update', True):
            print(f"🔄 Database needs update (max age: {self.max_age_hours}h)")
            return await self.force_update()
        else:
            print(f"✅ Database is fresh")
            return {
                'updated': False,
                'reason': 'Database is fresh',
                'pharmacy_count': info['pharmacy_count']
            }
    
    async def force_update(self) -> Dict[str, Any]:
        """Force database update"""
        try:
            print("📊 Starting pharmacy data update...")
            
            # Run import in a thread to avoid blocking
            def run_import():
                importer = MINSALDataImporter(self.db)
                importer.import_all_pharmacies()
                return self.db.get_pharmacy_count()
            
            # Run the import
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, run_import)
            
            print(f"✅ Database updated successfully!")
            print(f"   Total pharmacies: {result.get('total', 0)}")
            
            return {
                'updated': True,
                'pharmacy_count': result.get('total', 0),
                'on_duty': result.get('turno', 0),
                'regular': result.get('regular', 0)
            }
            
        except Exception as e:
            print(f"❌ Database update failed: {e}")
            return {
                'updated': False,
                'error': str(e)
            }


# Global instance
data_updater = DataUpdateService()
