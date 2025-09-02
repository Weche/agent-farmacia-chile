"""
Google Maps MCP Tools for enhanced location services
Provides geocoding, reverse geocoding, and address validation
"""

import os
import requests
import json
from typing import Dict, List, Optional, Tuple
from .base_tool import BaseTool

class GoogleMapsGeocodingTool(BaseTool):
    """Tool for geocoding addresses using Google Maps API"""
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        self.base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        
    def get_tool_config(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": "geocode_address",
                "description": "Convert an address to geographic coordinates using Google Maps API",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "address": {
                            "type": "string",
                            "description": "The address to geocode (e.g., 'Providencia 123, Santiago, Chile')"
                        },
                        "region": {
                            "type": "string",
                            "description": "Region bias for better results (e.g., 'cl' for Chile)",
                            "default": "cl"
                        }
                    },
                    "required": ["address"]
                }
            }
        }
    
    def execute(self, address: str, region: str = "cl") -> Dict:
        """
        Geocode an address to get coordinates
        
        Args:
            address: The address to geocode
            region: Region bias for results
            
        Returns:
            Dict with coordinates and formatted address
        """
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "Google Maps API key not configured",
                    "data": None
                }
            
            params = {
                "address": address,
                "region": region,
                "key": self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data["status"] == "OK" and data["results"]:
                result = data["results"][0]
                location = result["geometry"]["location"]
                
                return {
                    "success": True,
                    "data": {
                        "coordinates": {
                            "latitud": location["lat"],
                            "longitud": location["lng"]
                        },
                        "formatted_address": result["formatted_address"],
                        "address_components": result.get("address_components", []),
                        "place_id": result.get("place_id"),
                        "types": result.get("types", [])
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"Geocoding failed: {data.get('status', 'Unknown error')}",
                    "data": None
                }
                
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"Request error: {str(e)}",
                "data": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "data": None
            }


class GoogleMapsReverseGeocodingTool(BaseTool):
    """Tool for reverse geocoding coordinates using Google Maps API"""
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        self.base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        
    def get_tool_config(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": "reverse_geocode",
                "description": "Convert geographic coordinates to a readable address using Google Maps API",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "latitude": {
                            "type": "number",
                            "description": "Latitude coordinate"
                        },
                        "longitude": {
                            "type": "number", 
                            "description": "Longitude coordinate"
                        }
                    },
                    "required": ["latitude", "longitude"]
                }
            }
        }
    
    def execute(self, latitude: float, longitude: float) -> Dict:
        """
        Reverse geocode coordinates to get address
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Dict with address information
        """
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "Google Maps API key not configured",
                    "data": None
                }
            
            params = {
                "latlng": f"{latitude},{longitude}",
                "key": self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data["status"] == "OK" and data["results"]:
                result = data["results"][0]
                
                # Extract useful address components
                address_components = {}
                for component in result.get("address_components", []):
                    for component_type in component["types"]:
                        address_components[component_type] = component["long_name"]
                
                return {
                    "success": True,
                    "data": {
                        "formatted_address": result["formatted_address"],
                        "street_number": address_components.get("street_number", ""),
                        "route": address_components.get("route", ""),
                        "neighborhood": address_components.get("neighborhood", ""),
                        "locality": address_components.get("locality", ""),
                        "administrative_area_level_2": address_components.get("administrative_area_level_2", ""),
                        "administrative_area_level_1": address_components.get("administrative_area_level_1", ""),
                        "country": address_components.get("country", ""),
                        "postal_code": address_components.get("postal_code", ""),
                        "place_id": result.get("place_id"),
                        "types": result.get("types", [])
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"Reverse geocoding failed: {data.get('status', 'Unknown error')}",
                    "data": None
                }
                
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"Request error: {str(e)}",
                "data": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "data": None
            }


class GoogleMapsPlacesNearbyTool(BaseTool):
    """Tool for finding nearby places using Google Maps Places API"""
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        self.base_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        
    def get_tool_config(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": "find_nearby_places",
                "description": "Find nearby places like pharmacies, hospitals, or landmarks using Google Maps Places API",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "latitude": {
                            "type": "number",
                            "description": "Latitude coordinate"
                        },
                        "longitude": {
                            "type": "number",
                            "description": "Longitude coordinate"
                        },
                        "place_type": {
                            "type": "string",
                            "description": "Type of place to search for (e.g., 'pharmacy', 'hospital', 'store')",
                            "default": "pharmacy"
                        },
                        "radius": {
                            "type": "integer",
                            "description": "Search radius in meters (max 50000)",
                            "default": 5000
                        },
                        "keyword": {
                            "type": "string",
                            "description": "Keyword to filter results (e.g., 'farmacia', 'cruz verde')",
                            "default": ""
                        }
                    },
                    "required": ["latitude", "longitude"]
                }
            }
        }
    
    def execute(self, latitude: float, longitude: float, place_type: str = "pharmacy", 
                radius: int = 5000, keyword: str = "") -> Dict:
        """
        Find nearby places
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            place_type: Type of place to search for
            radius: Search radius in meters
            keyword: Optional keyword filter
            
        Returns:
            Dict with nearby places
        """
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "Google Maps API key not configured",
                    "data": None
                }
            
            params = {
                "location": f"{latitude},{longitude}",
                "radius": min(radius, 50000),  # Google Maps API limit
                "type": place_type,
                "key": self.api_key
            }
            
            if keyword:
                params["keyword"] = keyword
            
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if data["status"] == "OK":
                places = []
                for place in data.get("results", []):
                    place_info = {
                        "name": place.get("name", ""),
                        "place_id": place.get("place_id", ""),
                        "rating": place.get("rating", 0),
                        "vicinity": place.get("vicinity", ""),
                        "coordinates": {
                            "latitud": place["geometry"]["location"]["lat"],
                            "longitud": place["geometry"]["location"]["lng"]
                        },
                        "types": place.get("types", []),
                        "price_level": place.get("price_level"),
                        "opening_hours": place.get("opening_hours", {}),
                        "photos": [photo.get("photo_reference") for photo in place.get("photos", [])]
                    }
                    places.append(place_info)
                
                return {
                    "success": True,
                    "data": {
                        "places": places,
                        "total_results": len(places)
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"Places search failed: {data.get('status', 'Unknown error')}",
                    "data": None
                }
                
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"Request error: {str(e)}",
                "data": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "data": None
            }


