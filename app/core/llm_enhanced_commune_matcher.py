#!/usr/bin/env python3
"""
LLM-Enhanced Smart Commune Matcher
Uses OpenAI LLM to extract location intent + embeddings for semantic matching
"""
import json
import sqlite3
import unicodedata
import re
import os
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass
from difflib import SequenceMatcher
import numpy as np

# Try to import dependencies
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("⚠️ sentence-transformers not available. Install with: pip install sentence-transformers")

try:
    import openai
    from openai import OpenAI
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("⚠️ openai not available. Install with: pip install openai")

@dataclass
class LocationIntent:
    """Result of LLM location extraction"""
    original_query: str
    extracted_location: str
    intent_type: str  # 'pharmacy_search', 'location_query', 'general'
    confidence: float
    reasoning: str

@dataclass
class MatchResult:
    """Result of commune matching"""
    original_query: str
    matched_commune: str
    confidence: float
    method: str  # 'exact', 'fuzzy', 'embedding', 'llm_enhanced'
    suggestions: List[str]
    normalized_query: str
    location_intent: Optional[LocationIntent] = None

class LLMEnhancedCommuneMatcher:
    """Smart commune matcher using LLM + embeddings"""
    
    def __init__(self, analysis_file: str = "commune_analysis.json"):
        self.analysis_file = analysis_file
        self.communes_data = {}
        self.similarity_index = {}
        self.embeddings_model = None
        self.commune_embeddings = {}
        
        # Initialize OpenAI client
        self.openai_client = None
        if LLM_AVAILABLE:
            try:
                from app.core.utils import get_env_value
                api_key = get_env_value("OPENAI_API_KEY")
                if api_key:
                    self.openai_client = OpenAI(api_key=api_key)
                else:
                    print("⚠️ OPENAI_API_KEY not found in environment")
            except Exception as e:
                print(f"⚠️ Error initializing OpenAI: {e}")
        
        self.load_analysis()
        if EMBEDDINGS_AVAILABLE:
            self.initialize_embeddings()
    
    def load_analysis(self):
        """Load the commune analysis data"""
        try:
            with open(self.analysis_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.communes_data = data.get('communes_data', {})
                print(f"✅ Loaded data for {len(self.communes_data)} communes")
        except FileNotFoundError:
            print(f"⚠️ Analysis file {self.analysis_file} not found, loading from database")
            self.load_from_database()
    
    def load_from_database(self):
        """Load commune data directly from database"""
        try:
            db_path = os.getenv('DATABASE_URL', 'pharmacy_finder.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Use correct table name 'pharmacies'
            cursor.execute("SELECT DISTINCT comuna FROM pharmacies WHERE comuna IS NOT NULL")
            communes = [row[0] for row in cursor.fetchall()]
            
            self.communes_data = {commune: {"normalized": self.normalize_text(commune)} 
                                for commune in communes}
            
            conn.close()
            print(f"✅ Loaded {len(self.communes_data)} communes from database ({db_path})")
        except Exception as e:
            print(f"❌ Error loading from database: {e}")
    
    def initialize_embeddings(self):
        """Initialize sentence transformer model and commune embeddings"""
        try:
            print("🔄 Initializing embeddings model...")
            self.embeddings_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            
            # Create embeddings for all communes
            communes_list = list(self.communes_data.keys())
            if communes_list:
                embeddings = self.embeddings_model.encode(communes_list)
                self.commune_embeddings = {
                    commune: embedding 
                    for commune, embedding in zip(communes_list, embeddings)
                }
                print(f"✅ Created embeddings for {len(self.commune_embeddings)} communes")
        except Exception as e:
            print(f"❌ Error initializing embeddings: {e}")
            self.embeddings_model = None
    
    def extract_location_with_llm(self, query: str) -> LocationIntent:
        """Use LLM to extract location intent from natural language query"""
        if not self.openai_client:
            return LocationIntent(
                original_query=query,
                extracted_location="",
                intent_type="general",
                confidence=0.0,
                reasoning="LLM not available"
            )
        
        # Get list of available communes for context
        communes_sample = list(self.communes_data.keys())[:20]  # First 20 for context
        
        prompt = f"""
Eres un asistente especializado en extraer ubicaciones geográficas de consultas sobre farmacias en Chile.

TAREA: Analiza la siguiente consulta y extrae la comuna/ciudad mencionada.

CONSULTA: "{query}"

COMUNAS DISPONIBLES (ejemplo): {', '.join(communes_sample)}...

INSTRUCCIONES:
1. Identifica si la consulta menciona una ubicación específica
2. Extrae SOLO el nombre de la comuna/ciudad
3. Normaliza el nombre (ej: "la florida" -> "La Florida")
4. Si no hay ubicación clara, devuelve vacío

RESPONDE EN FORMATO JSON:
{{
    "extracted_location": "nombre de la comuna extraída o vacío",
    "intent_type": "pharmacy_search|location_query|general",
    "confidence": 0.0-1.0,
    "reasoning": "breve explicación de tu decisión"
}}

EJEMPLOS:
- "farmacias en la florida" -> {{"extracted_location": "La Florida", "intent_type": "pharmacy_search", "confidence": 0.95}}
- "necesito medicamentos en las condes" -> {{"extracted_location": "Las Condes", "intent_type": "pharmacy_search", "confidence": 0.90}}
- "dónde hay farmacias" -> {{"extracted_location": "", "intent_type": "general", "confidence": 0.1}}
"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un experto en análisis de texto para extraer ubicaciones en consultas sobre farmacias en Chile."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                result_json = json.loads(result_text)
                return LocationIntent(
                    original_query=query,
                    extracted_location=result_json.get("extracted_location", ""),
                    intent_type=result_json.get("intent_type", "general"),
                    confidence=result_json.get("confidence", 0.0),
                    reasoning=result_json.get("reasoning", "")
                )
            except json.JSONDecodeError:
                print(f"⚠️ LLM response not valid JSON: {result_text}")
                return LocationIntent(
                    original_query=query,
                    extracted_location="",
                    intent_type="general",
                    confidence=0.0,
                    reasoning="Invalid JSON response from LLM"
                )
                
        except Exception as e:
            print(f"❌ Error calling LLM: {e}")
            return LocationIntent(
                original_query=query,
                extracted_location="",
                intent_type="general",
                confidence=0.0,
                reasoning=f"LLM error: {str(e)}"
            )
    
    def semantic_match_with_embeddings(self, location_query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Find similar communes using semantic embeddings"""
        if not self.embeddings_model or not self.commune_embeddings:
            return []
        
        try:
            # Get embedding for the query
            query_embedding = self.embeddings_model.encode([location_query])
            
            # Calculate similarities
            similarities = []
            for commune, commune_embedding in self.commune_embeddings.items():
                similarity = np.dot(query_embedding[0], commune_embedding) / (
                    np.linalg.norm(query_embedding[0]) * np.linalg.norm(commune_embedding)
                )
                similarities.append((commune, float(similarity)))
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            print(f"❌ Error in semantic matching: {e}")
            return []
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        if not text:
            return ""
        
        # Remove accents and convert to lowercase
        text = unicodedata.normalize('NFD', text)
        text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
        return text.lower().strip()
    
    def exact_match(self, location: str) -> Optional[str]:
        """Try exact matching with various normalizations"""
        if not location:
            return None
            
        location_norm = self.normalize_text(location)
        
        # Try exact matches
        for commune in self.communes_data.keys():
            commune_norm = self.normalize_text(commune)
            if location_norm == commune_norm:
                return commune
        
        return None
    
    def fuzzy_match(self, location: str, threshold: float = 0.8) -> List[Tuple[str, float]]:
        """Fuzzy string matching"""
        if not location:
            return []
            
        location_norm = self.normalize_text(location)
        matches = []
        
        for commune in self.communes_data.keys():
            commune_norm = self.normalize_text(commune)
            similarity = SequenceMatcher(None, location_norm, commune_norm).ratio()
            
            if similarity >= threshold:
                matches.append((commune, similarity))
        
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:5]
    
    def smart_match(self, query: str, confidence_threshold: float = 0.7) -> MatchResult:
        """Enhanced matching using LLM + embeddings + fuzzy matching"""
        
        # Step 1: Use LLM to extract location intent
        location_intent = self.extract_location_with_llm(query)
        extracted_location = location_intent.extracted_location
        
        print(f"🤖 LLM extracted: '{extracted_location}' (confidence: {location_intent.confidence:.2f})")
        
        # Step 2: If no location extracted, try fallback methods
        if not extracted_location or location_intent.confidence < 0.5:
            print("🔄 LLM confidence low, trying fallback methods...")
            # Fallback to regex-based extraction
            extracted_location = self._fallback_extraction(query)
        
        if not extracted_location:
            return MatchResult(
                original_query=query,
                matched_commune="",
                confidence=0.0,
                method="no_location",
                suggestions=list(self.communes_data.keys())[:5],
                normalized_query=self.normalize_text(query),
                location_intent=location_intent
            )
        
        # Step 3: Try exact match first
        exact_match = self.exact_match(extracted_location)
        if exact_match:
            return MatchResult(
                original_query=query,
                matched_commune=exact_match,
                confidence=1.0,
                method="llm_exact",
                suggestions=[],
                normalized_query=self.normalize_text(extracted_location),
                location_intent=location_intent
            )
        
        # Step 4: Try semantic matching with embeddings
        semantic_matches = []
        if self.embeddings_model:
            semantic_matches = self.semantic_match_with_embeddings(extracted_location)
            if semantic_matches and semantic_matches[0][1] >= 0.85:  # High similarity threshold
                return MatchResult(
                    original_query=query,
                    matched_commune=semantic_matches[0][0],
                    confidence=semantic_matches[0][1],
                    method="llm_semantic",
                    suggestions=[match[0] for match in semantic_matches[1:5]],
                    normalized_query=self.normalize_text(extracted_location),
                    location_intent=location_intent
                )
        
        # Step 5: Fuzzy matching as fallback
        fuzzy_matches = self.fuzzy_match(extracted_location)
        if fuzzy_matches and fuzzy_matches[0][1] >= confidence_threshold:
            return MatchResult(
                original_query=query,
                matched_commune=fuzzy_matches[0][0],
                confidence=fuzzy_matches[0][1],
                method="llm_fuzzy",
                suggestions=[match[0] for match in fuzzy_matches[1:5]],
                normalized_query=self.normalize_text(extracted_location),
                location_intent=location_intent
            )
        
        # Step 6: Return suggestions if no good match
        all_suggestions = []
        if semantic_matches:
            all_suggestions.extend([match[0] for match in semantic_matches[:3]])
        if fuzzy_matches:
            all_suggestions.extend([match[0] for match in fuzzy_matches[:3]])
        
        # Remove duplicates while preserving order
        seen = set()
        suggestions = []
        for item in all_suggestions:
            if item not in seen:
                seen.add(item)
                suggestions.append(item)
        
        return MatchResult(
            original_query=query,
            matched_commune="",
            confidence=max([match[1] for match in (semantic_matches + fuzzy_matches)] or [0.0]),
            method="llm_suggestions",
            suggestions=suggestions[:5],
            normalized_query=self.normalize_text(extracted_location),
            location_intent=location_intent
        )
    
    def _fallback_extraction(self, query: str) -> str:
        """Fallback location extraction using regex patterns"""
        query_lower = query.lower()
        
        # Common patterns for location extraction
        patterns = [
            r'(?:farmacias?\s+)?(?:en|de|cerca\s+de)\s+(.+?)(?:\s|$)',
            r'(?:buscar|encontrar|necesito)\s+farmacias?\s+(.+?)(?:\s|$)',
            r'farmacias?\s+(.+?)(?:\s|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                location = match.group(1).strip()
                # Remove common stop words but preserve location articles
                stop_words = ['en', 'de', 'del', 'para', 'por', 'con', 'sin', 'cerca']
                words = location.split()
                filtered_words = [w for w in words if w not in stop_words]
                if filtered_words:
                    return ' '.join(filtered_words).title()
        
        return ""

def test_llm_enhanced_matcher():
    """Test the LLM-enhanced commune matcher"""
    matcher = LLMEnhancedCommuneMatcher()
    
    test_queries = [
        "La Florida",
        "farmacias en la florida", 
        "buscar farmacias la florida",
        "necesito medicamentos en Las Condes",
        "dónde hay farmacias en Quilpué",
        "farmacia cerca de la reina",
        "quiero farmacias de la florida"
    ]
    
    print("🧪 TESTING LLM-ENHANCED COMMUNE MATCHER")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        result = matcher.smart_match(query)
        
        print(f"   ✓ Matched: '{result.matched_commune}'")
        print(f"   ✓ Confidence: {result.confidence:.2f}")
        print(f"   ✓ Method: {result.method}")
        if result.location_intent:
            print(f"   🤖 LLM extracted: '{result.location_intent.extracted_location}'")
            print(f"   🤖 LLM reasoning: {result.location_intent.reasoning}")
        if result.suggestions:
            print(f"   💡 Suggestions: {result.suggestions[:3]}")

if __name__ == "__main__":
    test_llm_enhanced_matcher()
