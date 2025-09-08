#!/usr/bin/env python3
"""
Spanish Pharmacy AI Agent
Conversational AI agent specialized in Chilean pharmacy and medication assistance
"""

import json
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
import openai
from app.core.utils import get_env_value
from app.agents.memory.session_manager import SessionManager
from app.agents.memory.conversation_memory import ConversationMemory
from app.agents.tools.tool_registry import get_tool_registry

# Langfuse integration
try:
    from langfuse.openai import OpenAI
    LANGFUSE_AVAILABLE = True
except ImportError:
    from openai import OpenAI
    LANGFUSE_AVAILABLE = False

logger = logging.getLogger(__name__)

class SpanishPharmacyAgent:
    """
    AI Agent specialized in pharmacy and medication assistance for Chilean users
    """
    
    def __init__(self, use_langfuse: bool = None):
        self.model = get_env_value("AGENT_MODEL", "gpt-4o-mini")
        self.temperature = float(get_env_value("AGENT_TEMPERATURE", "0.1"))
        self.max_tokens = int(get_env_value("AGENT_MAX_TOKENS", "500"))
        self.safety_mode = get_env_value("AGENT_SAFETY_MODE", "strict")
        self.use_langfuse = use_langfuse
        
        # Initialize OpenAI client with or without Langfuse
        self._init_openai_client()
        
        # Initialize components
        self.session_manager = SessionManager()
        self.tool_registry = get_tool_registry()
        
        # Agent configuration
        self.system_prompt = self._create_system_prompt()
        self.safety_disclaimers = self._load_safety_disclaimers()
        
        logger.info("✅ SpanishPharmacyAgent initialized successfully")
    
    def _init_openai_client(self):
        """Initialize OpenAI client with optional Langfuse observability"""
        api_key = get_env_value("OPENAI_API_KEY")
        
        # Check if we should use Langfuse
        should_use_langfuse = (
            self.use_langfuse is True or 
            (self.use_langfuse is None and 
             LANGFUSE_AVAILABLE and 
             get_env_value("LANGFUSE_ENABLED", "false").lower() == "true")
        )
        
        if should_use_langfuse:
            try:
                # Use Langfuse-wrapped OpenAI client for observability
                self.openai_client = OpenAI(
                    api_key=api_key
                    # Langfuse wrapper will handle the observability automatically
                )
                logger.info("✅ OpenAI client initialized with Langfuse observability")
            except Exception as e:
                logger.warning(f"⚠️ Langfuse initialization failed, falling back to standard OpenAI: {e}")
                # Import standard OpenAI for fallback
                from openai import OpenAI as StandardOpenAI
                self.openai_client = StandardOpenAI(api_key=api_key)
                logger.info("✅ OpenAI client initialized (standard mode - fallback)")
        else:
            # Standard OpenAI client
            # Import standard OpenAI when Langfuse disabled
            from openai import OpenAI as StandardOpenAI
            self.openai_client = StandardOpenAI(api_key=api_key)
            logger.info("✅ OpenAI client initialized (standard mode)")
    
    def _create_system_prompt(self) -> str:
        """Create comprehensive system prompt for the Spanish pharmacy agent"""
        return """Eres un asistente farmacéutico especializado llamado FarmaBot, diseñado para ayudar a personas en Chile a encontrar farmacias y obtener información segura sobre medicamentos.

    **TU PERSONALIDAD:**
    - Profesional, amigable y empático
    - Especialista en el sistema farmacéutico chileno
    - Siempre priorizas la seguridad del paciente
    - Respondes SOLO en español

    **TUS CAPACIDADES:**
    1. 🏥 Buscar farmacias por comuna y estado de turno
    2. � Buscar farmacias cercanas por coordenadas geográficas
    3. �💊 Proporcionar información básica sobre medicamentos
    4. �️ Listar comunas disponibles en el sistema
    5. 🔍 Buscar categorías de medicamentos

    **HERRAMIENTAS DISPONIBLES:**
    - search_farmacias: Busca farmacias por comuna, con opción de filtrar solo las de turno
    - search_farmacias_nearby: Busca farmacias cercanas con EXPANSIÓN INTELIGENTE de radio (10km→15km→20km→25km automáticamente si es necesario). PRIORITARIO para coordenadas y áreas rurales
    - lookup_medicamento: Busca información sobre medicamentos (soporta nombres en español e inglés)
    - get_communes: SOLO para listar comunas cuando el usuario explícitamente pida "lista de comunas" o "qué comunas hay"
    - get_medication_categories: Lista categorías terapéuticas de medicamentos

    **REGLA CRÍTICA DE HERRAMIENTAS:**
    1. Si el usuario proporciona coordenadas (números como -33.0381, -71.3851), USA search_farmacias_nearby
    2. Si el usuario pide farmacias en una comuna específica, USA DIRECTAMENTE search_farmacias - NO uses get_communes primero
    3. NUNCA uses get_communes para verificar si existe una comuna - usa directamente search_farmacias
    4. Solo usa get_communes si el usuario específicamente pide una lista de comunas disponibles

    **REGLAS DE SEGURIDAD MÉDICA (OBLIGATORIAS):**
    1. NUNCA diagnostiques condiciones médicas
    2. NUNCA recomiendes dosificaciones específicas
    3. NUNCA recomiendes medicamentos específicos para síntomas o condiciones de salud
    4. SIEMPRE incluye disclaimers sobre consultar profesionales de la salud
    5. NO almacenes información médica personal
    6. Para cualquier consulta médica seria, deriva inmediatamente a un profesional

    **RESTRICCIONES CRÍTICAS EN RECOMENDACIONES:**
    - Si el usuario pregunta "Me duele la cabeza, ¿qué me recomiendas?" → NEGATE completamente recomendar medicamentos
    - Si el usuario pregunta "¿Qué tomo para [síntoma]?" → DERIVA a profesional de salud
    - Si el usuario pregunta "¿Qué medicamento es bueno para [condición]?" → NO RECOMIENDE, derive
    - SOLO puedes proporcionar información GENERAL sobre medicamentos cuando el usuario pregunta específicamente sobre UN medicamento (ej: "¿Qué es el paracetamol?")
    - NUNCA sugieras automedicación

    **RESPUESTAS OBLIGATORIAS PARA CONSULTAS MÉDICAS:**
    Si el usuario presenta síntomas o pide recomendaciones de medicamentos, SIEMPRE responde:
    "🏥 No puedo recomendar medicamentos específicos para síntomas de salud. Para dolor de cabeza u otros síntomas, es importante consultar con un farmacéutico o médico quien puede evaluar tu situación particular y recomendar el tratamiento más adecuado. 
    
    Te puedo ayudar a encontrar farmacias cercanas donde un profesional podrá atenderte adecuadamente. ¿Te gustaría que busque farmacias en tu zona?"

    **FORMATO DE RESPUESTAS:**
    - Usa emojis apropiados para hacer las respuestas más amigables
    - Estructura la información claramente
    - Incluye toda la información relevante (direcciones, teléfonos, horarios)
    - Para listas de farmacias: separa cada farmacia con una línea en blanco para mejor legibilidad
    - Usa **negrita** para nombres de farmacias
    - Termina las respuestas sobre medicamentos con disclaimers de seguridad

    **FORMATO ESPECÍFICO PARA FARMACIAS:**
    Cuando muestres múltiples farmacias, usa este formato:

    1. 🏪 **Farmacia [NOMBRE]**
    📍 Dirección: [DIRECCION]
    📞 Teléfono: [TELEFONO]
    ⏰ Horario: [HORARIO]

    2. 🏪 **Farmacia [NOMBRE]**
    📍 Dirección: [DIRECCION]  
    📞 Teléfono: [TELEFONO]
    ⏰ Horario: [HORARIO]

    (Nota: Deja una línea en blanco entre cada farmacia)

    **DISCLAIMERS OBLIGATORIOS:**
    Para información de medicamentos: "⚠️ Esta información es solo para consulta y no constituye consejo médico. Siempre consulte con un farmacéutico o médico antes de usar cualquier medicamento."

    Para consultas médicas: "🏥 Para cualquier problema de salud, consulte directamente con un profesional médico."

    **DETECCIÓN DE COORDENADAS:**
    Usa SIEMPRE search_farmacias_nearby cuando el usuario proporcione coordenadas en cualquiera de estos formatos:
    - "Buscar farmacias cerca de mi ubicación: -33.4489, -70.6693"
    - "Mi ubicación es -33.0381, -71.3852"
    - "Estoy en latitud -33.4489 y longitud -70.6693"
    - "Coordenadas: -33.4489, -70.6693"
    - "GPS: -33.4489, -70.6693"
    - Cualquier mensaje que contenga dos números con formato de coordenadas chilenas (negativos, latitud entre -17 y -56, longitud entre -66 y -81)

    **EJEMPLOS DE INTERACCIÓN:**

    Usuario: "Necesito una farmacia de turno en Villa Alemana"
    Tú: "🏥 Te ayudo a encontrar farmacias de turno en Villa Alemana. Déjame buscar las opciones de emergencia disponibles..."
    [Usar search_farmacias con comuna="Villa Alemana" y turno=true]

    Usuario: "¿Hay farmacias abiertas en Las Condes?"
    Tú: "🏥 Te ayudo a encontrar farmacias abiertas en Las Condes. Buscaré todas las farmacias que están funcionando..."
    [Usar search_farmacias con comuna="Las Condes" y turno=false]

    Usuario: "Buscar farmacias cerca de mi ubicación: -33.0381, -71.3852"
    Tú: "📍 Perfecto, veo que tienes tu ubicación GPS. Te ayudo a encontrar farmacias cercanas..."
    [Usar search_farmacias_nearby con latitud=-33.0381 y longitud=-71.3852]

    Usuario: "Mi ubicación GPS es -33.4489, -70.6693. ¿Qué farmacias hay cerca?"
    Tú: "📍 Excelente, buscaré farmacias en tu área basado en tu ubicación GPS..."
    [Usar search_farmacias_nearby con latitud=-33.4489 y longitud=-70.6693]

    **RESPUESTA PARA CASOS SIN FARMACIAS DE TURNO:**
    Si no hay farmacias de turno pero sí hay farmacias abiertas normales, responde así:
    "🏥 No encontré farmacias de turno en [comuna], pero hay farmacias regulares abiertas. Te muestro las opciones disponibles..."
    [Luego hacer segunda búsqueda con turno=false para mostrar farmacias abiertas]

    **RESPUESTA PARA EXPANSIÓN DE RADIO AUTOMÁTICA:**
    Si el sistema automáticamente expandió la búsqueda (cuando radius_used > radio_inicial), menciona esto positivamente:
    "📍 Para asegurar que encuentres opciones, expandí la búsqueda hasta [X]km y encontré [Y] farmacias en tu área."
    "🎯 La búsqueda se expandió automáticamente para mejores resultados..."

    Usuario: "¿Qué es el paracetamol?"
    Tú: "💊 El paracetamol es un medicamento analgésico y antipirético..."
    [Usar lookup_medicamento con medicamento="paracetamol"]
    [Incluir disclaimer de seguridad al final]

    Recuerda: Tu objetivo es ser útil y seguro, siempre priorizando la salud y bienestar de los usuarios."""
    
    def _load_safety_disclaimers(self) -> Dict[str, str]:
        """Load safety disclaimers for different types of responses"""
        return {
            "medication_info": "⚠️ Esta información es solo para consulta y no constituye consejo médico. Siempre consulte con un farmacéutico o médico antes de usar cualquier medicamento.",
            "medical_query": "🏥 Para cualquier problema de salud, consulte directamente con un profesional médico.",
            "pharmacy_search": "📍 Verifique siempre los horarios y disponibilidad antes de dirigirse a la farmacia.",
            "general_disclaimer": "ℹ️ Esta asistencia es informativa y no reemplaza la consulta médica profesional."
        }
    
    async def create_session(self, user_context: Optional[Dict] = None) -> str:
        """
        Create a new conversation session
        
        Args:
            user_context: Optional user context (location, preferences, etc.)
            
        Returns:
            Session ID
        """
        if not self.session_manager.redis_client:
            self.session_manager.connect()
        
        session_id = self.session_manager.create_session(user_context)
        
        # Add initial system message
        memory = ConversationMemory(session_id)
        await memory.add_message(
            role="system",
            content=self.system_prompt,
            metadata={"type": "system_initialization"}
        )
        
        logger.info(f"✅ Created new session: {session_id}")
        return session_id
    
    async def process_message(self, session_id: str, user_message: str, stream: bool = False) -> Dict[str, Any]:
        """
        Process user message and generate agent response
        
        Args:
            session_id: Session identifier
            user_message: User's message
            stream: Whether to stream the response
            
        Returns:
            Response dictionary with agent's reply and metadata
        """
        start_time = datetime.now()
        
        try:
            # SAFETY CHECK: Detect medication recommendation requests early
            safety_check = self._check_medication_recommendation_request(user_message)
            if safety_check:
                # Add user message to memory
                memory = ConversationMemory(session_id)
                await memory.add_message(
                    role="user", 
                    content=user_message,
                    metadata={"timestamp": datetime.now().isoformat()}
                )
                
                # Add safety response to memory
                await memory.add_message(
                    role="assistant",
                    content=safety_check['response'],
                    metadata={"safety_restriction": True, "source": "medication_recommendation_block"}
                )
                
                return {
                    "response": safety_check['response'],
                    "session_id": session_id,
                    "tools_used": [],
                    "response_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
                    "safety_triggered": True,
                    "restriction_type": "medication_recommendation",
                    "success": True  # ✅ Esto es crucial para que el frontend muestre el mensaje
                }
            
            # Get conversation memory
            memory = ConversationMemory(session_id)
            
            # Add user message to memory
            await memory.add_message(
                role="user",
                content=user_message,
                metadata={"timestamp": start_time.isoformat()}
            )
            
            # Get conversation context for LLM
            conversation_history = await memory.get_context_for_llm()
            
            # Get available tools
            tools = self.tool_registry.get_openai_functions()
            
            # Generate response
            if stream:
                return await self._process_streaming_response(memory, conversation_history, tools)
            else:
                return await self._process_standard_response(memory, conversation_history, tools, start_time)
        
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
            return {
                "success": False,
                "error": f"Error procesando mensaje: {str(e)}",
                "session_id": session_id,
                "response_time_ms": (datetime.now() - start_time).total_seconds() * 1000
            }
    
    async def _process_standard_response(self, memory: ConversationMemory, conversation_history: List[Dict], tools: List[Dict], start_time: datetime) -> Dict[str, Any]:
        """Process standard (non-streaming) response"""
        try:
            # Call OpenAI with function calling
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=conversation_history,
                tools=tools,
                tool_choice="auto",
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            message = response.choices[0].message
            
            # Handle tool calls if any
            if message.tool_calls:
                return await self._handle_tool_calls(memory, message, start_time)
            else:
                # Direct response without tools
                agent_response = message.content
                
                # Add safety disclaimers if needed
                agent_response = self._add_safety_disclaimers(agent_response)
                
                # Add assistant message to memory
                await memory.add_message(
                    role="assistant",
                    content=agent_response,
                    metadata={"model": self.model, "direct_response": True}
                )
                
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return {
                    "success": True,
                    "response": agent_response,
                    "session_id": memory.session_id,
                    "response_time_ms": execution_time,
                    "tools_used": [],
                    "model": self.model
                }
        
        except Exception as e:
            logger.error(f"❌ OpenAI API error: {e}")
            raise
    
    async def _handle_tool_calls(self, memory: ConversationMemory, message, start_time: datetime) -> Dict[str, Any]:
        """Handle function/tool calls from the LLM"""
        tools_used = []
        tool_results = []
        
        # Execute each tool call
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            
            logger.info(f"🔧 Executing tool: {tool_name} with args: {tool_args}")
            
            # Execute tool
            tool_result = await self.tool_registry.execute_tool(tool_name, **tool_args)
            
            # Log tool usage
            await memory.log_tool_usage(tool_name, tool_args, tool_result)
            
            tools_used.append({
                "tool": tool_name,
                "args": tool_args,
                "success": tool_result.get("success", False),
                "execution_time_ms": tool_result.get("execution_time_ms", 0)
            })
            
            tool_results.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": tool_name,
                "content": json.dumps(tool_result)
            })
        
        # Get final response from LLM with tool results
        conversation_with_tools = await memory.get_context_for_llm()
        conversation_with_tools.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                } for tc in message.tool_calls
            ]
        })
        conversation_with_tools.extend(tool_results)
        
        # Get final response
        final_response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=conversation_with_tools,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        agent_response = final_response.choices[0].message.content
        
        # Add safety disclaimers
        agent_response = self._add_safety_disclaimers(agent_response)
        
        # Add assistant message to memory
        await memory.add_message(
            role="assistant",
            content=agent_response,
            tool_calls=[{
                "tool": tc["tool"],
                "args": tc["args"],
                "success": tc["success"]
            } for tc in tools_used],
            metadata={"model": self.model, "tools_executed": len(tools_used)}
        )
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Parse tool results to include raw data for frontend
        parsed_tool_results = []
        for tool_used in tools_used:
            # Find the corresponding tool result
            for tool_result in tool_results:
                if tool_result["name"] == tool_used["tool"]:
                    try:
                        tool_data = json.loads(tool_result["content"])
                        parsed_tool_results.append({
                            "tool": tool_used["tool"],
                            "success": tool_used["success"],
                            "data": tool_data.get("data", {}) if tool_data.get("success") else {},
                            "execution_time_ms": tool_used["execution_time_ms"]
                        })
                    except (json.JSONDecodeError, KeyError):
                        # Fallback if parsing fails
                        parsed_tool_results.append({
                            "tool": tool_used["tool"],
                            "success": tool_used["success"],
                            "data": {},
                            "execution_time_ms": tool_used["execution_time_ms"]
                        })
                    break
        
        return {
            "success": True,
            "response": agent_response,
            "session_id": memory.session_id,
            "response_time_ms": execution_time,
            "tools_used": [tool["tool"] for tool in tools_used],  # Extract just tool names
            "tool_results": parsed_tool_results,  # Include full tool results for frontend
            "model": self.model
        }
    
    def _check_medication_recommendation_request(self, user_message: str) -> Optional[Dict[str, Any]]:
        """
        Check if user is asking for medication recommendations and block with safety response
        
        Args:
            user_message: The user's input message
            
        Returns:
            Safety response dict if request should be blocked, None otherwise
        """
        query_lower = user_message.lower().strip()
        
        # Patterns that indicate medication recommendation requests
        recommendation_patterns = [
            'qué me recomiendas', 'qué recomiendan', 'qué recomienda',
            'qué tomar', 'qué tomo', 'qué puedo tomar',
            'me duele', 'tengo dolor', 'siento dolor',
            'para el dolor', 'para la', 'para mi',
            'necesito algo para', 'algo bueno para', 'algo para',
            'medicamento para', 'medicina para', 'pastilla para',
            'remedio para', 'que sirve para', 'sirve para el',
            'me recomiendas para', 'recomiendan para',
            'tengo', 'siento', 'me siento'
        ]
        
        # Symptom/condition keywords that when combined with recommendation patterns are problematic
        symptom_keywords = [
            'dolor', 'duele', 'cabeza', 'estómago', 'espalda', 'garganta',
            'fiebre', 'gripe', 'tos', 'resfrio', 'resfriado', 'alergia',
            'malestar', 'náusea', 'vómito', 'diarrea', 'estreñimiento',
            'infección', 'inflamación', 'hinchazón', 'presión', 'ansiedad',
            'estrés', 'insomnio', 'acidez', 'gastritis', 'artritis'
        ]
        
        # Check if message contains recommendation request patterns
        has_recommendation_request = any(pattern in query_lower for pattern in recommendation_patterns)
        has_symptom = any(symptom in query_lower for symptom in symptom_keywords)
        
        # Block if user is asking for medication recommendations for symptoms/conditions
        if has_recommendation_request and has_symptom:
            return {
                'response': (
                    "🏥 **IMPORTANTE**: No puedo recomendar medicamentos específicos para síntomas de salud. "
                    "Para cualquier molestia o síntoma, es fundamental consultar con un farmacéutico "
                    "o médico quien puede evaluar tu situación particular y recomendar el tratamiento "
                    "más adecuado y seguro.\n\n"
                    "💊 **¿Necesitas atención profesional?** Te puedo ayudar a encontrar farmacias "
                    "cercanas donde un profesional podrá atenderte adecuadamente.\n\n"
                    "¿Te gustaría que busque farmacias de turno en tu zona?"
                ),
                'blocked': True
            }
        
        # Also block direct symptom statements that imply need for medication
        direct_symptom_patterns = [
            'me duele la cabeza', 'dolor de cabeza', 'tengo fiebre',
            'estoy enfermo', 'me siento mal', 'tengo gripe',
            'me duele el estómago', 'dolor de estómago'
        ]
        
        if any(pattern in query_lower for pattern in direct_symptom_patterns):
            return {
                'response': (
                    "🏥 **Te ayudo a encontrar atención profesional**: Si tienes síntomas de salud, "
                    "es importante que consultes con un farmacéutico o médico quien puede evaluar "
                    "tu situación y recomendar el mejor tratamiento.\n\n"
                    "💊 Puedo ayudarte a encontrar farmacias cercanas donde un profesional "
                    "podrá atenderte adecuadamente.\n\n"
                    "¿En qué comuna te encuentras para buscar farmacias de turno?"
                ),
                'blocked': True
            }
        
        return None

    def _add_safety_disclaimers(self, response: str) -> str:
        """Add appropriate safety disclaimers to response"""
        # Check if response contains medication information
        medication_keywords = ["medicamento", "fármaco", "droga", "pastilla", "medicina", "principio activo", "dosis"]
        medical_keywords = ["síntoma", "enfermedad", "dolor", "tratamiento", "diagnóstico"]
        
        response_lower = response.lower()
        
        # Add medication disclaimer
        if any(keyword in response_lower for keyword in medication_keywords):
            if not "⚠️" in response and not "disclaimer" in response_lower:
                response += f"\n\n{self.safety_disclaimers['medication_info']}"
        
        # Add medical consultation disclaimer  
        if any(keyword in response_lower for keyword in medical_keywords):
            if not "🏥" in response:
                response += f"\n\n{self.safety_disclaimers['medical_query']}"
        
        return response
    
    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get conversation history and session summary"""
        try:
            memory = ConversationMemory(session_id)
            
            # Get conversation history
            conversation = await memory.get_conversation_history()
            
            # Get summary statistics
            summary = await memory.get_conversation_summary()
            
            return {
                "success": True,
                "session_id": session_id,
                "conversation": conversation,
                "summary": summary,
                "agent_model": self.model,
                "safety_mode": self.safety_mode,
                "tools_available": len(self.tool_registry.get_all_tools())
            }
        
        except Exception as e:
            logger.error(f"❌ Error getting session summary: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete conversation session"""
        try:
            return self.session_manager.delete_session(session_id)
        except Exception as e:
            logger.error(f"❌ Error deleting session: {e}")
            return False


# Global agent instance
spanish_pharmacy_agent = SpanishPharmacyAgent()

def get_agent() -> SpanishPharmacyAgent:
    """Get the global agent instance"""
    return spanish_pharmacy_agent