class GoogleMapsDistanceMatrixTool(BaseTool):
    """Tool for calculating distances and travel times using Google Maps Distance Matrix API"""
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        self.base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        
    def get_tool_config(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": "calculate_distance_time",
                "description": "Calculate distance and travel time between origin and destination(s) using Google Maps",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "origin_lat": {
                            "type": "number",
                            "description": "Origin latitude"
                        },
                        "origin_lng": {
                            "type": "number",
                            "description": "Origin longitude"
                        },
                        "destinations": {
                            "type": "array",
                            "description": "List of destination coordinates",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "lat": {"type": "number"},
                                    "lng": {"type": "number"}
                                }
                            }
                        },
                        "mode": {
                            "type": "string",
                            "description": "Travel mode: driving, walking, transit, bicycling",
                            "default": "driving"
                        }
                    },
                    "required": ["origin_lat", "origin_lng", "destinations"]
                }
            }
        }
    
    def execute(self, origin_lat: float, origin_lng: float, destinations: List[Dict], 
                mode: str = "driving") -> Dict:
        """
        Calculate distances and travel times
        
        Args:
            origin_lat: Origin latitude
            origin_lng: Origin longitude  
            destinations: List of destination coordinates
            mode: Travel mode
            
        Returns:
            Dict with distance and time information
        """
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "Google Maps API key not configured",
                    "data": None
                }
            
            # Format destinations
            dest_coords = [f"{dest['lat']},{dest['lng']}" for dest in destinations]
            
            params = {
                "origins": f"{origin_lat},{origin_lng}",
                "destinations": "|".join(dest_coords),
                "mode": mode,
                "units": "metric",
                "key": self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if data["status"] == "OK":
                results = []
                elements = data["rows"][0]["elements"]
                
                for i, element in enumerate(elements):
                    if element["status"] == "OK":
                        distance = element.get("distance", {})
                        duration = element.get("duration", {})
                        
                        result = {
                            "destination_index": i,
                            "destination_coords": destinations[i],
                            "distance": {
                                "text": distance.get("text", ""),
                                "value": distance.get("value", 0)  # in meters
                            },
                            "duration": {
                                "text": duration.get("text", ""),
                                "value": duration.get("value", 0)  # in seconds
                            },
                            "status": "OK"
                        }
                    else:
                        result = {
                            "destination_index": i,
                            "destination_coords": destinations[i],
                            "status": element["status"],
                            "error": f"Could not calculate route to destination {i}"
                        }
                    
                    results.append(result)
                
                return {
                    "success": True,
                    "data": {
                        "origin": {"lat": origin_lat, "lng": origin_lng},
                        "results": results,
                        "mode": mode
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"Distance matrix failed: {data.get('status', 'Unknown error')}",
                    "data": None
                }
                
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"Request error: {str(e)}",
                "data": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "data": None
            }
