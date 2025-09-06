#!/usr/bin/env python3
"""
Search Farmacias Tool for AI Agent
Searches for pharmacies using existing infrastructure
"""

import logging
from typing import Dict, Any, List, Optional
from app.agents.tools.base_tool import BaseTool
from app.database import PharmacyDatabase
from app.cache.redis_client import get_redis_client
from app.utils.location_utils import enhance_pharmacy_info

logger = logging.getLogger(__name__)

# Try to import the smart matcher
try:
    import sys
    import os
    # Add the project root to Python path to import our smart matcher
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    if project_root not in sys.path:
        sys.path.append(project_root)
    
    from app.core.enhanced_pharmacy_search import EnhancedPharmacyDatabase, SmartSearchResponse
    SMART_MATCHING_AVAILABLE = True
    logger.info("✅ Smart commune matching available")
except ImportError as e:
    SMART_MATCHING_AVAILABLE = False
    logger.warning(f"⚠️ Smart commune matching not available: {e}")

class SearchFarmaciasTool(BaseTool):
    """
    Tool for searching pharmacies by commune, duty status, and other criteria
    """
    
    def __init__(self):
        super().__init__(
            name="search_farmacias",
            description="Busca farmacias por comuna, estado de turno y otros criterios. Utiliza la base de datos actualizada de farmacias en Chile con coincidencia inteligente para nombres de comunas."
        )
        # Use enhanced database if available, fallback to regular database
        if SMART_MATCHING_AVAILABLE:
            try:
                self.db = EnhancedPharmacyDatabase()
                self.use_smart_matching = True
                logger.info("🧠 Using enhanced database with smart commune matching")
            except Exception as e:
                logger.warning(f"Failed to initialize enhanced database: {e}")
                self.db = PharmacyDatabase()
                self.use_smart_matching = False
        else:
            self.db = PharmacyDatabase()
            self.use_smart_matching = False
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute pharmacy search
        
        Args:
            comuna (str): Nombre de la comuna para buscar farmacias
            turno (bool, optional): Si buscar SOLO farmacias de turno/emergencia (True) o farmacias regulares disponibles (False)
            limite (int, optional): Número máximo de resultados (default: 10)
            incluir_cerradas (bool, optional): Si incluir farmacias cerradas (default: False)
            
        Returns:
            Dictionary with search results
        """
        comuna = kwargs.get("comuna", "").strip()
        turno = kwargs.get("turno", False)
        limite = kwargs.get("limite", 10)
        incluir_cerradas = kwargs.get("incluir_cerradas", True)  # Default to including all pharmacies
        
        # Validate inputs
        if not comuna:
            return {
                "error": "Se requiere especificar una comuna para la búsqueda",
                "farmacias": [],
                "total": 0
            }
        
        try:
            # Use smart matching if available
            if self.use_smart_matching and hasattr(self.db, 'smart_find_by_comuna'):
                # Use enhanced search with smart commune matching
                farmacias_filtradas, match_result = self.db.smart_find_by_comuna(
                    comuna, 
                    only_open=turno,
                    confidence_threshold=0.7
                )
                
                # Create smart response
                search_response = SmartSearchResponse(
                    farmacias_filtradas, 
                    match_result, 
                    comuna, 
                    "turno" if turno else "all"
                )
                
                # If no match found or low confidence, return suggestions
                if not farmacias_filtradas and match_result.suggestions:
                    return {
                        "success": False,
                        "error": f"No se encontraron farmacias en '{comuna}'",
                        "farmacias": [],
                        "total": 0,
                        "suggestions": {
                            "message": "¿Quisiste decir alguna de estas comunas?",
                            "alternatives": match_result.suggestions[:5],
                            "original_query": comuna,
                            "confidence": match_result.confidence,
                            "method": match_result.method
                        }
                    }
                
                # Log successful smart match
                if match_result.matched_commune and match_result.matched_commune != comuna:
                    logger.info(f"🧠 Smart match: '{comuna}' -> '{match_result.matched_commune}' "
                              f"(confidence: {match_result.confidence:.3f}, method: {match_result.method})")
            
            else:
                # Fallback to regular search
                if turno:
                    farmacias_filtradas = self.db.find_by_comuna(comuna, only_open=True)
                else:
                    farmacias_filtradas = self.db.find_by_comuna(comuna, only_open=False)
            
            # Apply additional filters based on search type
            if turno:
                # For turno search, turno pharmacies are considered always available
                # but still apply closed filter if explicitly requested
                if not incluir_cerradas:
                    farmacias_filtradas = [
                        farmacia for farmacia in farmacias_filtradas
                        if farmacia.es_turno or self.db.is_pharmacy_currently_open(farmacia)
                    ]
            else:
                # For regular pharmacy search, include all pharmacies but mark their open status
                if not incluir_cerradas:
                    farmacias_filtradas = [
                        farmacia for farmacia in farmacias_filtradas
                        if self.db.is_pharmacy_currently_open(farmacia)
                    ]
            
            # Apply limit
            farmacias_resultado = farmacias_filtradas[:limite] if limite > 0 else farmacias_filtradas
            
            # Format results for agent with enhanced location features
            farmacias_formateadas = []
            for farmacia in farmacias_resultado:
                # Use enhanced formatting with location features
                farmacia_info = enhance_pharmacy_info(farmacia, self.db)
                farmacias_formateadas.append(farmacia_info)
            
            # Generate summary with helpful messaging
            total_encontradas = len(farmacias_filtradas)
            mostradas = len(farmacias_formateadas)
            
            # Check if searching for turno but found none
            turno_info = {}
            if turno and total_encontradas == 0:
                # Check if there are any regular open pharmacies
                try:
                    if self.use_smart_matching and hasattr(self.db, 'smart_find_by_comuna'):
                        farmacias_regulares, _ = self.db.smart_find_by_comuna(
                            comuna, 
                            only_open=False,
                            confidence_threshold=0.7
                        )
                    else:
                        farmacias_regulares = self.db.find_by_comuna(comuna, only_open=False)
                    
                    # Filter to only open regular pharmacies
                    farmacias_regulares_abiertas = [
                        f for f in farmacias_regulares 
                        if self.db.is_pharmacy_currently_open(f) and not f.es_turno
                    ]
                    
                    # Count total regular pharmacies (regardless of current time)
                    total_regulares = len([f for f in farmacias_regulares if not f.es_turno])
                    
                    turno_info = {
                        "no_turno_found": True,
                        "total_regular_pharmacies": total_regulares,
                        "regular_pharmacies_open_now": len(farmacias_regulares_abiertas),
                        "suggestion": f"No hay farmacias de turno, pero hay {total_regulares} farmacias regulares disponibles" if total_regulares > 0 else "No hay farmacias de turno ni regulares disponibles"
                    }
                except Exception as e:
                    logger.warning(f"Error checking regular pharmacies: {e}")
                    turno_info = {"no_turno_found": True}
            
            resumen = {
                "comuna_consultada": comuna,
                "solo_turno": turno,
                "total_encontradas": total_encontradas,
                "mostradas": mostradas,
                "incluye_cerradas": incluir_cerradas,
                **turno_info
            }
            
            # Generate contextual message
            if turno and total_encontradas == 0 and turno_info.get("total_regular_pharmacies", 0) > 0:
                mensaje = f"No se encontraron farmacias de turno en {comuna}, pero hay {turno_info['total_regular_pharmacies']} farmacias regulares disponibles."
            else:
                mensaje = f"Se encontraron {total_encontradas} farmacias en {comuna}" + \
                         (f" (solo de turno)" if turno else " (todas las farmacias)") + \
                         (f". Mostrando {mostradas} resultados." if total_encontradas > mostradas else ".")

            return {
                "farmacias": farmacias_formateadas,
                "resumen": resumen,
                "total": total_encontradas,
                "mensaje": mensaje
            }
            
        except Exception as e:
            logger.error(f"❌ Error searching pharmacies: {e}")
            return {
                "error": f"Error al buscar farmacias: {str(e)}",
                "farmacias": [],
                "total": 0
            }
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """
        Get JSON schema for search parameters
        """
        return {
            "type": "object",
            "properties": {
                "comuna": {
                    "type": "string",
                    "description": "Nombre de la comuna donde buscar farmacias (ej: 'Villa Alemana', 'Santiago', 'Valparaíso')"
                },
                "turno": {
                    "type": "boolean",
                    "description": "Si buscar SOLO farmacias de turno/emergencia (true) o TODAS las farmacias abiertas incluyendo regulares (false). Usar true solo para 'farmacias de turno', false para 'farmacias abiertas'",
                    "default": False
                },
                "limite": {
                    "type": "integer",
                    "description": "Número máximo de farmacias a retornar",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 10
                },
                "incluir_cerradas": {
                    "type": "boolean",
                    "description": "Si incluir farmacias que están cerradas en los resultados. Por defecto incluye todas las farmacias con información de horarios",
                    "default": True
                }
            },
            "required": ["comuna"]
        }


class SearchFarmaciasNearbyTool(BaseTool):
    """
    Tool for searching pharmacies by geographic coordinates (nearby search)
    """
    
    def __init__(self):
        super().__init__(
            name="search_farmacias_nearby",
            description="Busca farmacias cercanas a unas coordenadas geográficas específicas. Utiliza latitud y longitud para encontrar las farmacias más cercanas."
        )
        self.db = PharmacyDatabase()
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute nearby pharmacy search by coordinates
        
        Args:
            latitud (float): Latitud de la ubicación
            longitud (float): Longitud de la ubicación  
            radio_km (float, optional): Radio de búsqueda en kilómetros (default: 5.0)
            solo_abiertas (bool, optional): Solo farmacias abiertas (default: True)
            limite (int, optional): Número máximo de resultados (default: 10)
            
        Returns:
            Dictionary with search results
        """
        try:
            latitud = float(kwargs.get("latitud", 0))
            longitud = float(kwargs.get("longitud", 0))
            radio_km = float(kwargs.get("radio_km", 5.0))
            solo_abiertas = kwargs.get("solo_abiertas", True)
            limite = kwargs.get("limite", 10)
            
            # Validate coordinates
            if latitud == 0 or longitud == 0:
                return {
                    "success": False,
                    "error": "Se requieren coordenadas válidas (latitud y longitud)",
                    "data": {"farmacias": [], "total": 0}
                }
            
            # Search for nearby pharmacies
            if solo_abiertas:
                farmacias_cercanas = self.db.find_nearby_pharmacies_open_now(latitud, longitud, radio_km)
            else:
                farmacias_cercanas = self.db.find_nearby_pharmacies(latitud, longitud, radio_km, False)
            
            # Apply limit
            farmacias_resultado = farmacias_cercanas[:limite] if limite > 0 else farmacias_cercanas
            
            # Format results for agent with enhanced location features
            farmacias_formateadas = []
            for farmacia in farmacias_resultado:
                # Use enhanced formatting with location features
                farmacia_info = enhance_pharmacy_info(farmacia, self.db)
                farmacias_formateadas.append(farmacia_info)
            
            # Determine message based on results
            if farmacias_formateadas:
                tipo_busqueda = "abiertas" if solo_abiertas else "en el área"
                mensaje = f"Se encontraron {len(farmacias_formateadas)} farmacias {tipo_busqueda} en un radio de {radio_km}km."
            else:
                tipo_busqueda = "abiertas" if solo_abiertas else ""
                mensaje = f"No se encontraron farmacias {tipo_busqueda} en un radio de {radio_km}km de tu ubicación."
            
            return {
                "success": True,
                "data": {
                    "farmacias": farmacias_formateadas,
                    "resumen": {
                        "latitud": latitud,
                        "longitud": longitud,
                        "radio_km": radio_km,
                        "solo_abiertas": solo_abiertas,
                        "total_encontradas": len(farmacias_formateadas),
                        "mostradas": len(farmacias_formateadas)
                    },
                    "total": len(farmacias_formateadas),
                    "mensaje": mensaje
                },
                "tool": "search_farmacias_nearby"
            }
            
        except Exception as e:
            logger.error(f"Error in SearchFarmaciasNearbyTool: {e}")
            return {
                "success": False,
                "error": f"Error en la búsqueda por coordenadas: {str(e)}",
                "data": {"farmacias": [], "total": 0}
            }
    
    def get_openai_function_definition(self) -> Dict[str, Any]:
        """Return OpenAI function definition for this tool"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "latitud": {
                            "type": "number",
                            "description": "Latitud de la ubicación para buscar farmacias cercanas"
                        },
                        "longitud": {
                            "type": "number", 
                            "description": "Longitud de la ubicación para buscar farmacias cercanas"
                        },
                        "radio_km": {
                            "type": "number",
                            "description": "Radio de búsqueda en kilómetros (default: 5.0)",
                            "default": 5.0
                        },
                        "solo_abiertas": {
                            "type": "boolean",
                            "description": "Si buscar solo farmacias abiertas/de turno (default: true)",
                            "default": True
                        },
                        "limite": {
                            "type": "integer",
                            "description": "Número máximo de resultados a retornar (default: 10)",
                            "default": 10
                        }
                    },
                    "required": ["latitud", "longitud"]
                }
            }
        }
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Get JSON schema for tool parameters"""
        return {
            "type": "object",
            "properties": {
                "latitud": {
                    "type": "number",
                    "description": "Latitud de la ubicación para buscar farmacias cercanas"
                },
                "longitud": {
                    "type": "number", 
                    "description": "Longitud de la ubicación para buscar farmacias cercanas"
                },
                "radio_km": {
                    "type": "number",
                    "description": "Radio de búsqueda en kilómetros (default: 5.0)",
                    "default": 5.0
                },
                "solo_abiertas": {
                    "type": "boolean",
                    "description": "Si buscar solo farmacias abiertas/de turno (default: true)",
                    "default": True
                },
                "limite": {
                    "type": "integer",
                    "description": "Número máximo de resultados a retornar (default: 10)",
                    "default": 10
                }
            },
            "required": ["latitud", "longitud"]
        }


