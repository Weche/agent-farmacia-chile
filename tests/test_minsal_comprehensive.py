#!/usr/bin/env python3
"""
🏥 COMPREHENSIVE MINSAL API VERIFICATION TEST
Explores all available columns, features, and endpoints from MINSAL API
"""

import requests
import json
import time
import os
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from collections import Counter, defaultdict
import re

load_dotenv()

# Configuration
MINSAL_API_BASE = os.getenv("MINSAL_API_BASE", "https://midas.minsal.cl/farmacia_v2/WS")
FALLBACK_BASE = "https://farmanet.minsal.cl/index.php/ws"
TIMEOUT = 15

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*80}")
    print(f"🏥 {title}")
    print(f"{'='*80}")

def print_section(section):
    """Print section header"""
    print(f"\n{'─'*60}")
    print(f"📋 {section}")
    print(f"{'─'*60}")

def analyze_field_patterns(records: List[Dict]) -> Dict[str, Any]:
    """Analyze field patterns across all records"""
    analysis = {
        "all_fields": set(),
        "field_types": defaultdict(Counter),
        "field_samples": defaultdict(list),
        "field_coverage": defaultdict(int),
        "total_records": len(records)
    }
    
    for record in records:
        if not isinstance(record, dict):
            continue
            
        for field, value in record.items():
            analysis["all_fields"].add(field)
            analysis["field_coverage"][field] += 1
            
            # Determine field type
            if value is None:
                field_type = "null"
            elif isinstance(value, bool):
                field_type = "boolean"
            elif isinstance(value, int):
                field_type = "integer"
            elif isinstance(value, float):
                field_type = "float"
            elif isinstance(value, str):
                if value.strip() == "":
                    field_type = "empty_string"
                elif re.match(r'^-?\d+(\.\d+)?$', value.strip()):
                    field_type = "numeric_string"
                elif '@' in value and '.' in value:
                    field_type = "email_string"
                elif value.strip().lower() in ['true', 'false', 'yes', 'no', 'si', '1', '0']:
                    field_type = "boolean_string"
                elif re.match(r'^\d{2}:\d{2}(:\d{2})?$', value.strip()):
                    field_type = "time_string"
                elif 'http' in value.lower():
                    field_type = "url_string"
                elif len(value) > 100:
                    field_type = "long_string"
                else:
                    field_type = "string"
            else:
                field_type = "other"
            
            analysis["field_types"][field][field_type] += 1
            
            # Store sample values (up to 3 per field)
            if len(analysis["field_samples"][field]) < 3:
                if value is not None and str(value).strip():
                    analysis["field_samples"][field].append(str(value)[:100])
    
    return analysis

def test_minsal_endpoints():
    """Test different MINSAL API endpoints"""
    print_header("MINSAL API ENDPOINTS DISCOVERY")
    
    endpoints_to_test = [
        ("getLocales.php", "Regular pharmacies"),
        ("getLocalesTurnos.php", "Emergency/turno pharmacies"),
        ("getRegiones.php", "Regions list"),
        ("getComunas.php", "Communes list"),
        ("getLocalesTurnos", "Turno pharmacies (no .php)"),
        ("getLocales", "Regular pharmacies (no .php)"),
    ]
    
    results = []
    
    for base_url in [MINSAL_API_BASE, FALLBACK_BASE]:
        print(f"\n🌐 Testing base URL: {base_url}")
        print("-" * 60)
        
        base_results = {"base_url": base_url, "endpoints": {}}
        
        for endpoint, description in endpoints_to_test:
            url = f"{base_url.rstrip('/')}/{endpoint}"
            
            try:
                start_time = time.time()
                response = requests.get(url, timeout=TIMEOUT)
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        
                        # Extract actual data
                        if isinstance(data, dict) and "data" in data:
                            actual_data = data["data"]
                        else:
                            actual_data = data
                        
                        record_count = len(actual_data) if isinstance(actual_data, list) else 1
                        
                        print(f"✅ {description}")
                        print(f"   📍 URL: {url}")
                        print(f"   🕐 Response Time: {response_time:.2f}ms")
                        print(f"   📊 Records: {record_count}")
                        print(f"   📏 Response Size: {len(response.content):,} bytes")
                        
                        base_results["endpoints"][endpoint] = {
                            "status": "success",
                            "url": url,
                            "response_time": response_time,
                            "record_count": record_count,
                            "response_size": len(response.content),
                            "data": actual_data
                        }
                        
                    except json.JSONDecodeError:
                        print(f"❌ {description} - Invalid JSON response")
                        base_results["endpoints"][endpoint] = {
                            "status": "invalid_json",
                            "url": url,
                            "response_time": response_time
                        }
                else:
                    print(f"❌ {description} - HTTP {response.status_code}")
                    base_results["endpoints"][endpoint] = {
                        "status": f"http_{response.status_code}",
                        "url": url,
                        "response_time": response_time
                    }
                    
            except Exception as e:
                print(f"❌ {description} - Error: {str(e)}")
                base_results["endpoints"][endpoint] = {
                    "status": "error",
                    "url": url,
                    "error": str(e)
                }
        
        results.append(base_results)
    
    return results

