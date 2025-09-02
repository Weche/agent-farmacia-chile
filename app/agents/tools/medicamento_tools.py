#!/usr/bin/env python3
"""
Medication Lookup Tool for AI Agent
Searches medication information using enhanced vademecum service
"""

import logging
from typing import Dict, Any, List, Optional
from app.agents.tools.base_tool import BaseTool
from app.services.vademecum_service import load_vademecum, search_vademecum
from app.core.utils import get_env_value

logger = logging.getLogger(__name__)

class LookupMedicamentoTool(BaseTool):
    """
    Tool for looking up medication information with bilingual search
    """
    
    def __init__(self):
        super().__init__(
            name="lookup_medicamento",
            description="Busca información detallada sobre medicamentos en el vademécum. Soporta búsqueda en español e inglés con información completa sobre composición, usos y precauciones."
        )
        # Load vademecum data
        vademecum_path = get_env_value('VADEMECUM_PATH')
        self.vademecum_data = load_vademecum(vademecum_path)
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute medication lookup
        
        Args:
            medicamento (str): Nombre del medicamento a buscar
            busqueda_exacta (bool, optional): Si realizar búsqueda exacta (True) o parcial (False)
            limite (int, optional): Número máximo de resultados (default: 5)
            incluir_similares (bool, optional): Si incluir medicamentos similares (default: True)
            
        Returns:
            Dictionary with medication information
        """
        medicamento = kwargs.get("medicamento", "").strip()
        busqueda_exacta = kwargs.get("busqueda_exacta", False)
        limite = kwargs.get("limite", 5)
        incluir_similares = kwargs.get("incluir_similares", True)
        
        # Validate inputs
        if not medicamento:
            return {
                "error": "Se requiere especificar el nombre del medicamento",
                "medicamentos": [],
                "total": 0
            }
        
        if len(medicamento) < 2:
            return {
                "error": "El nombre del medicamento debe tener al menos 2 caracteres",
                "medicamentos": [],
                "total": 0
            }
        
        try:
            # Search medications using existing service
            resultados = search_vademecum(
                items=self.vademecum_data,
                q=medicamento,
                limit=limite if limite > 0 else 10
            )
            
            # If exact match is requested, filter results
            if busqueda_exacta:
                resultados = [
                    item for item in resultados
                    if medicamento.lower() in item.get("nombre", "").lower() or 
                       medicamento.lower() in item.get("principio_activo", "").lower()
                ]
            
            # Format results for agent
            medicamentos_formateados = []
            
            for medicamento_info in resultados:
                medicamento_formateado = {
                    "nombre": medicamento_info.get("nombre", "Sin nombre"),
                    "principio_activo": medicamento_info.get("principio_activo", "No especificado"),
                    "forma_farmaceutica": medicamento_info.get("forma_farmaceutica", "No especificada"),
                    "concentracion": medicamento_info.get("concentracion", "No especificada"),
                    "laboratorio": medicamento_info.get("laboratorio", "No especificado"),
                    "categoria": medicamento_info.get("categoria_terapeutica", "Sin categoría"),
                    "uso_terapeutico": medicamento_info.get("uso_terapeutico", "No especificado")
                }
                
                # Add additional information if available
                medicamento_formateado.update({
                    "indicaciones": medicamento_info.get("indicaciones", "Consulte con su médico"),
                    "contraindicaciones": medicamento_info.get("contraindicaciones", "Consulte prospecto"),
                    "efectos_adversos": medicamento_info.get("efectos_adversos", "Consulte prospecto"),
                    "dosificacion": medicamento_info.get("dosificacion", "Según prescripción médica"),
                    "precauciones": medicamento_info.get("precauciones", "Uso bajo supervisión médica")
                })
                
                # Add safety disclaimer
                medicamento_formateado["advertencia_seguridad"] = (
                    "⚠️ INFORMACIÓN SOLO PARA CONSULTA. No reemplaza la consulta médica profesional. "
                    "Siempre consulte con un profesional de la salud antes de usar cualquier medicamento."
                )
                
                medicamentos_formateados.append(medicamento_formateado)
            
            # Generate summary
            total_encontrados = len(resultados)
            mostrados = len(medicamentos_formateados)
            
            # Find similar medications if requested
            similares = []
            if incluir_similares and total_encontrados > 0:
                primer_resultado = resultados[0]
                principio_activo = primer_resultado.get("principio_activo", "")
                
                if principio_activo:
                    # Search by active ingredient for similar medications
                    similares_resultados = search_vademecum(
                        items=self.vademecum_data,
                        q=principio_activo,
                        limit=5
                    )
                    
                    # Filter out already shown medications
                    nombres_mostrados = {med["nombre"].lower() for med in medicamentos_formateados}
                    similares = [
                        {
                            "nombre": med.get("nombre", ""),
                            "laboratorio": med.get("laboratorio", ""),
                            "forma_farmaceutica": med.get("forma_farmaceutica", "")
                        }
                        for med in similares_resultados[:3]  # Max 3 similar
                        if med.get("nombre", "").lower() not in nombres_mostrados
                    ]
            
            resumen = {
                "termino_busqueda": medicamento,
                "busqueda_exacta": busqueda_exacta,
                "total_encontrados": total_encontrados,
                "mostrados": mostrados,
                "similares_encontrados": len(similares)
            }
            
            resultado = {
                "medicamentos": medicamentos_formateados,
                "medicamentos_similares": similares,
                "resumen": resumen,
                "total": total_encontrados,
                "mensaje": f"Se encontraron {total_encontrados} medicamentos para '{medicamento}'" + 
                          (f". Mostrando {mostrados} resultados." if total_encontrados > mostrados else "."),
                "advertencia_general": (
                    "🏥 Esta información es solo para consulta y no constituye consejo médico. "
                    "Para el uso seguro de medicamentos, siempre consulte con un profesional de la salud."
                )
            }
            
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Error looking up medication: {e}")
            return {
                "error": f"Error al buscar medicamento: {str(e)}",
                "medicamentos": [],
                "total": 0,
                "advertencia": "Si necesita información sobre medicamentos, consulte directamente con un farmacéutico o médico."
            }
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """
        Get JSON schema for medication lookup parameters
        """
        return {
            "type": "object",
            "properties": {
                "medicamento": {
                    "type": "string",
                    "description": "Nombre del medicamento a buscar (puede ser nombre comercial, principio activo, o nombre en inglés)",
                    "minLength": 2,
                    "examples": ["paracetamol", "aspirina", "ibuprofeno", "acetaminophen"]
                },
                "busqueda_exacta": {
                    "type": "boolean",
                    "description": "Si buscar coincidencia exacta (true) o permitir coincidencias parciales (false)",
                    "default": False
                },
                "limite": {
                    "type": "integer",
                    "description": "Número máximo de medicamentos a retornar",
                    "minimum": 1,
                    "maximum": 20,
                    "default": 5
                },
                "incluir_similares": {
                    "type": "boolean",
                    "description": "Si incluir medicamentos similares con el mismo principio activo",
                    "default": True
                }
            },
            "required": ["medicamento"]
        }


class GetMedicationCategoriestool(BaseTool):
    """
    Tool for getting available medication categories
    """
    
    def __init__(self):
        super().__init__(
            name="get_medication_categories",
            description="Obtiene las categorías terapéuticas disponibles en el vademécum para ayudar en la búsqueda de medicamentos."
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Get available medication categories
        
        Returns:
            Dictionary with medication categories
        """
        try:
            # This would be implemented to get actual categories from the vademecum
            # For now, return common therapeutic categories
            categorias = [
                "Analgésicos y Antiinflamatorios",
                "Antibióticos",
                "Antihistamínicos",
                "Antihipertensivos",
                "Antidiabéticos",
                "Antiácidos y Digestivos",
                "Vitaminas y Suplementos",
                "Dermatológicos",
                "Oftalmológicos",
                "Respiratorios",
                "Cardiológicos",
                "Neurológicos",
                "Ginecológicos",
                "Pediátricos"
            ]
            
            return {
                "categorias": sorted(categorias),
                "total": len(categorias),
                "mensaje": f"Se encontraron {len(categorias)} categorías terapéuticas disponibles",
                "nota": "Para buscar medicamentos en una categoría específica, use el término de la categoría en la búsqueda de medicamentos"
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting medication categories: {e}")
            return {
                "error": f"Error al obtener categorías: {str(e)}",
                "categorias": [],
                "total": 0
            }
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """
        Get JSON schema for category parameters
        """
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
