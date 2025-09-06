"""
Enhanced Database Search with LLM-Enhanced Smart Commune Matching
Integrates the LLM-enhanced matcher into the existing database search system
"""
from app.database import PharmacyDatabase
from app.core.llm_enhanced_commune_matcher import LLMEnhancedCommuneMatcher, MatchResult
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class EnhancedPharmacyDatabase(PharmacyDatabase):
    """Enhanced pharmacy database with LLM-enhanced smart commune matching"""
    
    def __init__(self, db_path: str = "pharmacy_finder.db"):
        super().__init__(db_path)
        self.smart_matcher = None
        self._initialize_smart_matcher()
    
    def _initialize_smart_matcher(self):
        """Initialize the LLM-enhanced smart commune matcher"""
        try:
            self.smart_matcher = LLMEnhancedCommuneMatcher()
            logger.info("✅ LLM-enhanced smart commune matcher initialized")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize LLM-enhanced matcher: {e}")
            self.smart_matcher = None
    
    def smart_find_by_comuna(self, comuna_query: str, only_open: bool = False, 
                           confidence_threshold: float = 0.7) -> Tuple[List, MatchResult]:
        """
        Find pharmacies with smart commune matching
        
        Args:
            comuna_query: User's commune query (with typos, accents, etc.)
            only_open: Filter for turno pharmacies only
            confidence_threshold: Minimum confidence for auto-matching
            
        Returns:
            Tuple of (pharmacies_list, match_result)
        """
        if not self.smart_matcher:
            # Fallback to original method
            logger.warning("Smart matcher not available, using fallback")
            pharmacies = self.find_by_comuna(comuna_query, only_open)
            # Create a basic match result
            match_result = MatchResult(
                original_query=comuna_query,
                matched_commune=comuna_query if pharmacies else "",
                confidence=1.0 if pharmacies else 0.0,
                method="fallback",
                suggestions=[],
                normalized_query=comuna_query.lower()
            )
            return pharmacies, match_result
        
        # Use LLM-enhanced smart matching
        match_result = self.smart_matcher.smart_match(comuna_query)
        
        if match_result.confidence >= confidence_threshold and match_result.matched_commune:
            # High confidence match - proceed with search
            pharmacies = self.find_by_comuna(match_result.matched_commune, only_open)
            logger.info(f"LLM-enhanced match: '{comuna_query}' -> '{match_result.matched_commune}' "
                       f"(confidence: {match_result.confidence:.3f}, method: {match_result.method})")
            return pharmacies, match_result
        
        elif match_result.suggestions:
            # Low confidence but has suggestions - return empty list with suggestions
            logger.info(f"Low confidence match for '{comuna_query}'. Suggestions: {match_result.suggestions}")
            return [], match_result
        
        else:
            # No match found
            logger.info(f"No match found for '{comuna_query}'")
            return [], match_result
    
    def get_commune_suggestions(self, query: str, max_suggestions: int = 5) -> List[Dict]:
        """Get commune suggestions with additional context"""
        if not self.smart_matcher:
            return []
        
        match_result = self.smart_matcher.smart_match(query)
        suggestions = []
        
        # Include the matched commune if confidence is reasonable
        if match_result.matched_commune and match_result.confidence >= 0.5:
            # Simple suggestion without detailed info (for now)
            suggestions.append({
                'name': match_result.matched_commune,
                'confidence': match_result.confidence,
                'method': match_result.method,
                'pharmacies_count': 0,  # TODO: Get from database
                'turno_count': 0,  # TODO: Get from database
                'region': 'Unknown'  # TODO: Get from database
            })
        
        # Add other suggestions
        for suggestion in match_result.suggestions[:max_suggestions-1]:
            if suggestion != match_result.matched_commune:  # Avoid duplicates
                suggestions.append({
                    'name': suggestion,
                    'confidence': 0.0,  # These are just suggestions
                    'method': 'suggestion',
                    'pharmacies_count': 0,  # TODO: Get from database
                    'turno_count': 0,  # TODO: Get from database
                    'region': 'Unknown'  # TODO: Get from database
                })
        
        return suggestions[:max_suggestions]