def analyze_pharmacy_data(endpoint_results: List[Dict]) -> Dict[str, Any]:
    """Analyze pharmacy data structure and available fields"""
    print_header("PHARMACY DATA STRUCTURE ANALYSIS")
    
    # Find the best endpoint with data
    best_endpoint = None
    best_data = None
    
    for base_result in endpoint_results:
        for endpoint, result in base_result["endpoints"].items():
            if result.get("status") == "success" and result.get("data"):
                if isinstance(result["data"], list) and len(result["data"]) > 0:
                    if best_endpoint is None or result["record_count"] > best_data["record_count"]:
                        best_endpoint = endpoint
                        best_data = result
    
    if not best_data:
        print("❌ No valid pharmacy data found")
        return {}
    
    print(f"📊 Analyzing data from endpoint: {best_endpoint}")
    print(f"📊 Total records: {best_data['record_count']}")
    
    # Analyze field patterns
    records = best_data["data"]
    analysis = analyze_field_patterns(records)
    
    print_section("ALL AVAILABLE FIELDS")
    
    # Sort fields by coverage (most common first)
    sorted_fields = sorted(analysis["all_fields"], 
                          key=lambda x: analysis["field_coverage"][x], 
                          reverse=True)
    
    for field in sorted_fields:
        coverage = analysis["field_coverage"][field]
        coverage_pct = (coverage / analysis["total_records"]) * 100
        main_type = analysis["field_types"][field].most_common(1)[0][0]
        samples = analysis["field_samples"][field]
        
        print(f"📝 {field}")
        print(f"   📊 Coverage: {coverage}/{analysis['total_records']} ({coverage_pct:.1f}%)")
        print(f"   🔧 Main Type: {main_type}")
        if samples:
            print(f"   💡 Examples: {', '.join(samples[:2])}")
    
    return analysis

