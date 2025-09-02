# app/services/minsal_client.py
from typing import List, Dict, Optional
import os, requests, logging
from app.core.utils import norm_lower, is_open_now_from_times

log = logging.getLogger("minsal_client")
MINSAL_API_BASE = os.getenv("MINSAL_API_BASE", "https://farmanet.minsal.cl/index.php/ws")
DEFAULT_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "8.0"))

def _fetch(path: str) -> List[Dict]:
    url = f"{MINSAL_API_BASE.rstrip('/')}/{path.lstrip('/')}"
    resp = requests.get(url, timeout=DEFAULT_TIMEOUT)
    resp.raise_for_status()
    try:
        data = resp.json()
    except Exception as e:
        log.exception("Respuesta no-JSON desde MINSAL: %s", e)
        raise
    if isinstance(data, dict) and "data" in data:
        data = data["data"]
    return data if isinstance(data, list) else []

def _normalize_item(it: Dict) -> Dict:
    reg = (it.get("region") or it.get("fk_region") or "")
    com = (it.get("comuna") or it.get("comuna_nombre") or it.get("fk_comuna") or "")
    nombre = it.get("local_nombre") or it.get("nombre_local") or it.get("local")
    return {
        "nombre_local": nombre,
        "direccion": it.get("local_direccion") or it.get("direccion"),
        "comuna": str(com),
        "region": str(reg),
        "telefono": it.get("local_telefono") or it.get("telefono"),
        "lat": float(it.get("local_lat") or it.get("lat") or 0) if (it.get("local_lat") or it.get("lat")) else None,
        "lng": float(it.get("local_lng") or it.get("lng") or 0) if (it.get("local_lng") or it.get("lng")) else None,
        "horario_apertura": it.get("funcionamiento_hora_apertura"),
        "horario_cierre": it.get("funcionamiento_hora_cierre"),
    }

def get_locales(region: Optional[str]=None, comuna: Optional[str]=None, limit: int=20) -> List[Dict]:
    items = [_normalize_item(x) for x in _fetch("getLocales.php")]
    if region:
        rnorm = norm_lower(region)
        items = [x for x in items if norm_lower(x["region"]) == rnorm]
    if comuna:
        cnorm = norm_lower(comuna)
        items = [x for x in items if norm_lower(x["comuna"]) == cnorm]
    return items[: max(1, min(limit, 100))]

def get_locales_turno(region: Optional[str]=None, comuna: Optional[str]=None, abierto: bool=False, limit: int=20) -> List[Dict]:
    items = [_normalize_item(x) for x in _fetch("getLocalesTurnos.php")]
    if region:
        rnorm = norm_lower(region)
        items = [x for x in items if norm_lower(x["region"]) == rnorm]
    if comuna:
        cnorm = norm_lower(comuna)
        items = [x for x in items if norm_lower(x["comuna"]) == cnorm]
    if abierto:
        items = [x for x in items if is_open_now_from_times(x["horario_apertura"], x["horario_cierre"])]
    return items[: max(1, min(limit, 100))]
