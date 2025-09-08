# app/services/vademecum_service.py
from typing import List, Dict, Optional
import os, csv, json
from pathlib import Path

def _load_from_parquet(path: str) -> List[Dict]:
    try:
        import pandas as pd
        df = pd.read_parquet(path)
        return df.to_dict(orient="records")
    except Exception:
        return []

def _load_from_csv(path: str) -> List[Dict]:
    out = []
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                out.append({k: v for k, v in row.items()})
    except Exception:
        return []
    return out

def load_vademecum(path: Optional[str]) -> List[Dict]:
    import logging
    logger = logging.getLogger(__name__)
    
    if not path:
        logger.warning("⚠️  No vademecum path provided")
        return []
    
    logger.info(f"📋 Loading vademecum from: {path}")
    p = Path(path)
    
    if not p.exists():
        logger.error(f"❌ Vademecum file not found: {path}")
        # Try alternative paths for debugging
        alt_paths = [
            "./data/comprehensive_vademecum.csv",
            "/app/data/comprehensive_vademecum.csv",
            "comprehensive_vademecum.csv"
        ]
        for alt_path in alt_paths:
            if Path(alt_path).exists():
                logger.info(f"📋 Found vademecum at alternative path: {alt_path}")
                p = Path(alt_path)
                break
        else:
            logger.error(f"❌ Vademecum not found in any alternative paths: {alt_paths}")
            return []
    
    try:
        if p.suffix.lower() in [".parquet", ".pq"]:
            data = _load_from_parquet(str(p))
        elif p.suffix.lower() in [".csv", ".txt"]:
            data = _load_from_csv(str(p))
        else:
            logger.error(f"❌ Unsupported vademecum file format: {p.suffix}")
            return []
        
        logger.info(f"✅ Vademecum loaded successfully: {len(data)} medications")
        return data
        
    except Exception as e:
        logger.error(f"❌ Error loading vademecum: {e}")
        return []

def search_vademecum(items: List[Dict], q: str, limit: int=10) -> List[Dict]:
    """
    Search medications with bilingual support (Spanish/English)
    Supports both original Spanish fields and Kaggle dataset English fields
    """
    ql = (q or "").lower()
    res = []
    
    # Common medication name mappings for bilingual search
    name_mappings = {
        'aspirin': 'aspirina',
        'acetaminophen': 'paracetamol', 
        'ibuprofen': 'ibuprofeno',
        'amoxicillin': 'amoxicilina'
    }
    
    # Add reverse mappings
    reverse_mappings = {v: k for k, v in name_mappings.items()}
    name_mappings.update(reverse_mappings)
    
    # Expand search query with alternative names
    search_terms = [ql]
    if ql in name_mappings:
        search_terms.append(name_mappings[ql])
    
    for it in items:
        # Support both Spanish and English field names
        nombre = (it.get("nombre") or it.get("Drug Name") or 
                 it.get("denominacion_comun") or "")
        pa = (it.get("principio_activo") or it.get("Generic Name") or "")
        
        # Search in multiple fields
        searchable_text = f"{nombre} {pa}".lower()
        
        # Check if any search term matches
        match_found = any(term in searchable_text for term in search_terms)
        
        if match_found:
            # Create standardized response with safety information
            result = {
                "nombre": nombre or pa,
                "principio_activo": pa or nombre,
                "forma": it.get("forma") or it.get("Dosage Form") or "Ver envase",
                "concentracion": it.get("concentracion") or it.get("Strength") or "Ver envase",
                "presentacion": it.get("presentacion") or f"{it.get('forma', 'N/A')} - {it.get('concentracion', 'Ver envase')}",
                "indicaciones": it.get("indicaciones") or it.get("Indications") or "Consulte información del producto",
                "advertencias": it.get("advertencias") or it.get("Warnings and Precautions") or 
                              "Lea las instrucciones del envase. Consulte con un profesional de la salud.",
                "contraindicaciones": it.get("contraindicaciones") or it.get("Contraindications") or 
                                   "Consulte las contraindicaciones en el envase del producto",
                "contraindicaciones_fuente": it.get("contraindicaciones_fuente") or 
                                           "Fuente: Dataset farmacológico - Solo información general",
                "categoria": it.get("categoria") or it.get("Drug Class") or "Ver clasificación",
                "disponibilidad": it.get("disponibilidad") or it.get("Availability") or "Consulte disponibilidad"
            }
            res.append(result)
            
        if len(res) >= limit:
            break
    
    return res
