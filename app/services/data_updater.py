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

# Add parent directory to path for proper imports
current_dir = os.path.dirname(__file__)
app_root = os.path.join(current_dir, '../..')
sys.path.insert(0, app_root)

print(f"🔍 Attempting to import from app_root: {app_root}")
print(f"🔍 Current working directory: {os.getcwd()}")
print(f"🔍 Python path: {sys.path[:3]}")  # Show first 3 paths

try:
    from data.import_data import MINSALDataImporter
    print("✅ Successfully imported MINSALDataImporter via data.import_data")
except ImportError as e:
    print(f"❌ Failed to import data.import_data: {e}")
    # Try multiple fallback paths
    import importlib.util
    
    fallback_paths = [
        os.path.join(app_root, 'data', 'import_data.py'),
        '/app/data_source/import_data.py',  # New source backup location
        '/app/data/import_data.py',  # Original data location
    ]
    
    for import_data_path in fallback_paths:
        print(f"🔍 Trying fallback import from: {import_data_path}")
        if os.path.exists(import_data_path):
            print("✅ Found import_data.py file, attempting dynamic import")
            spec = importlib.util.spec_from_file_location("import_data", import_data_path)
            import_data_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(import_data_module)
            MINSALDataImporter = import_data_module.MINSALDataImporter
            print(f"✅ Successfully imported MINSALDataImporter via fallback: {import_data_path}")
            break
        else:
            print(f"❌ Not found at: {import_data_path}")
    else:
        # List what files are actually there in various directories
        for check_dir in ['/app/data', '/app/data_source', os.path.join(app_root, 'data')]:
            if os.path.exists(check_dir):
                print(f"📁 Files in {check_dir}: {os.listdir(check_dir)}")
        raise ImportError("Cannot import MINSALDataImporter - not found in any fallback path")

from app.database import PharmacyDatabase


class DataUpdateService:
    """Service to manage automatic database updates"""
    
    def __init__(self, db_path: str = None, max_age_hours: int = None):
        # Prefer env path (e.g., Fly volume); fallback to local file
        if db_path is None:
            db_path = os.getenv('DATABASE_URL', 'pharmacy_finder.db')
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