def test_location_features(endpoint_results: List[Dict]) -> Dict[str, Any]:
    """Test location and 'como llegar' features"""
    print_header("LOCATION & 'COMO LLEGAR' FEATURES")
    
    # Find pharmacy data
    pharmacy_data = None
    for base_result in endpoint_results:
        for endpoint, result in base_result["endpoints"].items():
            if result.get("status") == "success" and result.get("data"):
                if isinstance(result["data"], list) and len(result["data"]) > 0:
                    pharmacy_data = result["data"]
                    break
        if pharmacy_data:
            break
    
    if not pharmacy_data:
        print("❌ No pharmacy data available")
        return {}
    
    location_analysis = {
        "total_records": len(pharmacy_data),
        "address_fields": [],
        "coordinate_fields": [],
        "google_maps_urls": 0,
        "location_features": {}
    }
    
    # Sample first few records for detailed analysis
    sample_size = min(5, len(pharmacy_data))
    sample_records = pharmacy_data[:sample_size]
    
    print_section("LOCATION FIELD DETECTION")
    
    location_keywords = [
        ("direccion", "Address fields"),
        ("direc", "Address fields (short)"),
        ("ubicacion", "Location fields"),
        ("address", "Address fields (EN)"),
        ("lat", "Latitude fields"),
        ("lng", "Longitude fields"), 
        ("long", "Longitude fields"),
        ("coord", "Coordinate fields"),
        ("maps", "Map URL fields"),
        ("como", "Como llegar fields"),
        ("llegar", "Como llegar fields"),
        ("telefono", "Phone fields"),
        ("horario", "Schedule fields"),
        ("funcionamiento", "Operation fields")
    ]
    
    found_fields = defaultdict(list)
    
    for record in sample_records:
        if not isinstance(record, dict):
            continue
            
        for field, value in record.items():
            field_lower = field.lower()
            
            for keyword, category in location_keywords:
                if keyword in field_lower:
                    found_fields[category].append({
                        "field": field,
                        "value": str(value)[:100] if value else None,
                        "type": type(value).__name__
                    })
                    break
    
    # Print found location fields
    for category, fields in found_fields.items():
        if fields:
            print(f"🔍 {category}:")
            unique_fields = {}
            for field_info in fields:
                if field_info["field"] not in unique_fields:
                    unique_fields[field_info["field"]] = field_info
            
            for field_name, field_info in unique_fields.items():
                print(f"   📍 {field_name}: '{field_info['value']}' ({field_info['type']})")
    
    # Check for Google Maps URLs
    print_section("GOOGLE MAPS URL DETECTION")
    
    google_maps_count = 0
    google_maps_fields = set()
    
    for record in pharmacy_data:
        if not isinstance(record, dict):
            continue
            
        for field, value in record.items():
            if isinstance(value, str) and ('google.com/maps' in value.lower() or 'maps.google' in value.lower() or 'goo.gl/maps' in value.lower()):
                google_maps_count += 1
                google_maps_fields.add(field)
                break
    
    if google_maps_count > 0:
        print(f"✅ Found {google_maps_count} records with Google Maps URLs")
        print(f"📍 Fields containing Maps URLs: {', '.join(google_maps_fields)}")
    else:
        print("❌ No Google Maps URLs found")
    
    location_analysis["google_maps_urls"] = google_maps_count
    location_analysis["location_features"] = dict(found_fields)
    
    return location_analysis

