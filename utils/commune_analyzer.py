#!/usr/bin/env python3
"""
Comprehensive Database Analyzer for Commune Data
Analyzes commune variations, creates embeddings, and builds smart matching system
"""
import sqlite3
import json
import unicodedata
import re
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import pandas as pd

class CommuneAnalyzer:
    """Analyzes and processes commune data for smart matching"""
    
    def __init__(self, db_path: str = "pharmacy_finder.db"):
        self.db_path = db_path
        self.communes_data = {}
        self.analysis_results = {}
        
    def normalize_text(self, text: str) -> str:
        """Normalize text by removing accents and converting to lowercase"""
        if not text:
            return ""
        # Remove accents
        nfd = unicodedata.normalize('NFD', text)
        without_accents = ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')
        # Convert to lowercase and clean
        return re.sub(r'[^\w\s]', '', without_accents.lower().strip())
    
    def extract_commune_data(self) -> Dict:
        """Extract comprehensive commune data from database"""
        print("🔍 Extracting commune data from database...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all commune variations with statistics
        query = """
        SELECT 
            comuna,
            region,
            COUNT(*) as total_pharmacies,
            COUNT(CASE WHEN es_turno = 1 THEN 1 END) as turno_pharmacies,
            COUNT(CASE WHEN lat != 0 AND lng != 0 THEN 1 END) as with_coordinates,
            AVG(CASE WHEN lat != 0 THEN lat END) as avg_lat,
            AVG(CASE WHEN lng != 0 THEN lng END) as avg_lng
        FROM pharmacies 
        GROUP BY comuna, region
        ORDER BY total_pharmacies DESC
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        communes_data = {}
        for row in results:
            comuna, region, total, turno, coords, lat, lng = row
            
            # Create normalized version for matching
            normalized = self.normalize_text(comuna)
            
            communes_data[comuna] = {
                'original_name': comuna,
                'normalized_name': normalized,
                'region': region,
                'statistics': {
                    'total_pharmacies': total,
                    'turno_pharmacies': turno,
                    'with_coordinates': coords,
                    'coordinate_coverage': round((coords / total) * 100, 1) if total > 0 else 0
                },
                'coordinates': {
                    'avg_lat': round(lat, 6) if lat else None,
                    'avg_lng': round(lng, 6) if lng else None
                },
                'variations': [comuna, normalized]  # Will expand this
            }
        
        conn.close()
        self.communes_data = communes_data
        
        print(f"✅ Extracted data for {len(communes_data)} communes")
        return communes_data
    
    def analyze_patterns(self) -> Dict:
        """Analyze patterns in commune names"""
        print("📊 Analyzing commune name patterns...")
        
        if not self.communes_data:
            self.extract_commune_data()
        
        analysis = {
            'total_communes': len(self.communes_data),
            'by_region': defaultdict(list),
            'name_patterns': {
                'length_distribution': {},
                'common_prefixes': Counter(),
                'common_suffixes': Counter(),
                'common_words': Counter(),
                'special_characters': Counter()
            },
            'normalization_impacts': [],
            'potential_duplicates': []
        }
        
        # Analyze by region
        for comuna_data in self.communes_data.values():
            analysis['by_region'][comuna_data['region']].append({
                'name': comuna_data['original_name'],
                'pharmacies': comuna_data['statistics']['total_pharmacies']
            })
        
        # Analyze name patterns
        for comuna_data in self.communes_data.values():
            name = comuna_data['original_name']
            normalized = comuna_data['normalized_name']
            
            # Length distribution
            length = len(name)
            analysis['name_patterns']['length_distribution'][length] = \
                analysis['name_patterns']['length_distribution'].get(length, 0) + 1
            
            # Common prefixes/suffixes
            words = name.split()
            if len(words) > 1:
                analysis['name_patterns']['common_prefixes'][words[0]] += 1
                analysis['name_patterns']['common_suffixes'][words[-1]] += 1
            
            # Common words
            for word in words:
                if len(word) > 2:  # Skip short words
                    analysis['name_patterns']['common_words'][word] += 1
            
            # Special characters
            for char in name:
                if not char.isalnum() and not char.isspace():
                    analysis['name_patterns']['special_characters'][char] += 1
            
            # Track normalization impact
            if name != normalized:
                analysis['normalization_impacts'].append({
                    'original': name,
                    'normalized': normalized,
                    'changes': self._identify_changes(name, normalized)
                })
        
        # Find potential duplicates (after normalization)
        normalized_to_original = defaultdict(list)
        for comuna_data in self.communes_data.values():
            normalized_to_original[comuna_data['normalized_name']].append(
                comuna_data['original_name']
            )
        
        for normalized, originals in normalized_to_original.items():
            if len(originals) > 1:
                analysis['potential_duplicates'].append({
                    'normalized': normalized,
                    'variations': originals
                })
        
        # Convert Counters to regular dicts for JSON serialization
        for key in analysis['name_patterns']:
            if isinstance(analysis['name_patterns'][key], Counter):
                analysis['name_patterns'][key] = dict(analysis['name_patterns'][key].most_common(10))
        
        self.analysis_results = analysis
        print(f"✅ Analysis completed")
        return analysis
    
    def _identify_changes(self, original: str, normalized: str) -> List[str]:
        """Identify what changes were made during normalization"""
        changes = []
        
        if original.lower() != normalized:
            changes.append("case_change")
        
        # Check for accent removal
        original_no_case = original.lower()
        if original_no_case != normalized and len(original_no_case) == len(normalized):
            changes.append("accent_removal")
        
        # Check for special character removal
        original_clean = re.sub(r'[^\w\s]', '', original.lower())
        if original_clean != normalized:
            changes.append("special_char_removal")
        
        return changes
    
    def generate_variations(self) -> Dict:
        """Generate common variations for each commune"""
        print("🔄 Generating commune variations...")
        
        if not self.communes_data:
            self.extract_commune_data()
        
        for comuna, data in self.communes_data.items():
            variations = set([comuna, data['normalized_name']])
            
            # Add common variations
            name = comuna
            
            # Add without accents but keeping case
            no_accents = unicodedata.normalize('NFD', name)
            no_accents = ''.join(c for c in no_accents if unicodedata.category(c) != 'Mn')
            variations.add(no_accents)
            
            # Add all uppercase
            variations.add(name.upper())
            
            # Add all lowercase
            variations.add(name.lower())
            
            # Add variations without common prefixes/suffixes
            words = name.split()
            if len(words) > 1:
                # Try without first word if it's common
                if words[0].upper() in ['LA', 'LAS', 'EL', 'LOS', 'DE', 'DEL']:
                    variations.add(' '.join(words[1:]))
                
                # Try without last word if it's common
                if words[-1].upper() in ['NORTE', 'SUR', 'ESTE', 'OESTE', 'ALTO', 'BAJO']:
                    variations.add(' '.join(words[:-1]))
            
            # Store all variations
            self.communes_data[comuna]['variations'] = list(variations)
        
        print(f"✅ Generated variations for all communes")
        return self.communes_data
    
    def create_similarity_index(self) -> Dict:
        """Create similarity index for fast matching"""
        print("🧮 Creating similarity index...")
        
        if not self.communes_data:
            self.extract_commune_data()
        
        # Create trigram index for fast similarity search
        trigram_index = defaultdict(set)
        
        for comuna, data in self.communes_data.items():
            for variation in data['variations']:
                # Create trigrams
                text = f"  {variation.lower()}  "  # Padding for edge trigrams
                for i in range(len(text) - 2):
                    trigram = text[i:i+3]
                    trigram_index[trigram].add(comuna)
        
        similarity_data = {
            'trigram_index': {k: list(v) for k, v in trigram_index.items()},
            'commune_variations': {k: v['variations'] for k, v in self.communes_data.items()}
        }
        
        print(f"✅ Created similarity index with {len(trigram_index)} trigrams")
        return similarity_data
    
    def save_analysis(self, output_file: str = "commune_analysis.json"):
        """Save complete analysis to file"""
        print(f"💾 Saving analysis to {output_file}...")
        
        complete_data = {
            'metadata': {
                'total_communes': len(self.communes_data),
                'analysis_timestamp': pd.Timestamp.now().isoformat(),
                'database_path': self.db_path
            },
            'communes_data': self.communes_data,
            'analysis_results': self.analysis_results,
            'similarity_index': self.create_similarity_index()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(complete_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Analysis saved to {output_file}")
        return output_file
    
    def print_summary(self):
        """Print a summary of the analysis"""
        if not self.analysis_results:
            self.analyze_patterns()
        
        print("\n" + "="*60)
        print("📊 COMMUNE ANALYSIS SUMMARY")
        print("="*60)
        
        analysis = self.analysis_results
        
        print(f"📍 Total Communes: {analysis['total_communes']}")
        print(f"🏛️ Regions: {len(analysis['by_region'])}")
        
        print(f"\n📏 Name Length Distribution:")
        for length, count in sorted(analysis['name_patterns']['length_distribution'].items()):
            print(f"  {length} chars: {count} communes")
        
        print(f"\n🔤 Most Common Words:")
        for word, count in list(analysis['name_patterns']['common_words'].items())[:5]:
            print(f"  '{word}': {count} times")
        
        print(f"\n🔄 Normalization Impact:")
        print(f"  {len(analysis['normalization_impacts'])} communes affected by normalization")
        
        if analysis['potential_duplicates']:
            print(f"\n⚠️ Potential Duplicates:")
            for dup in analysis['potential_duplicates'][:3]:
                print(f"  {dup['normalized']} -> {dup['variations']}")
        
        print(f"\n🏆 Top Regions by Commune Count:")
        region_counts = [(region, len(communes)) for region, communes in analysis['by_region'].items()]
        for region, count in sorted(region_counts, key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {region}: {count} communes")

def main():
    """Run the complete commune analysis"""
    print("🚀 Starting Commune Database Analysis")
    print("="*50)
    
    analyzer = CommuneAnalyzer()
    
    # Step 1: Extract data
    analyzer.extract_commune_data()
    
    # Step 2: Analyze patterns
    analyzer.analyze_patterns()
    
    # Step 3: Generate variations
    analyzer.generate_variations()
    
    # Step 4: Save everything
    analyzer.save_analysis()
    
    # Step 5: Print summary
    analyzer.print_summary()
    
    print(f"\n✅ Analysis complete! Check 'commune_analysis.json' for full results.")

if __name__ == "__main__":
    main()
