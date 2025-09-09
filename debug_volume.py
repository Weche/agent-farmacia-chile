#!/usr/bin/env python3
"""
Volume and Database Debug Endpoint
Add this to main.py to diagnose volume issues in production
"""

# Add this to your main.py file:

VOLUME_DEBUG_ENDPOINT = '''
@app.get("/admin/volume-debug")
async def debug_volume():
    """Debug volume mounting and database access"""
    import os
    import sqlite3
    from pathlib import Path
    
    debug_info = {
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENV", "unknown"),
        "database_url_env": os.getenv("DATABASE_URL"),
    }
    
    # Check volume directory
    volume_path = "/app/data"
    debug_info["volume_path"] = volume_path
    debug_info["volume_exists"] = os.path.exists(volume_path)
    
    if os.path.exists(volume_path):
        try:
            # List contents
            debug_info["volume_contents"] = os.listdir(volume_path)
            
            # Check permissions
            debug_info["volume_readable"] = os.access(volume_path, os.R_OK)
            debug_info["volume_writable"] = os.access(volume_path, os.W_OK)
            debug_info["volume_executable"] = os.access(volume_path, os.X_OK)
            
            # Try to create a test file
            test_file = os.path.join(volume_path, "test_write.txt")
            try:
                with open(test_file, "w") as f:
                    f.write("test")
                debug_info["can_write_files"] = True
                os.remove(test_file)  # Clean up
            except Exception as e:
                debug_info["can_write_files"] = False
                debug_info["write_error"] = str(e)
                
        except Exception as e:
            debug_info["volume_error"] = str(e)
    
    # Check database file specifically
    db_path = os.getenv("DATABASE_URL", "/app/data/pharmacy_finder.db")
    debug_info["db_path"] = db_path
    debug_info["db_file_exists"] = os.path.exists(db_path)
    
    if os.path.exists(db_path):
        try:
            debug_info["db_file_size"] = os.path.getsize(db_path)
            debug_info["db_readable"] = os.access(db_path, os.R_OK)
            debug_info["db_writable"] = os.access(db_path, os.W_OK)
            
            # Try to connect to database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            debug_info["db_tables"] = [t[0] for t in tables]
            
            # Check pharmacy count
            if ("pharmacies",) in tables:
                cursor.execute("SELECT COUNT(*) FROM pharmacies")
                count = cursor.fetchone()[0]
                debug_info["pharmacy_count"] = count
                
                # Sample data
                cursor.execute("SELECT * FROM pharmacies LIMIT 3")
                sample = cursor.fetchall()
                debug_info["sample_pharmacies"] = len(sample)
            else:
                debug_info["pharmacy_table_missing"] = True
                
            conn.close()
            debug_info["db_connection"] = "success"
            
        except Exception as e:
            debug_info["db_error"] = str(e)
    
    # Test import functionality
    debug_info["import_test"] = {}
    try:
        from app.services.data_updater import data_updater
        age_info = data_updater.get_database_age()
        debug_info["import_test"]["age_check"] = age_info
        
        # Test if we can create the database directory
        db_dir = os.path.dirname(db_path)
        os.makedirs(db_dir, exist_ok=True)
        debug_info["import_test"]["db_dir_created"] = True
        
    except Exception as e:
        debug_info["import_test"]["error"] = str(e)
    
    return {
        "status": "debug_complete",
        "debug_info": debug_info
    }


@app.post("/admin/force-volume-update")
async def force_volume_update():
    """Force database update with detailed logging"""
    try:
        from app.services.data_updater import data_updater
        
        # Get initial state
        initial_state = data_updater.get_database_age()
        
        # Force update
        update_result = await data_updater.force_update()
        
        # Get final state
        final_state = data_updater.get_database_age()
        
        return {
            "status": "force_update_complete",
            "initial_state": initial_state,
            "update_result": update_result,
            "final_state": final_state,
            "volume_path": "/app/data",
            "db_path": os.getenv("DATABASE_URL")
        }
        
    except Exception as e:
        import traceback
        return {
            "status": "force_update_failed",
            "error": str(e),
            "traceback": traceback.format_exc()
        }
'''

print("Volume Debug Endpoint Code Generated")
print("=" * 40)
print("To add volume debugging to production:")
print("1. Add the above endpoints to app/main.py")
print("2. Deploy the update")
print("3. Test with:")
print("   GET https://pharmacy-finder-chile.fly.dev/admin/volume-debug")
print("   POST https://pharmacy-finder-chile.fly.dev/admin/force-volume-update")
print()
print("This will show:")
print("- Volume mount status")
print("- File permissions") 
print("- Database connectivity")
print("- Import process details")