def test_coordinate_data(endpoint_results: List[Dict]) -> Dict[str, Any]:
    """Test coordinate data quality and coverage"""
    print_header("COORDINATE DATA ANALYSIS")
    
    # Find pharmacy data
    pharmacy_data = None
    for base_result in endpoint_results:
        for endpoint, result in base_result["endpoints"].items():
            if result.get("status") == "success" and result.get("data"):
                if isinstance(result["data"], list) and len(result["data"]) > 0:
                    pharmacy_data = result["data"]
                    break
        if pharmacy_data:
            break
    
    if not pharmacy_data:
        print("❌ No pharmacy data available")
        return {}
    
    coordinate_analysis = {
        "total_records": len(pharmacy_data),
        "coordinates_found": 0,
        "valid_coordinates": 0,
        "chile_coordinates": 0,
        "coordinate_fields": {},
        "sample_coordinates": []
    }
    
    # Look for coordinate fields
    potential_lat_fields = []
    potential_lng_fields = []
    
    for record in pharmacy_data[:10]:  # Sample first 10 records
        if not isinstance(record, dict):
            continue
            
        for field, value in record.items():
            field_lower = field.lower()
            if 'lat' in field_lower and value and str(value).strip() not in ['0', '0.0', '']:
                potential_lat_fields.append(field)
            elif 'lng' in field_lower or 'long' in field_lower:
                if value and str(value).strip() not in ['0', '0.0', '']:
                    potential_lng_fields.append(field)
    
    # Get most common coordinate field names
    lat_field = Counter(potential_lat_fields).most_common(1)
    lng_field = Counter(potential_lng_fields).most_common(1)
    
    lat_field_name = lat_field[0][0] if lat_field else None
    lng_field_name = lng_field[0][0] if lng_field else None
    
    print(f"🔍 Detected coordinate fields:")
    print(f"   📍 Latitude field: {lat_field_name}")
    print(f"   📍 Longitude field: {lng_field_name}")
    
    if lat_field_name and lng_field_name:
        coordinates_found = 0
        valid_coordinates = 0
        chile_coordinates = 0
        
        for record in pharmacy_data:
            if not isinstance(record, dict):
                continue
                
            lat = record.get(lat_field_name)
            lng = record.get(lng_field_name)
            
            if lat and lng:
                coordinates_found += 1
                
                try:
                    lat_float = float(lat)
                    lng_float = float(lng)
                    
                    if lat_float != 0.0 and lng_float != 0.0:
                        valid_coordinates += 1
                        
                        # Check if coordinates are in Chile (approximate bounds)
                        # Chile: Latitude -55 to -17, Longitude -109 to -66
                        if -55 <= lat_float <= -17 and -109 <= lng_float <= -66:
                            chile_coordinates += 1
                            
                            # Store sample coordinates
                            if len(coordinate_analysis["sample_coordinates"]) < 5:
                                coordinate_analysis["sample_coordinates"].append({
                                    "name": record.get("nombre_local") or record.get("local_nombre") or "Unknown",
                                    "lat": lat_float,
                                    "lng": lng_float,
                                    "address": record.get("direccion") or record.get("local_direccion") or "Unknown"
                                })
                
                except (ValueError, TypeError):
                    pass
        
        coordinate_analysis.update({
            "coordinates_found": coordinates_found,
            "valid_coordinates": valid_coordinates,
            "chile_coordinates": chile_coordinates,
            "coordinate_fields": {
                "latitude": lat_field_name,
                "longitude": lng_field_name
            }
        })
        
        print_section("COORDINATE QUALITY ANALYSIS")
        print(f"📊 Records with coordinates: {coordinates_found}/{len(pharmacy_data)} ({(coordinates_found/len(pharmacy_data)*100):.1f}%)")
        print(f"📊 Valid coordinates (non-zero): {valid_coordinates}/{coordinates_found} ({(valid_coordinates/coordinates_found*100):.1f}%)" if coordinates_found > 0 else "📊 No coordinates found")
        print(f"📊 Coordinates in Chile: {chile_coordinates}/{valid_coordinates} ({(chile_coordinates/valid_coordinates*100):.1f}%)" if valid_coordinates > 0 else "📊 No valid coordinates")
        
        if coordinate_analysis["sample_coordinates"]:
            print_section("SAMPLE COORDINATES")
            for i, coord in enumerate(coordinate_analysis["sample_coordinates"], 1):
                print(f"🏥 {i}. {coord['name']}")
                print(f"   📍 Coordinates: {coord['lat']}, {coord['lng']}")
                print(f"   🏠 Address: {coord['address']}")
    
    return coordinate_analysis

