"""
🗺️ Enhanced Location Utilities
Helper functions for formatting pharmacy data with enhanced location features
"""

from datetime import datetime, time
from typing import Dict, Optional
import urllib.parse
import re

def format_operating_hours(hora_apertura: str, hora_cierre: str, dia_funcionamiento: str) -> Dict[str, str]:
    """
    Convert operating hours to user-friendly format
    
    Args:
        hora_apertura: "08:30:00"
        hora_cierre: "18:30:00" 
        dia_funcionamiento: "viernes"
        
    Returns:
        Dictionary with formatted hour information
    """
    try:
        # Parse times and remove seconds
        apertura = hora_apertura.split(":")[0:2]  # ["08", "30"]
        cierre = hora_cierre.split(":")[0:2]      # ["18", "30"]
        
        apertura_clean = ":".join(apertura)  # "08:30"
        cierre_clean = ":".join(cierre)      # "18:30"
        
        # Capitalize day name
        dia_display = dia_funcionamiento.capitalize()
        
        # Determine current status
        now = datetime.now()
        current_time = now.time()
        
        try:
            apertura_time = time(int(apertura[0]), int(apertura[1]))
            cierre_time = time(int(cierre[0]), int(cierre[1]))
            
            if apertura_time <= current_time <= cierre_time:
                estado = "abierta"
            elif current_time < apertura_time:
                estado = "por_abrir"
            else:
                estado = "cerrada"
        except (ValueError, IndexError):
            estado = "sin_informacion"
        
        return {
            "apertura": apertura_clean,
            "cierre": cierre_clean,
            "dia_actual": dia_funcionamiento,
            "dia_display": dia_display,
            "display": f"{dia_display} {apertura_clean} - {cierre_clean}",
            "estado": estado
        }
        
    except (AttributeError, IndexError, ValueError):
        return {
            "apertura": hora_apertura,
            "cierre": hora_cierre,
            "dia_actual": dia_funcionamiento,
            "dia_display": dia_funcionamiento.capitalize(),
            "display": f"{dia_funcionamiento.capitalize()} {hora_apertura} - {hora_cierre}",
            "estado": "sin_informacion"
        }

def generate_maps_urls(lat: float, lng: float, address: str, pharmacy_name: str) -> Dict[str, str]:
    """
    Generate various map URLs from coordinates and address
    
    Args:
        lat: Latitude (-32.9849921792696)
        lng: Longitude (-71.2757177058683)
        address: "URMENETA 99"
        pharmacy_name: "CRUZ VERDE"
        
    Returns:
        Dictionary with different map URL formats
    """
    # Encode address and name for URLs
    encoded_address = urllib.parse.quote(f"{pharmacy_name} {address}")
    coords_string = f"{lat},{lng}"
    
    return {
        "google_maps": f"https://maps.google.com/maps?q={coords_string}",
        "apple_maps": f"http://maps.apple.com/?q={coords_string}",
        "direcciones": f"https://www.google.com/maps/dir/?destination={coords_string}",
        "google_search": f"https://www.google.com/maps/search/{encoded_address}",
        "waze": f"https://waze.com/ul?ll={coords_string}&navigate=yes",
        "coordinates": coords_string
    }

def format_phone_number(raw_phone: str) -> Dict[str, str]:
    """
    Format Chilean phone numbers for better display and functionality
    
    Args:
        raw_phone: "+56332415940" or "332415940"
        
    Returns:
        Dictionary with formatted phone information
    """
    if not raw_phone:
        return {
            "telefono_raw": "",
            "telefono_display": "Sin teléfono",
            "click_to_call": "",
            "whatsapp": "",
            "formato": "sin_telefono"
        }
    
    # Clean the phone number
    clean_phone = re.sub(r'[^\d+]', '', raw_phone)
    
    # Ensure it starts with +56
    if not clean_phone.startswith('+56'):
        if clean_phone.startswith('56'):
            clean_phone = '+' + clean_phone
        elif clean_phone.startswith('0'):
            clean_phone = '+56' + clean_phone[1:]
        else:
            clean_phone = '+56' + clean_phone
    
    # Format for display: +56 33 241 5940
    try:
        if len(clean_phone) >= 11:  # +56xxxxxxxxx
            country = clean_phone[:3]     # +56
            area = clean_phone[3:5]       # 33
            first = clean_phone[5:8]      # 241
            second = clean_phone[8:]      # 5940
            
            display_format = f"{country} {area} {first} {second}"
        else:
            display_format = clean_phone
    except:
        display_format = raw_phone
    
    # Generate WhatsApp URL (remove + and spaces)
    whatsapp_number = clean_phone.replace('+', '').replace(' ', '')
    
    return {
        "telefono_raw": clean_phone,
        "telefono_display": display_format,
        "click_to_call": f"tel:{clean_phone}",
        "whatsapp": f"https://wa.me/{whatsapp_number}",
        "formato": "valido" if clean_phone.startswith('+56') else "invalido"
    }