class SmartSearchResponse:
    """Response object for smart search results"""
    
    def __init__(self, pharmacies: List, match_result: MatchResult, 
                 original_query: str, search_type: str = "turno"):
        self.pharmacies = pharmacies
        self.match_result = match_result
        self.original_query = original_query
        self.search_type = search_type
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        # Convert pharmacies to dict format
        pharmacies_data = []
        for pharmacy in self.pharmacies:
            pharmacy_dict = {
                "id": pharmacy.local_id,
                "nombre": pharmacy.nombre,
                "direccion": pharmacy.direccion,
                "comuna": pharmacy.comuna,
                "region": pharmacy.region,
                "telefono": pharmacy.telefono,
                "ubicacion": {
                    "latitud": pharmacy.lat,
                    "longitud": pharmacy.lng
                },
                "horarios": {
                    "apertura": pharmacy.hora_apertura,
                    "cierre": pharmacy.hora_cierre,
                    "dias": pharmacy.dia_funcionamiento
                },
                "turno": pharmacy.es_turno,
                "abierta": pharmacy.es_turno,  # For compatibility
                "fecha_actualizacion": pharmacy.fecha_actualizacion
            }
            pharmacies_data.append(pharmacy_dict)
        
        response = {
            "success": True,
            "search_info": {
                "original_query": self.original_query,
                "matched_commune": self.match_result.matched_commune,
                "confidence": self.match_result.confidence,
                "method": self.match_result.method,
                "normalized_query": self.match_result.normalized_query,
                "search_type": self.search_type
            },
            "results": {
                "total_found": len(pharmacies_data),
                "farmacias": pharmacies_data
            }
        }
        
        # Add suggestions if no results or low confidence
        if not pharmacies_data or self.match_result.confidence < 0.8:
            response["suggestions"] = {
                "message": "¿Quisiste decir alguna de estas comunas?",
                "alternatives": self.match_result.suggestions[:5]
            }
        
        # Add match explanation
        if self.match_result.method == "exact":
            response["search_info"]["explanation"] = "Coincidencia exacta encontrada"
        elif self.match_result.method in ["fuzzy_high", "embedding"]:
            response["search_info"]["explanation"] = f"Coincidencia inteligente (confianza: {self.match_result.confidence:.1%})"
        elif self.match_result.method == "trigram":
            response["search_info"]["explanation"] = "Coincidencia por similitud de texto"
        elif self.match_result.method == "fuzzy_low":
            response["search_info"]["explanation"] = "Coincidencia parcial - verifica las sugerencias"
        else:
            response["search_info"]["explanation"] = "No se encontró coincidencia"
        
        return response

def test_enhanced_search():
    """Test the enhanced database search"""
    print("🧪 Testing Enhanced Database Search")
    print("=" * 50)
    
    enhanced_db = EnhancedPharmacyDatabase()
    
    test_queries = [
        ("Quilpué", True),    # With accent, turno only
        ("quilpue", False),   # Without accent, all pharmacies
        ("kilpue", True),     # Typo, turno only
        ("santiago", True),   # Common city
        ("xyz123", True),     # Non-existent
    ]
    
    for query, only_turno in test_queries:
        print(f"\n📍 Testing: '{query}' (turno only: {only_turno})")
        
        pharmacies, match_result = enhanced_db.smart_find_by_comuna(query, only_turno)
        response = SmartSearchResponse(pharmacies, match_result, query, 
                                     "turno" if only_turno else "all")
        
        result_dict = response.to_dict()
        
        print(f"   Results: {result_dict['results']['total_found']} pharmacies found")
        print(f"   Match: {result_dict['search_info']['explanation']}")
        
        if 'suggestions' in result_dict:
            print(f"   Suggestions: {', '.join(result_dict['suggestions']['alternatives'][:3])}")

if __name__ == "__main__":
    test_enhanced_search()
