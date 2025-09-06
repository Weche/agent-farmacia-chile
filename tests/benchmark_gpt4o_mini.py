#!/usr/bin/env python3
"""
BENCHMARK GPT-4O MINI - EVALUACIÓN COMPARATIVA
==============================================

Este script evalúa específicamente el rendimiento de GPT-4o mini con 10 preguntas
diseñadas para medir:
- Precisión en selección de herramientas
- Calidad de respuestas vs GPT-4o
- Manejo de consultas típicas chilenas
- Consistencia en formato de respuestas
- Velocidad de procesamiento

Compara resultados con benchmark anterior de GPT-4o para análisis de regresión.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from app.agents.spanish_agent import SpanishPharmacyAgent

class GPT4oMiniBenchmark:
    """Benchmark específico para GPT-4o mini"""
    
    def __init__(self):
        self.agent = None
        self.session_id = None
        self.results = []
        self.start_time = None
        self.model_name = "gpt-4o-mini"
        
    async def initialize(self):
        """Inicializar el agente"""
        try:
            self.agent = SpanishPharmacyAgent()
            self.session_id = await self.agent.create_session()
            print(f"✅ Agente inicializado correctamente con modelo: {self.agent.model}")
            return True
        except Exception as e:
            print(f"❌ Error inicializando agente: {e}")
            return False
    
    async def evaluate_question(self, question: str, category: str, 
                              expected_tools: List[str], expected_features: List[str]) -> Dict[str, Any]:
        """Evaluar una pregunta específica"""
        print(f"\n🔍 Evaluando: {question}")
        print(f"   Categoría: {category}")
        print(f"   Herramientas esperadas: {expected_tools}")
        
        start_time = time.time()
        
        try:
            # Ejecutar la consulta
            result = await self.agent.process_message(question, self.session_id)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Extraer información del resultado
            reply = result.get('reply', '')
            tools_used = result.get('tools_used', [])
            
            # Evaluar resultado
            evaluation = self._evaluate_response(
                question, category, expected_tools, expected_features, 
                tools_used, reply, response_time
            )
            
            print(f"   ⏱️  Tiempo: {response_time:.2f}s")
            print(f"   🛠️  Herramientas usadas: {tools_used}")
            print(f"   ✅ Éxito: {evaluation['passed']}")
            if not evaluation['passed']:
                print(f"   ❌ Razón: {evaluation['reason']}")
                
            return {
                'question': question,
                'category': category,
                'expected_tools': expected_tools,
                'expected_features': expected_features,
                'tools_used': tools_used,
                'reply': reply,
                'response_time': response_time,
                'evaluation': evaluation,
                'model': self.model_name
            }
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return {
                'question': question,
                'category': category,
                'error': str(e),
                'evaluation': {'passed': False, 'reason': f'Error de ejecución: {str(e)}'}
            }
    
    def _evaluate_response(self, question: str, category: str, expected_tools: List[str], 
                          expected_features: List[str], tools_used: List[str], reply: str, 
                          response_time: float) -> Dict[str, Any]:
        """Evaluar la respuesta según criterios específicos"""
        
        # Verificar herramientas correctas
        tools_correct = any(tool in tools_used for tool in expected_tools) if expected_tools else True
        
        # Verificar características esperadas en la respuesta
        features_present = []
        for feature in expected_features:
            if feature.lower() in reply.lower():
                features_present.append(feature)
        
        features_correct = len(features_present) >= len(expected_features) * 0.7  # 70% de las características
        
        # Evaluar tiempo de respuesta (penalizar si es muy lento)
        time_acceptable = response_time < 15.0  # Máximo 15 segundos
        
        # Evaluar calidad de la respuesta
        quality_score = self._evaluate_response_quality(reply, category)
        
        # Resultado final
        passed = tools_correct and features_correct and time_acceptable and quality_score >= 0.7
        
        return {
            'passed': passed,
            'tools_correct': tools_correct,
            'features_correct': features_correct,
            'features_present': features_present,
            'time_acceptable': time_acceptable,
            'response_time': response_time,
            'quality_score': quality_score,
            'reason': self._generate_reason(tools_correct, features_correct, time_acceptable, quality_score)
        }
    
    def _evaluate_response_quality(self, reply: str, category: str) -> float:
        """Evaluar calidad de la respuesta (0.0 - 1.0)"""
        score = 0.0
        
        # Criterios básicos
        if len(reply) > 50:  # Respuesta no muy corta
            score += 0.2
        if len(reply) < 1000:  # Respuesta no muy larga
            score += 0.1
            
        # Criterios por categoría
        if category == "pharmacy_search":
            if any(word in reply.lower() for word in ["farmacia", "dirección", "teléfono"]):
                score += 0.3
            if any(word in reply.lower() for word in ["mapa", "google", "maps"]):
                score += 0.2
            if "horario" in reply.lower():
                score += 0.2
                
        elif category == "medication_search":
            if any(word in reply.lower() for word in ["medicamento", "laboratorio", "principio"]):
                score += 0.4
            if "consulte" in reply.lower():
                score += 0.3
                
        elif category == "commune_info":
            if "comuna" in reply.lower():
                score += 0.3
            if len(reply) > 100:  # Respuesta informativa
                score += 0.4
                
        return min(score, 1.0)
    
    def _generate_reason(self, tools_correct: bool, features_correct: bool, 
                        time_acceptable: bool, quality_score: float) -> str:
        """Generar razón del resultado"""
        reasons = []
        
        if not tools_correct:
            reasons.append("Herramientas incorrectas")
        if not features_correct:
            reasons.append("Características faltantes")
        if not time_acceptable:
            reasons.append("Tiempo excesivo")
        if quality_score < 0.7:
            reasons.append(f"Calidad baja ({quality_score:.2f})")
            
        if not reasons:
            return "Evaluación exitosa"
        else:
            return ", ".join(reasons)
    
    def get_test_questions(self) -> List[Dict[str, Any]]:
        """10 preguntas de benchmark para GPT-4o mini"""
        return [
            {
                "question": "Necesito farmacias de turno en Las Condes",
                "category": "pharmacy_search",
                "expected_tools": ["search_farmacias"],
                "expected_features": ["farmacia", "turno", "dirección", "teléfono"]
            },
            {
                "question": "¿Dónde puedo comprar paracetamol en Providencia?",
                "category": "pharmacy_search", 
                "expected_tools": ["search_farmacias"],
                "expected_features": ["farmacia", "providencia", "dirección"]
            },
            {
                "question": "Busco información sobre el medicamento ibuprofeno",
                "category": "medication_search",
                "expected_tools": ["lookup_medicamento"],
                "expected_features": ["ibuprofeno", "laboratorio", "principio activo"]
            },
            {
                "question": "¿Qué farmacias están abiertas ahora en Santiago Centro?",
                "category": "pharmacy_search",
                "expected_tools": ["search_farmacias"],
                "expected_features": ["farmacia", "santiago", "horario", "abierta"]
            },
            {
                "question": "Dame la lista de todas las comunas disponibles",
                "category": "commune_info",
                "expected_tools": ["get_communes"],
                "expected_features": ["comuna", "disponible"]
            },
            {
                "question": "Estoy en las coordenadas -33.4372, -70.6506, ¿hay farmacias cerca?",
                "category": "location_search",
                "expected_tools": ["search_farmacias_nearby"],
                "expected_features": ["farmacia", "cerca", "coordenadas"]
            },
            {
                "question": "¿Tienen farmacias Cruz Verde en Maipú?",
                "category": "pharmacy_search",
                "expected_tools": ["search_farmacias"],
                "expected_features": ["farmacia", "maipú", "cruz verde"]
            },
            {
                "question": "Necesito farmacias que vendan medicamentos controlados en Ñuñoa",
                "category": "pharmacy_search",
                "expected_tools": ["search_farmacias"],
                "expected_features": ["farmacia", "ñuñoa", "controlados"]
            },
            {
                "question": "¿Cuáles son los horarios de farmacias en fines de semana en Valparaíso?",
                "category": "pharmacy_search",
                "expected_tools": ["search_farmacias"],
                "expected_features": ["farmacia", "valparaíso", "horario", "fin de semana"]
            },
            {
                "question": "Busco medicamentos para el dolor de cabeza, ¿qué opciones hay?",
                "category": "medication_search",
                "expected_tools": ["lookup_medicamento", "get_medication_categories"],
                "expected_features": ["medicamento", "dolor", "cabeza", "consulte"]
            }
        ]
    
    async def run_benchmark(self):
        """Ejecutar el benchmark completo"""
        print("🚀 INICIANDO BENCHMARK GPT-4O MINI")
        print("=" * 50)
        
        if not await self.initialize():
            return
            
        self.start_time = time.time()
        questions = self.get_test_questions()
        
        # Ejecutar evaluaciones
        for i, test_case in enumerate(questions, 1):
            print(f"\n📝 PREGUNTA {i}/10")
            result = await self.evaluate_question(
                test_case["question"],
                test_case["category"],
                test_case["expected_tools"],
                test_case["expected_features"]
            )
            self.results.append(result)
            
            # Pausa entre preguntas
            await asyncio.sleep(1)
        
        # Generar reporte
        await self.generate_report()
    
    async def generate_report(self):
        """Generar reporte detallado"""
        total_time = time.time() - self.start_time
        
        # Estadísticas generales
        total_questions = len(self.results)
        successful = sum(1 for r in self.results if r.get('evaluation', {}).get('passed', False))
        success_rate = (successful / total_questions) * 100 if total_questions > 0 else 0
        
        avg_response_time = sum(r.get('response_time', 0) for r in self.results) / total_questions
        
        # Generar archivo de reporte
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"benchmark_gpt4o_mini_{timestamp}.txt"
        report_path = os.path.join(os.path.dirname(__file__), report_filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("BENCHMARK GPT-4O MINI - REPORTE DETALLADO\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Fecha: {datetime.now().strftime('%d de %B, %Y - %H:%M:%S')}\n")
            f.write(f"Modelo: {self.model_name}\n")
            f.write(f"Total preguntas: {total_questions}\n")
            f.write(f"Exitosas: {successful}\n")
            f.write(f"Tasa de éxito: {success_rate:.1f}%\n")
            f.write(f"Tiempo promedio: {avg_response_time:.2f}s\n")
            f.write(f"Tiempo total: {total_time:.1f}s\n\n")
            
            # Análisis por categorías
            categories = {}
            for result in self.results:
                cat = result.get('category', 'unknown')
                if cat not in categories:
                    categories[cat] = {'total': 0, 'passed': 0}
                categories[cat]['total'] += 1
                if result.get('evaluation', {}).get('passed', False):
                    categories[cat]['passed'] += 1
            
            f.write("ANÁLISIS POR CATEGORÍAS\n")
            f.write("-" * 30 + "\n")
            for cat, stats in categories.items():
                rate = (stats['passed'] / stats['total']) * 100
                f.write(f"{cat}: {stats['passed']}/{stats['total']} ({rate:.1f}%)\n")
            
            f.write("\nDETALLE DE EVALUACIONES\n")
            f.write("-" * 30 + "\n\n")
            
            for i, result in enumerate(self.results, 1):
                f.write(f"PREGUNTA {i}: {result.get('question', 'N/A')}\n")
                f.write(f"Categoría: {result.get('category', 'N/A')}\n")
                f.write(f"Herramientas usadas: {result.get('tools_used', [])}\n")
                f.write(f"Tiempo: {result.get('response_time', 0):.2f}s\n")
                
                eval_result = result.get('evaluation', {})
                f.write(f"Resultado: {'✅ ÉXITO' if eval_result.get('passed', False) else '❌ FALLO'}\n")
                f.write(f"Razón: {eval_result.get('reason', 'N/A')}\n")
                
                if 'reply' in result:
                    f.write(f"Respuesta: {result['reply'][:200]}{'...' if len(result['reply']) > 200 else ''}\n")
                
                f.write("\n" + "-" * 50 + "\n\n")
        
        # Mostrar resumen en consola
        print("\n" + "=" * 50)
        print("🎯 RESUMEN DEL BENCHMARK")
        print("=" * 50)
        print(f"✅ Tasa de éxito: {success_rate:.1f}% ({successful}/{total_questions})")
        print(f"⏱️  Tiempo promedio: {avg_response_time:.2f}s")
        print(f"📄 Reporte guardado: {report_filename}")
        
        # Análisis comparativo
        print("\n📊 ANÁLISIS POR CATEGORÍAS:")
        for cat, stats in categories.items():
            rate = (stats['passed'] / stats['total']) * 100
            print(f"   {cat}: {rate:.1f}% ({stats['passed']}/{stats['total']})")
        
        if success_rate >= 80:
            print("🌟 EXCELENTE rendimiento con GPT-4o mini")
        elif success_rate >= 70:
            print("👍 BUENO rendimiento con GPT-4o mini")
        elif success_rate >= 60:
            print("⚠️  ACEPTABLE rendimiento con GPT-4o mini")
        else:
            print("❌ BAJO rendimiento con GPT-4o mini")

if __name__ == "__main__":
    benchmark = GPT4oMiniBenchmark()
    asyncio.run(benchmark.run_benchmark())
