import os
import re
import requests
import pytest
from dotenv import load_dotenv


load_dotenv()
MINSAL_API_BASE = os.getenv("MINSAL_API_BASE", "https://midas.minsal.cl/farmacia_v2/WS")


def _is_google_maps_url(s: str) -> bool:
    if not s or not isinstance(s, str):
        return False
    # common google maps patterns
    return bool(re.search(r"https?://(www\.)?(google\.com/maps|maps\.google|goo\.gl/maps)", s, re.IGNORECASE))


def _looks_like_address_field(key: str, value: str) -> bool:
    if not key or not isinstance(key, str):
        return False
    key_l = key.lower()
    if any(substr in key_l for substr in ("direccion", "direc", "ubicacion", "como", "llegar", "address")):
        return isinstance(value, str) and len(value.strip()) > 5
    return False


@pytest.mark.network
def test_minsal_records_expose_como_llegar():
    """
    Verifica que al menos un registro del endpoint `getLocales.php` incluye un campo
    utilizable como "cómo llegar":
      - una URL a Google Maps (recomendada) o
      - un campo de dirección legible (p. ej. 'local_direccion') y/o coordenadas

    Asumimos que el endpoint está disponible públicamente. Si la petición falla, el test se salta.
    """

    endpoint = f"{MINSAL_API_BASE}/getLocales.php"

    try:
        resp = requests.get(endpoint, timeout=15)
    except Exception as e:
        pytest.skip(f"No se pudo conectar al endpoint MINSAL ({endpoint}): {e}")

    if resp.status_code != 200:
        pytest.skip(f"Endpoint MINSAL devolvió HTTP {resp.status_code}")

    try:
        payload = resp.json()
    except ValueError:
        pytest.skip("La respuesta de MINSAL no es JSON válido")

    # payload puede ser una lista o un dict con clave 'data'
    if isinstance(payload, dict) and 'data' in payload:
        records = payload['data']
    else:
        records = payload

    assert isinstance(records, list) and len(records) > 0, "No se encontraron registros en el endpoint de MINSAL"

    found = False
    reasons = []

    for rec in records:
        if not isinstance(rec, dict):
            continue

        # 1) Buscar valores que contengan una URL de Google Maps
        for k, v in rec.items():
            if isinstance(v, str) and _is_google_maps_url(v):
                found = True
                reasons.append(f"Google Maps URL found in field '{k}'")
                break

        if found:
            break

        # 2) Buscar campos que parezcan dirección
        for k, v in rec.items():
            if _looks_like_address_field(k, v):
                # si además existen coordenadas en el mismo registro, lo consideramos suficiente
                lat = rec.get('local_lat') or rec.get('lat') or rec.get('latitude')
                lng = rec.get('local_lng') or rec.get('lng') or rec.get('longitude')
                if (lat and str(lat).strip() not in ('0', '0.0', '', None)) or (lng and str(lng).strip() not in ('0', '0.0', '', None)):
                    found = True
                    reasons.append(f"Address-like field '{k}' plus coordinates present")
                    break
                else:
                    # keep as potential match even without coords
                    found = True
                    reasons.append(f"Address-like field '{k}' present (no coords)")
                    break

        if found:
            break

    assert found, f"No se encontró ningún campo 'cómo llegar' en los registros de MINSAL. Ejemplos de inspección: {reasons[:5]}"