class GetCommunesTool(BaseTool):
    """
    Tool for getting available communes with pharmacies
    """
    
    def __init__(self):
        super().__init__(
            name="get_communes",
            description="Obtiene la lista de comunas disponibles que tienen farmacias registradas en el sistema."
        )
        self.db = PharmacyDatabase()
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Get list of available communes
        
        Args:
            region (str, optional): Filtrar por región específica
            
        Returns:
            Dictionary with commune list
        """
        region_filter = kwargs.get("region", "").strip()
        
        try:
            # Get all communes from the database
            comunas_disponibles = self.db.get_all_communes()
            
            if region_filter:
                # Basic region filtering (would be improved with proper data)
                if region_filter.lower() in ["valparaiso", "valparaíso", "v region", "v región"]:
                    # Filter for Valparaíso region communes
                    comunas_valparaiso = [
                        "Villa Alemana", "Valparaíso", "Viña del Mar",
                        "Quilpué", "Concón", "Casablanca", "Limache", "Olmué"
                    ]
                    comunas_disponibles = [
                        comuna for comuna in comunas_disponibles 
                        if comuna in comunas_valparaiso
                    ]
                elif region_filter.lower() in ["santiago", "metropolitana", "rm"]:
                    # Filter for Santiago region communes  
                    comunas_santiago = [
                        "Santiago", "Las Condes", "Providencia", "Ñuñoa",
                        "La Florida", "Maipú", "Puente Alto", "San Bernardo", "La Pintana"
                    ]
                    comunas_disponibles = [
                        comuna for comuna in comunas_disponibles 
                        if comuna in comunas_santiago
                    ]
            
            return {
                "comunas": sorted(comunas_disponibles),
                "total": len(comunas_disponibles),
                "region": region_filter if region_filter else "Todas las regiones",
                "mensaje": f"Se encontraron {len(comunas_disponibles)} comunas disponibles" + 
                          (f" en {region_filter}" if region_filter else "")
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting communes: {e}")
            return {
                "error": f"Error al obtener comunas: {str(e)}",
                "comunas": [],
                "total": 0
            }
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """
        Get JSON schema for commune parameters
        """
        return {
            "type": "object",
            "properties": {
                "region": {
                    "type": "string",
                    "description": "Nombre de la región para filtrar comunas (opcional)",
                    "examples": ["Valparaíso", "Santiago", "Metropolitana"]
                }
            },
            "required": []
        }
