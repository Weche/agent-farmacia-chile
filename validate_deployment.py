#!/usr/bin/env python3
"""
Deployment validation script for Fly.io
Validates that all required components are properly configured
"""
import os
import sys
from pathlib import Path

def validate_deployment():
    """Validate deployment configuration"""
    print("Validating Fly.io deployment configuration...")
    errors = []
    warnings = []
    
    # Check environment variables
    required_env_vars = [
        'DATABASE_URL',
        'VADEMECUM_PATH', 
        'REDIS_URL',
        'OPENAI_API_KEY'
    ]
    
    for var in required_env_vars:
        value = os.getenv(var)
        if not value:
            errors.append(f"Missing required environment variable: {var}")
        else:
            print(f"OK {var}: Configured")
    
    # Check file paths
    db_path = os.getenv('DATABASE_URL', 'pharmacy_finder.db')
    vademecum_path = os.getenv('VADEMECUM_PATH', './data/comprehensive_vademecum.csv')
    
    # In production, these files might not exist yet, so just check if paths are reasonable
    if not db_path.startswith('/app/data/'):
        warnings.append(f"WARNING Database path may not be in volume: {db_path}")
    else:
        print(f"OK Database path looks correct: {db_path}")
    
    if not vademecum_path.startswith('/app/data/'):
        warnings.append(f"WARNING Vademecum path may not be in volume: {vademecum_path}")
    else:
        print(f"OK Vademecum path looks correct: {vademecum_path}")
    
    # Check if running in expected environment
    env = os.getenv('ENV', 'dev')
    if env == 'production':
        print(f"OK Environment: {env}")
    else:
        warnings.append(f"WARNING Not running in production mode: {env}")
    
    # Test import statements
    try:
        from app.database import PharmacyDatabase
        print("OK Database module imports correctly")
    except Exception as e:
        errors.append(f"ERROR Database import failed: {e}")
    
    try:
        from app.services.vademecum_service import load_vademecum
        print("OK Vademecum service imports correctly") 
    except Exception as e:
        errors.append(f"ERROR Vademecum service import failed: {e}")
    
    try:
        from app.agents.spanish_agent import SpanishPharmacyAgent
        print("OK AI Agent imports correctly")
    except Exception as e:
        errors.append(f"ERROR AI Agent import failed: {e}")
    
    # Summary
    print("\n" + "="*50)
    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print(error)
    else:
        print("VALIDATION PASSED")
    
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(warning)
    
    print("="*50)
    return len(errors) == 0

if __name__ == "__main__":
    success = validate_deployment()
    sys.exit(0 if success else 1)