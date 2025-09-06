#!/usr/bin/env python3
"""
🗺️ ENHANCED MINSAL DATA UTILIZATION
Integration of all MINSAL API features into our pharmacy system
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import math

class EnhancedMinsalClient:
    """Enhanced client that utilizes all available MINSAL API features"""
    
    BASE_URL = "https://midas.minsal.cl/farmacia_v2/WS"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 10
    
    def get_full_pharmacy_data(self, include_turno: bool = True) -> Dict:
        """Get comprehensive pharmacy data with all fields"""
        results = {
            "regular_pharmacies": [],
            "turno_pharmacies": [],
            "total_count": 0,
            "data_fields": set(),
            "coordinate_stats": {
                "total": 0,
                "with_coordinates": 0,
                "valid_coordinates": 0
            }
        }
        
        # Get regular pharmacies
        try:
            response = self.session.get(f"{self.BASE_URL}/getLocales.php")
            if response.status_code == 200:
                regular_data = response.json()
                results["regular_pharmacies"] = regular_data
                results["total_count"] += len(regular_data)
                
                # Analyze data structure
                if regular_data:
                    results["data_fields"].update(regular_data[0].keys())
                    results["coordinate_stats"]["total"] = len(regular_data)
                    
                    for pharmacy in regular_data:
                        # Check coordinate availability
                        if 'local_lat' in pharmacy and 'local_lng' in pharmacy:
                            results["coordinate_stats"]["with_coordinates"] += 1
                            
                            try:
                                lat = float(pharmacy['local_lat'])
                                lng = float(pharmacy['local_lng'])
                                
                                # Validate coordinates (Chile bounds approximately)
                                if -56 <= lat <= -17 and -109 <= lng <= -66:
                                    results["coordinate_stats"]["valid_coordinates"] += 1
                            except (ValueError, TypeError):
                                pass
                                
        except Exception as e:
            print(f"Error fetching regular pharmacies: {e}")
        
        # Get turno pharmacies if requested
        if include_turno:
            try:
                response = self.session.get(f"{self.BASE_URL}/getLocalesTurnos.php")
                if response.status_code == 200:
                    turno_data = response.json()
                    results["turno_pharmacies"] = turno_data
                    results["total_count"] += len(turno_data)
                    
                    if turno_data:
                        results["data_fields"].update(turno_data[0].keys())
                        
            except Exception as e:
                print(f"Error fetching turno pharmacies: {e}")
        
        results["data_fields"] = list(results["data_fields"])
        return results
    
    def generate_google_maps_url(self, pharmacy: Dict) -> Optional[str]:
        """Generate Google Maps URL for a pharmacy"""
        try:
            lat = float(pharmacy.get('local_lat', 0))
            lng = float(pharmacy.get('local_lng', 0))
            name = pharmacy.get('local_nombre', 'Farmacia')
            address = pharmacy.get('local_direccion', '')
            
            if lat != 0 and lng != 0:
                # Google Maps URL with coordinates and name
                query = f"{name} {address}".replace(' ', '+')
                return f"https://maps.google.com/maps?q={lat},{lng}+({query})"
            
        except (ValueError, TypeError):
            pass
        
        return None
    
    def generate_directions_url(self, pharmacy: Dict, from_address: str = "") -> Optional[str]:
        """Generate Google Maps directions URL"""
        try:
            lat = float(pharmacy.get('local_lat', 0))
            lng = float(pharmacy.get('local_lng', 0))
            
            if lat != 0 and lng != 0:
                destination = f"{lat},{lng}"
                if from_address:
                    return f"https://maps.google.com/maps?saddr={from_address.replace(' ', '+')}&daddr={destination}"
                else:
                    return f"https://maps.google.com/maps?daddr={destination}"
                    
        except (ValueError, TypeError):
            pass
        
        return None
    
    def calculate_distance(self, pharmacy: Dict, user_lat: float, user_lng: float) -> Optional[float]:
        """Calculate distance between user and pharmacy (Haversine formula)"""
        try:
            pharm_lat = float(pharmacy.get('local_lat', 0))
            pharm_lng = float(pharmacy.get('local_lng', 0))
            
            if pharm_lat == 0 or pharm_lng == 0:
                return None
            
            # Haversine formula
            R = 6371  # Earth's radius in kilometers
            
            lat1_rad = math.radians(user_lat)
            lat2_rad = math.radians(pharm_lat)
            delta_lat = math.radians(pharm_lat - user_lat)
            delta_lng = math.radians(pharm_lng - user_lng)
            
            a = (math.sin(delta_lat/2)**2 + 
                 math.cos(lat1_rad) * math.cos(lat2_rad) * 
                 math.sin(delta_lng/2)**2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            
            distance = R * c
            return round(distance, 2)
            
        except (ValueError, TypeError):
            return None
    
    def find_nearest_pharmacies(self, user_lat: float, user_lng: float, 
                               limit: int = 10, max_distance_km: float = 50) -> List[Dict]:
        """Find nearest pharmacies to user location"""
        data = self.get_full_pharmacy_data()
        all_pharmacies = data["regular_pharmacies"] + data["turno_pharmacies"]
        
        pharmacies_with_distance = []
        
        for pharmacy in all_pharmacies:
            distance = self.calculate_distance(pharmacy, user_lat, user_lng)
            
            if distance is not None and distance <= max_distance_km:
                pharmacy_enhanced = pharmacy.copy()
                pharmacy_enhanced['distance_km'] = distance
                pharmacy_enhanced['google_maps_url'] = self.generate_google_maps_url(pharmacy)
                pharmacy_enhanced['directions_url'] = self.generate_directions_url(pharmacy)
                pharmacies_with_distance.append(pharmacy_enhanced)
        
        # Sort by distance and return top results
        pharmacies_with_distance.sort(key=lambda x: x['distance_km'])
        return pharmacies_with_distance[:limit]
    
    def get_pharmacy_operating_info(self, pharmacy: Dict) -> Dict:
        """Extract comprehensive operating information"""
        return {
            "name": pharmacy.get('local_nombre', 'N/A'),
            "address": pharmacy.get('local_direccion', 'N/A'),
            "phone": pharmacy.get('local_telefono', 'N/A'),
            "commune": pharmacy.get('comuna_nombre', 'N/A'),
            "locality": pharmacy.get('localidad_nombre', 'N/A'),
            "opening_hours": {
                "opening_time": pharmacy.get('funcionamiento_hora_apertura', 'N/A'),
                "closing_time": pharmacy.get('funcionamiento_hora_cierre', 'N/A'),
                "current_day": pharmacy.get('funcionamiento_dia', 'N/A')
            },
            "coordinates": {
                "latitude": pharmacy.get('local_lat', None),
                "longitude": pharmacy.get('local_lng', None)
            },
            "ids": {
                "pharmacy_id": pharmacy.get('local_id', None),
                "region_id": pharmacy.get('fk_region', None),
                "commune_id": pharmacy.get('fk_comuna', None),
                "locality_id": pharmacy.get('fk_localidad', None)
            },
            "data_date": pharmacy.get('fecha', 'N/A')
        }
    
    def get_enhanced_pharmacy_summary(self) -> Dict:
        """Get comprehensive summary with all features"""
        data = self.get_full_pharmacy_data()
        
        # Analyze available features
        features = {
            "location_services": False,
            "operating_hours": False,
            "contact_info": False,
            "geographic_hierarchy": False
        }
        
        sample_pharmacy = None
        if data["regular_pharmacies"]:
            sample_pharmacy = data["regular_pharmacies"][0]
            
            # Check for location services
            if 'local_lat' in sample_pharmacy and 'local_lng' in sample_pharmacy:
                features["location_services"] = True
            
            # Check for operating hours
            if 'funcionamiento_hora_apertura' in sample_pharmacy:
                features["operating_hours"] = True
            
            # Check for contact info
            if 'local_telefono' in sample_pharmacy:
                features["contact_info"] = True
            
            # Check for geographic hierarchy
            if 'fk_region' in sample_pharmacy and 'fk_comuna' in sample_pharmacy:
                features["geographic_hierarchy"] = True
        
        return {
            "summary": {
                "total_pharmacies": data["total_count"],
                "regular_pharmacies": len(data["regular_pharmacies"]),
                "turno_pharmacies": len(data["turno_pharmacies"]),
                "coordinate_coverage": f"{data['coordinate_stats']['with_coordinates']}/{data['coordinate_stats']['total']} ({data['coordinate_stats']['with_coordinates']/data['coordinate_stats']['total']*100:.1f}%)" if data['coordinate_stats']['total'] > 0 else "0/0 (0%)",
                "valid_coordinates": f"{data['coordinate_stats']['valid_coordinates']}/{data['coordinate_stats']['with_coordinates']} ({data['coordinate_stats']['valid_coordinates']/data['coordinate_stats']['with_coordinates']*100:.1f}%)" if data['coordinate_stats']['with_coordinates'] > 0 else "0/0 (0%)"
            },
            "available_fields": data["data_fields"],
            "features": features,
            "capabilities": {
                "google_maps_integration": features["location_services"],
                "directions_api": features["location_services"],
                "distance_calculation": features["location_services"],
                "nearest_pharmacy_search": features["location_services"],
                "operating_hours_display": features["operating_hours"],
                "contact_information": features["contact_info"],
                "geographic_filtering": features["geographic_hierarchy"]
            }
        }


def test_enhanced_minsal_features():
    """Test all enhanced MINSAL features"""
    print("🗺️ TESTING ENHANCED MINSAL FEATURES")
    print("=" * 60)
    
    client = EnhancedMinsalClient()
    
    # Test 1: Get comprehensive summary
    print("\n1️⃣ COMPREHENSIVE API SUMMARY:")
    print("-" * 40)
    summary = client.get_enhanced_pharmacy_summary()
    
    print(f"📊 Total Pharmacies: {summary['summary']['total_pharmacies']}")
    print(f"🏪 Regular: {summary['summary']['regular_pharmacies']}")
    print(f"🚨 Turno: {summary['summary']['turno_pharmacies']}")
    print(f"📍 Coordinate Coverage: {summary['summary']['coordinate_coverage']}")
    print(f"✅ Valid Coordinates: {summary['summary']['valid_coordinates']}")
    
    print(f"\n🚀 Available Capabilities:")
    for capability, available in summary['capabilities'].items():
        print(f"   {'✅' if available else '❌'} {capability.replace('_', ' ').title()}: {available}")
    
    # Test 2: Find nearest pharmacies (example with Santiago coordinates)
    print("\n2️⃣ NEAREST PHARMACY SEARCH:")
    print("-" * 40)
    santiago_lat, santiago_lng = -33.4489, -70.6693  # Santiago center
    
    try:
        nearest = client.find_nearest_pharmacies(santiago_lat, santiago_lng, limit=5)
        print(f"🔍 Found {len(nearest)} nearest pharmacies to Santiago center:")
        
        for i, pharmacy in enumerate(nearest, 1):
            print(f"\n🏥 {i}. {pharmacy.get('local_nombre', 'N/A')}")
            print(f"   📍 Address: {pharmacy.get('local_direccion', 'N/A')}")
            print(f"   📏 Distance: {pharmacy.get('distance_km', 'N/A')} km")
            print(f"   🗺️  Maps: {pharmacy.get('google_maps_url', 'N/A')[:50]}..." if pharmacy.get('google_maps_url') else "   🗺️  Maps: N/A")
            
    except Exception as e:
        print(f"❌ Error in nearest pharmacy search: {e}")
    
    # Test 3: Operating hours analysis
    print("\n3️⃣ OPERATING HOURS ANALYSIS:")
    print("-" * 40)
    try:
        data = client.get_full_pharmacy_data()
        if data["regular_pharmacies"]:
            sample = data["regular_pharmacies"][0]
            operating_info = client.get_pharmacy_operating_info(sample)
            
            print(f"📋 Sample Pharmacy: {operating_info['name']}")
            print(f"🕐 Opening Hours:")
            print(f"   ⏰ Opens: {operating_info['opening_hours']['opening_time']}")
            print(f"   ⏰ Closes: {operating_info['opening_hours']['closing_time']}")
            print(f"   📅 Current Day: {operating_info['opening_hours']['current_day']}")
            print(f"   📞 Phone: {operating_info['phone']}")
            print(f"   📍 Location: {operating_info['commune']}, {operating_info['locality']}")
            
    except Exception as e:
        print(f"❌ Error in operating hours analysis: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Enhanced MINSAL features test completed!")
    

if __name__ == "__main__":
    test_enhanced_minsal_features()