def generate_summary_report(endpoint_results, field_analysis, location_analysis, coordinate_analysis):
    """Generate comprehensive summary report"""
    print_header("COMPREHENSIVE MINSAL API SUMMARY REPORT")
    
    # Endpoint summary
    print_section("ENDPOINT AVAILABILITY")
    
    working_endpoints = 0
    total_endpoints = 0
    
    for base_result in endpoint_results:
        print(f"🌐 Base URL: {base_result['base_url']}")
        
        for endpoint, result in base_result["endpoints"].items():
            total_endpoints += 1
            if result.get("status") == "success":
                working_endpoints += 1
                record_count = result.get("record_count", 0)
                response_time = result.get("response_time", 0)
                print(f"   ✅ {endpoint}: {record_count} records ({response_time:.0f}ms)")
            else:
                print(f"   ❌ {endpoint}: {result.get('status', 'unknown')}")
    
    # Data summary
    print_section("DATA STRUCTURE SUMMARY")
    
    if field_analysis:
        total_fields = len(field_analysis["all_fields"])
        total_records = field_analysis["total_records"]
        print(f"📊 Total unique fields: {total_fields}")
        print(f"📊 Total records analyzed: {total_records}")
        print(f"📊 Average fields per record: {sum(field_analysis['field_coverage'].values()) / total_fields:.1f}")
        
        # Most common fields
        sorted_fields = sorted(field_analysis["field_coverage"].items(), key=lambda x: x[1], reverse=True)
        print(f"📊 Most common fields:")
        for field, count in sorted_fields[:10]:
            coverage_pct = (count / total_records) * 100
            print(f"   📝 {field}: {coverage_pct:.1f}% coverage")
    
    # Location features summary
    print_section("LOCATION FEATURES SUMMARY")
    
    if location_analysis:
        print(f"🗺️  Total records: {location_analysis['total_records']}")
        print(f"🗺️  Google Maps URLs found: {location_analysis['google_maps_urls']}")
        
        feature_count = sum(len(fields) for fields in location_analysis['location_features'].values())
        print(f"🗺️  Location-related fields detected: {feature_count}")
        
        for category, fields in location_analysis['location_features'].items():
            if fields:
                unique_field_names = set(field['field'] for field in fields)
                print(f"   📍 {category}: {len(unique_field_names)} fields")
    
    # Coordinate summary
    print_section("COORDINATE DATA SUMMARY")
    
    if coordinate_analysis and coordinate_analysis.get("coordinate_fields"):
        total = coordinate_analysis["total_records"]
        coords = coordinate_analysis["coordinates_found"]
        valid = coordinate_analysis["valid_coordinates"]
        chile = coordinate_analysis["chile_coordinates"]
        
        print(f"📍 Coordinate coverage: {coords}/{total} ({(coords/total*100):.1f}%)")
        print(f"📍 Valid coordinates: {valid}/{coords} ({(valid/coords*100):.1f}%)" if coords > 0 else "📍 No coordinates found")
        print(f"📍 Chile coordinates: {chile}/{valid} ({(chile/valid*100):.1f}%)" if valid > 0 else "📍 No valid coordinates")
        
        if coordinate_analysis["coordinate_fields"]:
            print(f"📍 Latitude field: {coordinate_analysis['coordinate_fields']['latitude']}")
            print(f"📍 Longitude field: {coordinate_analysis['coordinate_fields']['longitude']}")
    
    # Overall assessment
    print_section("OVERALL ASSESSMENT")
    
    endpoint_score = (working_endpoints / total_endpoints) * 100 if total_endpoints > 0 else 0
    
    print(f"🎯 Endpoint Success Rate: {endpoint_score:.1f}% ({working_endpoints}/{total_endpoints})")
    
    # Feature availability
    features = []
    if location_analysis and location_analysis.get('google_maps_urls', 0) > 0:
        features.append("✅ Google Maps URLs")
    if coordinate_analysis and coordinate_analysis.get('valid_coordinates', 0) > 0:
        features.append("✅ Geographic Coordinates")
    if location_analysis and location_analysis.get('location_features'):
        features.append("✅ Address Information")
    
    if features:
        print("🚀 Available Features:")
        for feature in features:
            print(f"   {feature}")
    else:
        print("⚠️  Limited location features detected")
    
    # Recommendations
    print_section("RECOMMENDATIONS")
    
    if endpoint_score >= 75:
        print("🎉 EXCELLENT: MINSAL API is highly available and functional")
    elif endpoint_score >= 50:
        print("👍 GOOD: MINSAL API is mostly functional with some issues")
    else:
        print("⚠️  POOR: MINSAL API has significant availability issues")
    
    if coordinate_analysis and coordinate_analysis.get('chile_coordinates', 0) > 0:
        print("✅ Geographic features can be implemented (coordinates available)")
    if location_analysis and location_analysis.get('google_maps_urls', 0) > 0:
        print("✅ 'Como Llegar' feature can be implemented (Google Maps URLs available)")
    if not coordinate_analysis or coordinate_analysis.get('valid_coordinates', 0) == 0:
        print("❌ Limited geographic functionality (no valid coordinates)")

def main():
    """Run comprehensive MINSAL API test"""
    print_header("STARTING COMPREHENSIVE MINSAL API VERIFICATION")
    
    # Test endpoints
    endpoint_results = test_minsal_endpoints()
    
    # Analyze pharmacy data structure
    field_analysis = analyze_pharmacy_data(endpoint_results)
    
    # Test location features
    location_analysis = test_location_features(endpoint_results)
    
    # Test coordinate data
    coordinate_analysis = test_coordinate_data(endpoint_results)
    
    # Generate summary report
    generate_summary_report(endpoint_results, field_analysis, location_analysis, coordinate_analysis)
    
    print(f"\n🎉 MINSAL API comprehensive test completed!")

if __name__ == "__main__":
    main()
