#!/usr/bin/env python3
"""
Smart Commune Matcher with Embeddings and LLM Validation
Handles fuzzy matching, typos, accents, and provides intelligent suggestions
"""
import json
import sqlite3
import unicodedata
import re
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass
from difflib import SequenceMatcher
import numpy as np

# Try to import sentence-transformers for embeddings
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("⚠️ sentence-transformers not available. Install with: pip install sentence-transformers")

@dataclass
class MatchResult:
    """Result of commune matching"""
    original_query: str
    matched_commune: str
    confidence: float
    method: str  # 'exact', 'fuzzy', 'embedding', 'llm'
    suggestions: List[str]
    normalized_query: str

class SmartCommuneMatcher:
    """Smart fuzzy matcher for commune names with multiple strategies"""
    
    def __init__(self, analysis_file: str = "commune_analysis.json"):
        self.analysis_file = analysis_file
        self.communes_data = {}
        self.similarity_index = {}
        self.embeddings_model = None
        self.commune_embeddings = {}
        
        self.load_analysis()
        if EMBEDDINGS_AVAILABLE:
            self.initialize_embeddings()
    
    def load_analysis(self):
        """Load the commune analysis data"""
        try:
            with open(self.analysis_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.communes_data = data['communes_data']
            self.similarity_index = data['similarity_index']
            print(f"✅ Loaded data for {len(self.communes_data)} communes")
            
        except FileNotFoundError:
            print(f"❌ Analysis file {self.analysis_file} not found. Run commune_analyzer.py first.")
            raise
    
    def initialize_embeddings(self):
        """Initialize sentence transformer model and compute embeddings"""
        try:
            print("🧠 Initializing embeddings model...")
            # Use a multilingual model that works well with Spanish
            self.embeddings_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            
            # Compute embeddings for all commune variations
            all_variations = []
            variation_to_commune = {}
            
            for commune, data in self.communes_data.items():
                for variation in data['variations']:
                    all_variations.append(variation)
                    variation_to_commune[variation] = commune
            
            print(f"🔄 Computing embeddings for {len(all_variations)} variations...")
            embeddings = self.embeddings_model.encode(all_variations)
            
            # Store embeddings by commune
            for i, variation in enumerate(all_variations):
                commune = variation_to_commune[variation]
                if commune not in self.commune_embeddings:
                    self.commune_embeddings[commune] = []
                self.commune_embeddings[commune].append({
                    'variation': variation,
                    'embedding': embeddings[i]
                })
            
            print(f"✅ Embeddings ready for {len(self.commune_embeddings)} communes")
            
        except Exception as e:
            print(f"⚠️ Could not initialize embeddings: {e}")
            self.embeddings_model = None
    
    def normalize_text(self, text: str) -> str:
        """Normalize text by removing accents and converting to lowercase"""
        if not text:
            return ""
        # Remove accents
        nfd = unicodedata.normalize('NFD', text)
        without_accents = ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')
        # Convert to lowercase and clean
        return re.sub(r'[^\w\s]', '', without_accents.lower().strip())
    
    def exact_match(self, query: str) -> Optional[str]:
        """Try exact matching with variations"""
        normalized_query = self.normalize_text(query)
        
        # Try exact matches
        for commune, data in self.communes_data.items():
            if query in data['variations']:
                return commune
            if normalized_query in [self.normalize_text(v) for v in data['variations']]:
                return commune
        
        return None
    
    def fuzzy_match(self, query: str, min_similarity: float = 0.6) -> List[Tuple[str, float]]:
        """Fuzzy matching using string similarity"""
        normalized_query = self.normalize_text(query)
        matches = []
        
        for commune, data in self.communes_data.items():
            max_similarity = 0
            
            # Check similarity with all variations
            for variation in data['variations']:
                normalized_variation = self.normalize_text(variation)
                
                # Use SequenceMatcher for similarity
                similarity = SequenceMatcher(None, normalized_query, normalized_variation).ratio()
                max_similarity = max(max_similarity, similarity)
                
                # Also try substring matching
                if normalized_query in normalized_variation or normalized_variation in normalized_query:
                    substring_bonus = 0.2
                    max_similarity = max(max_similarity, similarity + substring_bonus)
            
            if max_similarity >= min_similarity:
                matches.append((commune, max_similarity))
        
        # Sort by similarity descending
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
    
    def trigram_match(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Fast trigram-based similarity matching"""
        normalized_query = self.normalize_text(query)
        query_trigrams = set()
        
        # Generate trigrams for query
        text = f"  {normalized_query}  "
        for i in range(len(text) - 2):
            query_trigrams.add(text[i:i+3])
        
        # Count matches for each commune
        commune_scores = {}
        
        for trigram in query_trigrams:
            if trigram in self.similarity_index['trigram_index']:
                for commune in self.similarity_index['trigram_index'][trigram]:
                    commune_scores[commune] = commune_scores.get(commune, 0) + 1
        
        # Calculate Jaccard similarity
        matches = []
        for commune, matches_count in commune_scores.items():
            # Get all trigrams for this commune
            commune_trigrams = set()
            for variation in self.communes_data[commune]['variations']:
                normalized_var = self.normalize_text(variation)
                var_text = f"  {normalized_var}  "
                for i in range(len(var_text) - 2):
                    commune_trigrams.add(var_text[i:i+3])
            
            # Jaccard similarity
            intersection = len(query_trigrams & commune_trigrams)
            union = len(query_trigrams | commune_trigrams)
            jaccard = intersection / union if union > 0 else 0
            
            if jaccard > 0:
                matches.append((commune, jaccard))
        
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:top_k]
    
    def embedding_match(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Semantic matching using embeddings"""
        if not self.embeddings_model:
            return []
        
        try:
            # Encode the query
            query_embedding = self.embeddings_model.encode([query])[0]
            
            matches = []
            for commune, embeddings_data in self.commune_embeddings.items():
                max_similarity = 0
                
                for embed_data in embeddings_data:
                    # Cosine similarity
                    similarity = np.dot(query_embedding, embed_data['embedding']) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(embed_data['embedding'])
                    )
                    max_similarity = max(max_similarity, similarity)
                
                matches.append((commune, float(max_similarity)))
            
            matches.sort(key=lambda x: x[1], reverse=True)
            return matches[:top_k]
            
        except Exception as e:
            print(f"⚠️ Embedding match failed: {e}")
            return []
    
    def extract_commune_from_query(self, query: str) -> List[str]:
        """Extract potential commune names from contextual queries"""
        import re
        
        query_lower = query.lower()
        
        # Common patterns that indicate location context
        location_patterns = [
            r'farmacias?\s+en\s+(.+?)(?:\s|$)',
            r'(?:de\s+)?turno\s+en\s+(.+?)(?:\s|$)',
            r'(?:en|de)\s+(.+?)(?:\s|$)',
            r'cerca\s+(?:de|a)\s+(.+?)(?:\s|$)',
            r'(.+?)\s+(?:farmacias?|turno|comuna)',
        ]
        
        extracted_terms = []
        
        # Try each pattern
        for pattern in location_patterns:
            matches = re.findall(pattern, query_lower, re.IGNORECASE)
            for match in matches:
                # Clean the extracted term
                cleaned = match.strip()
                
                # Smart filtering: keep "la" and "el" if they're part of official commune names
                # Check if the term matches known commune patterns
                cleaned_title = cleaned.title()  # Capitalize first letter of each word
                
                # Add both the cleaned version and the title case version
                if cleaned:
                    extracted_terms.append(cleaned)
                    extracted_terms.append(cleaned_title)
                    
                    # Also try without common prepositions (but keep la/el for commune names)
                    words = cleaned.split()
                    if len(words) > 1:
                        # Only remove truly unnecessary words, preserve "la" and "el" for communes
                        filtered_words = []
                        for i, word in enumerate(words):
                            # Keep "la" and "el" if they're at the beginning and followed by a capitalized word
                            if word in ['la', 'el'] and i == 0:
                                filtered_words.append(word)
                            elif word not in ['de', 'del', 'las', 'los', 'y', 'o', 'u', 'en', 'con', 'por', 'para']:
                                filtered_words.append(word)
                        
                        if filtered_words and len(filtered_words) != len(words):
                            filtered_text = ' '.join(filtered_words)
                            extracted_terms.append(filtered_text)
                            extracted_terms.append(filtered_text.title())
        
        # Also try the original query as is (without modification)
        extracted_terms.append(query.strip())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_terms = []
        for term in extracted_terms:
            if term not in seen and term:
                seen.add(term)
                unique_terms.append(term)
        
        return unique_terms

    def smart_match(self, query: str) -> MatchResult:
        """Smart matching combining all strategies with query preprocessing"""
        if not query or not query.strip():
            return MatchResult(
                original_query=query,
                matched_commune="",
                confidence=0.0,
                method="error",
                suggestions=[],
                normalized_query=""
            )
        
        query = query.strip()
        normalized_query = self.normalize_text(query)
        
        # Extract potential commune names from the query
        potential_communes = self.extract_commune_from_query(query)
        
        best_result = None
        best_confidence = 0.0
        
        # Try matching each extracted term
        for term in potential_communes:
            if not term:
                continue
                
            term_normalized = self.normalize_text(term)
            term_normalized = self.normalize_text(term)
            
            # Strategy 1: Exact match
            exact_match = self.exact_match(term)
            if exact_match:
                return MatchResult(
                    original_query=query,
                    matched_commune=exact_match,
                    confidence=1.0,
                    method="exact_extracted",
                    suggestions=[],
                    normalized_query=normalized_query
                )
            
            # Strategy 2: High-confidence fuzzy match
            fuzzy_matches = self.fuzzy_match(term, min_similarity=0.85)
            if fuzzy_matches and fuzzy_matches[0][1] >= 0.9:
                if fuzzy_matches[0][1] > best_confidence:
                    best_result = MatchResult(
                        original_query=query,
                        matched_commune=fuzzy_matches[0][0],
                        confidence=fuzzy_matches[0][1],
                        method="fuzzy_high_extracted",
                        suggestions=[m[0] for m in fuzzy_matches[1:3]],
                        normalized_query=normalized_query
                    )
                    best_confidence = fuzzy_matches[0][1]
            
            # Strategy 3: Embedding match (if available)
            embedding_matches = self.embedding_match(term)
            if embedding_matches and embedding_matches[0][1] >= 0.8:
                if embedding_matches[0][1] > best_confidence:
                    best_result = MatchResult(
                        original_query=query,
                        matched_commune=embedding_matches[0][0],
                        confidence=embedding_matches[0][1],
                        method="embedding_extracted",
                        suggestions=[m[0] for m in embedding_matches[1:3]],
                        normalized_query=normalized_query
                    )
                    best_confidence = embedding_matches[0][1]
            
            # Strategy 4: Trigram match
            trigram_matches = self.trigram_match(term)
            if trigram_matches and trigram_matches[0][1] >= 0.6:
                if trigram_matches[0][1] > best_confidence:
                    best_result = MatchResult(
                        original_query=query,
                        matched_commune=trigram_matches[0][0],
                        confidence=trigram_matches[0][1],
                        method="trigram_extracted",
                        suggestions=[m[0] for m in trigram_matches[1:4]],
                        normalized_query=normalized_query
                    )
                    best_confidence = trigram_matches[0][1]
        
        # Return best result if found
        if best_result:
            return best_result

        # Strategy 5: Low-confidence fuzzy match with suggestions (using original query)
        all_fuzzy = self.fuzzy_match(query, min_similarity=0.3)
        if all_fuzzy:
            suggestions = [m[0] for m in all_fuzzy[:5]]
            return MatchResult(
                original_query=query,
                matched_commune="",  # No confident match
                confidence=all_fuzzy[0][1],
                method="fuzzy_low",
                suggestions=suggestions,
                normalized_query=normalized_query
            )

        # No matches found
        return MatchResult(
            original_query=query,
            matched_commune="",
            confidence=0.0,
            method="no_match",
            suggestions=[],
            normalized_query=normalized_query
        )
    
    def get_commune_info(self, commune: str) -> Optional[Dict]:
        """Get detailed information about a commune"""
        if commune in self.communes_data:
            return self.communes_data[commune]
        return None
    
    def test_matching(self, test_cases: List[str]):
        """Test the matching system with various inputs"""
        print("\n🧪 Testing Smart Commune Matching")
        print("=" * 50)
        
        for test_query in test_cases:
            print(f"\n📍 Query: '{test_query}'")
            result = self.smart_match(test_query)
            
            print(f"   Match: '{result.matched_commune}' (confidence: {result.confidence:.3f})")
            print(f"   Method: {result.method}")
            
            if result.suggestions:
                print(f"   Suggestions: {', '.join(result.suggestions[:3])}")
            
            if result.matched_commune:
                info = self.get_commune_info(result.matched_commune)
                if info:
                    print(f"   📊 {info['statistics']['total_pharmacies']} pharmacies, "
                          f"{info['statistics']['turno_pharmacies']} turno")

def main():
    """Test the smart matching system"""
    matcher = SmartCommuneMatcher()
    
    # Test cases including typos, accents, and variations
    test_cases = [
        "Quilpué",        # Original with accent
        "Quilpue",        # Without accent
        "quilpue",        # Lowercase
        "QUILPUE",        # Uppercase
        "kilpue",         # Typo (k instead of qu)
        "quilpe",         # Typo (missing u)
        "quillpue",       # Double l
        "santiago",       # Common city
        "valparaiso",     # Missing accent
        "Valparaíso",     # With accent
        "viña del mar",   # Lowercase
        "Viña del Mar",   # Proper case
        "vina del mar",   # Without accent
        "la serena",      # Article included
        "Las Condes",     # Proper name
        "condes",         # Without article
        "maipo",          # Similar to Maipú
        "temco",          # Typo for Temuco
        "antfagasta",     # Typo for Antofagasta
        "xyz123"          # Non-existent
    ]
    
    matcher.test_matching(test_cases)

if __name__ == "__main__":
    main()