def determine_open_status(hora_apertura: str, hora_cierre: str, current_datetime: Optional[datetime] = None) -> str:
    """
    Determine if pharmacy is currently open
    
    Args:
        hora_apertura: "08:30:00"
        hora_cierre: "18:30:00"
        current_datetime: Optional datetime (uses now() if not provided)
        
    Returns:
        "abierta", "cerrada", "por_abrir", or "sin_informacion"
    """
    if not current_datetime:
        current_datetime = datetime.now()
    
    current_time = current_datetime.time()
    
    try:
        # Parse opening and closing times
        apertura_parts = hora_apertura.split(":")
        cierre_parts = hora_cierre.split(":")
        
        apertura_time = time(int(apertura_parts[0]), int(apertura_parts[1]))
        cierre_time = time(int(cierre_parts[0]), int(cierre_parts[1]))
        
        # Handle cases where closing time is past midnight (24-hour format)
        if cierre_time < apertura_time:
            # Pharmacy closes after midnight
            if current_time >= apertura_time or current_time <= cierre_time:
                return "abierta"
            else:
                return "cerrada"
        else:
            # Normal opening hours within same day
            if apertura_time <= current_time <= cierre_time:
                return "abierta"
            elif current_time < apertura_time:
                return "por_abrir"
            else:
                return "cerrada"
                
    except (ValueError, IndexError, AttributeError):
        return "sin_informacion"

def enhance_pharmacy_info(farmacia, db_instance=None) -> Dict:
    """
    Enhanced pharmacy information formatting
    
    Args:
        farmacia: Pharmacy object with all MINSAL data
        db_instance: Database instance for additional checks
        
    Returns:
        Enhanced pharmacy dictionary with location features
    """
    # Base information (existing format preserved)
    farmacia_info = {
        "nombre": farmacia.nombre,
        "direccion": farmacia.direccion,
        "comuna": farmacia.comuna,
        "telefono": farmacia.telefono or "Sin teléfono",
        "turno": farmacia.es_turno,
        "cadena": "Independiente"  # Could be enhanced with actual chain data
    }
    
    # Enhanced operating hours
    if farmacia.hora_apertura and farmacia.hora_cierre:
        horario_info = format_operating_hours(
            farmacia.hora_apertura, 
            farmacia.hora_cierre, 
            farmacia.dia_funcionamiento or "sin información"
        )
        farmacia_info["horario"] = horario_info
        farmacia_info["abierta"] = (horario_info["estado"] == "abierta")
    else:
        farmacia_info["horario"] = {
            "display": "Sin información de horarios",
            "estado": "sin_informacion"
        }
        farmacia_info["abierta"] = False
    
    # Enhanced location features (if coordinates available)
    if farmacia.lat and farmacia.lng and farmacia.lat != 0.0 and farmacia.lng != 0.0:
        farmacia_info["ubicacion"] = {
            "latitud": farmacia.lat,
            "longitud": farmacia.lng
        }
        
        # Generate map URLs
        farmacia_info["mapas"] = generate_maps_urls(
            farmacia.lat,
            farmacia.lng, 
            farmacia.direccion,
            farmacia.nombre
        )
    
    # Enhanced contact information
    farmacia_info["contacto"] = format_phone_number(farmacia.telefono or "")
    
    return farmacia_info
