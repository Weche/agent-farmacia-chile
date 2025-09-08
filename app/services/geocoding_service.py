"""
Reverse Geocoding Service
Detects commune/city from GPS coordinates using local database + external APIs
"""
import math
import requests
import sqlite3
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class LocationInfo:
    """Location information from reverse geocoding"""
    commune: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    confidence: float = 0.0
    method: str = "unknown"
    raw_data: Optional[Dict] = None

class ReverseGeocodingService:
    """Service for reverse geocoding - converting coordinates to location names"""
    
    def __init__(self, db_path: str = "pharmacy_finder.db"):
        self.db_path = db_path
        self.commune_centers = {}
        self._load_commune_centers()
    
    def _load_commune_centers(self):
        """Load commune centers from our pharmacy database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Calculate average coordinates for each commune from pharmacies
                cursor.execute('''
                    SELECT comuna, 
                           AVG(lat) as center_lat, 
                           AVG(lng) as center_lng,
                           COUNT(*) as pharmacy_count
                    FROM pharmacies 
                    WHERE lat != 0 AND lng != 0 
                      AND comuna IS NOT NULL 
                      AND comuna != ''
                    GROUP BY comuna
                    HAVING COUNT(*) >= 2
                    ORDER BY pharmacy_count DESC
                ''')
                
                for row in cursor.fetchall():
                    commune, lat, lng, count = row
                    self.commune_centers[commune.upper()] = {
                        'lat': float(lat),
                        'lng': float(lng),
                        'pharmacy_count': count
                    }
                
                logger.info(f"✅ Loaded {len(self.commune_centers)} commune centers from database")
        except Exception as e:
            logger.error(f"❌ Error loading commune centers: {e}")
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        # Convert to radians
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Earth radius in kilometers
        
        return c * r
    
    def _reverse_geocode_local(self, lat: float, lng: float) -> LocationInfo:
        """Use local database to find closest commune"""
        if not self.commune_centers:
            return LocationInfo(method="local_no_data")
        
        closest_commune = None
        min_distance = float('inf')
        
        for commune, center in self.commune_centers.items():
            distance = self._calculate_distance(
                lat, lng, center['lat'], center['lng']
            )
            
            if distance < min_distance:
                min_distance = distance
                closest_commune = commune
        
        if closest_commune and min_distance <= 50:  # Within 50km
            # Calculate confidence based on distance (closer = higher confidence)
            confidence = max(0.1, 1.0 - (min_distance / 50.0))
            
            return LocationInfo(
                commune=closest_commune,
                city=closest_commune,
                confidence=confidence,
                method="local_database",
                raw_data={
                    "distance_km": round(min_distance, 2),
                    "pharmacy_count": self.commune_centers[closest_commune]['pharmacy_count']
                }
            )
        
        return LocationInfo(method="local_no_match")
    
    def _reverse_geocode_nominatim(self, lat: float, lng: float) -> LocationInfo:
        """Use OpenStreetMap Nominatim API for reverse geocoding"""
        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                'lat': lat,
                'lon': lng,
                'format': 'json',
                'accept-language': 'es,en',
                'zoom': 10,  # City level
                'addressdetails': 1
            }
            
            headers = {
                'User-Agent': 'PharmacyFinderChile/1.0 (pharmacy-finder-chile@example.com)'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            if 'error' in data:
                return LocationInfo(method="nominatim_error")
            
            address = data.get('address', {})
            
            # Try to extract Chilean administrative divisions
            commune = (
                address.get('municipality') or 
                address.get('city') or 
                address.get('town') or 
                address.get('village') or
                address.get('suburb')
            )
            
            city = address.get('city') or commune
            region = (
                address.get('state') or 
                address.get('region') or 
                address.get('province')
            )
            country = address.get('country')
            
            # Higher confidence if it's in Chile
            confidence = 0.8 if country and 'chile' in country.lower() else 0.6
            
            return LocationInfo(
                commune=commune.upper() if commune else None,
                city=city.title() if city else None,
                region=region.title() if region else None,
                country=country,
                confidence=confidence,
                method="nominatim_api",
                raw_data=data
            )
            
        except Exception as e:
            logger.warning(f"⚠️ Nominatim API error: {e}")
            return LocationInfo(method="nominatim_error")
    
    def reverse_geocode(self, lat: float, lng: float) -> LocationInfo:
        """
        Main reverse geocoding method - tries local DB first, then external API
        
        Args:
            lat: Latitude
            lng: Longitude
            
        Returns:
            LocationInfo with detected location data
        """
        logger.info(f"🗺️ Reverse geocoding coordinates: {lat}, {lng}")
        
        # Method 1: Try local database first (fastest)
        local_result = self._reverse_geocode_local(lat, lng)
        
        if local_result.commune and local_result.confidence > 0.5:
            logger.info(f"✅ Local geocoding successful: {local_result.commune} (confidence: {local_result.confidence:.2f})")
            return local_result
        
        # Method 2: Try external API as fallback
        logger.info("⚡ Trying external API for better accuracy...")
        api_result = self._reverse_geocode_nominatim(lat, lng)
        
        if api_result.commune:
            # If we have both results, prefer the one with higher confidence
            if local_result.commune and local_result.confidence > api_result.confidence:
                logger.info(f"✅ Using local result: {local_result.commune}")
                return local_result
            else:
                logger.info(f"✅ Using API result: {api_result.commune}")
                return api_result
        
        # Return best available result
        return local_result if local_result.commune else api_result
    
    def get_location_summary(self, location_info: LocationInfo) -> str:
        """Generate a user-friendly location summary"""
        if not location_info.commune and not location_info.city:
            return "ubicación no identificada"
        
        parts = []
        if location_info.commune:
            parts.append(location_info.commune.title())
        if location_info.region and location_info.region != location_info.commune:
            parts.append(location_info.region)
        
        if parts:
            confidence_text = ""
            if location_info.confidence < 0.7:
                confidence_text = " (aproximadamente)"
            
            return ", ".join(parts) + confidence_text
        
        return "ubicación aproximada"

# Global service instance
geocoding_service = ReverseGeocodingService()