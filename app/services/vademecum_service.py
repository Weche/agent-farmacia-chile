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
    if not path:
        return []
    p = Path(path)
    if not p.exists():
        return []
    if p.suffix.lower() in [".parquet", ".pq"]:
        return _load_from_parquet(str(p))
    if p.suffix.lower() in [".csv", ".txt"]:
        return _load_from_csv(str(p))
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
            'amoxicillin': 'amoxicilina',
            'lisinopril': 'lisinopril',
            'albuterol': 'salbutamol',
            'omeprazole': 'omeprazol',
            'levothyroxine': 'levotiroxina',
            'simvastatin': 'simvastatina',
            'metformin': 'metformina',
            'ibuprofen': 'ibuprofeno',
            'ciprofloxacin': 'ciprofloxacino',
            'alprazolam': 'alprazolam',
            'ranitidine': 'ranitidina',
            'atorvastatin': 'atorvastatina',
            'cephalexin': 'cefalexina',
            'paracetamol': 'paracetamol',
            'morphine': 'morfina',
            'risperidone': 'risperidona',
            'sildenafil': 'sildenafilo',
            'furosemide': 'furosemida',
            'esomeprazole': 'esomeprazol',
            'warfarin': 'warfarina',
            'tramadol': 'tramadol',
            'fluoxetine': 'fluoxetina',
            'levofloxacin': 'levofloxacino',
            'lorazepam': 'lorazepam',
            'losartan': 'losartán',
            'amphetamine': 'anfetamina',
            'citalopram': 'citalopram',
            'metoprolol': 'metoprolol',
            'venlafaxine': 'venlafaxina',
            'methylphenidate': 'metilfenidato',
            'rosuvastatin': 'rosuvastatina',
            'bupropion': 'bupropión',
            'ceftriaxone': 'ceftriaxona',
            'fentanyl': 'fentanilo',
            'hydrochlorothiazide': 'hidroclorotiazida',
            'escitalopram': 'escitalopram',
            'amlodipine': 'amlodipino',
            'mirtazapine': 'mirtazapina',
            'trazodone': 'trazodona',
            'pravastatin': 'pravastatina',
            'aripiprazole': 'aripiprazol',
            'amoxicillin-clavulanate': 'amoxicilina / ácido clavulánico',
            'lithium': 'litio',
            'pregabalin': 'pregabalina',
            'isosorbide mononitrate': 'mononitrato de isosorbida',
            'ezetimibe': 'ezetimiba',
            'enalapril': 'enalapril',
            'diazepam': 'diazepam',
            'methotrexate': 'metotrexato',
            'cetirizine': 'cetirizina',
            'bromocriptine': 'bromocriptina',
            'ethinyl estradiol / levonorgestrel': 'etinilestradiol / levonorgestrel',
            'gabapentin': 'gabapentina',
            'naproxen': 'naproxeno',
            'carvedilol': 'carvedilol',
            'clopidogrel': 'clopidogrel',
            'ezetimibe / simvastatin': 'ezetimiba / simvastatina',
            'fluticasone propionate': 'propionato de fluticasona',
            'metronidazole': 'metronidazol',
            'duloxetine': 'duloxetina',
            'chlorthalidone': 'clortalidona',
            'cefuroxime': 'cefuroxima',
            'alendronate': 'alendronato',
            'levetiracetam': 'levetiracetam',
            'pioglitazone': 'pioglitazona',
            'cyclobenzaprine': 'ciclobenzaprina',
            'quetiapine': 'quetiapina',
            'paroxetine': 'paroxetina',
            'allopurinol': 'alopurinol',
            'ethinyl estradiol / norgestimate': 'etinilestradiol / norgestimato',
            'valacyclovir': 'valaciclovir',
            'clonazepam': 'clonazepam',
            'memantine': 'memantina',
            'insulin glargine': 'insulina glargina',
            'potassium chloride': 'cloruro de potasio',
            'tamoxifen': 'tamoxifeno',
            'latanoprost': 'latanoprost',
            'loratadine': 'loratadina',
            'bimatoprost': 'bimatoprost',
            'lamotrigine': 'lamotrigina',
            'rosiglitazone': 'rosiglitazona',
            'prednisone': 'prednisona',
            'fluticasone propionate / salmeterol': 'propionato de fluticasona / salmeterol',
            'ondansetron': 'ondansetrón',
            'amiodarone': 'amiodarona',
            'drospirenone / ethinyl estradiol': 'drospirenona / etinilestradiol',
            'propranolol': 'propranolol',
            'olanzapine': 'olanzapina',
            'atenolol': 'atenolol',
            'sertraline': 'sertralina',
            'lovastatin': 'lovastatina'
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
