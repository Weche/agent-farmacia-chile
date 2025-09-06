#!/usr/bin/env python3
"""
BENCHMARK RÁPIDO GPT-4O MINI - VÍA API HTTP
==========================================

Este script evalúa el rendimiento de GPT-4o mini usando la API HTTP
para no interferir con el servidor en ejecución.

Genera un archivo de texto con resultados que puede ser procesado manualmente.
"""

import requests
import json
import time
from datetime import datetime
import os

class QuickBenchmark:
    """Benchmark rápido vía API HTTP"""
    
    def __init__(self, base_url="http://127.0.0.1:8004"):
        self.base_url = base_url
        self.session_id = None
        self.results = []
        
    def create_session(self):
        """Crear sesión para el chat"""
        try:
            response = requests.post(f"{self.base_url}/api/chat/session")
            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get('session_id')
                print(f"✅ Sesión creada: {self.session_id}")
                return True
        except Exception as e:
            print(f"❌ Error creando sesión: {e}")
        return False
    
    def send_message(self, message):
        """Enviar mensaje y medir tiempo"""
        if not self.session_id:
            return None
            
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat/message",
                json={"message": message, "session_id": self.session_id},
                timeout=20
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "reply": data.get("response", ""),
                    "response_time": response_time,
                    "status": "success"
                }
            else:
                return {
                    "reply": f"Error HTTP {response.status_code}",
                    "response_time": response_time,
                    "status": "error"
                }
                
        except requests.exceptions.Timeout:
            return {
                "reply": "Timeout - respuesta muy lenta",
                "response_time": 20.0,
                "status": "timeout"
            }
        except Exception as e:
            return {
                "reply": f"Error: {str(e)}",
                "response_time": 0,
                "status": "error"
            }
    
    def get_benchmark_questions(self):
        """Las 10 preguntas del benchmark"""
        return [
            {
                "id": 1,
                "question": "Necesito farmacias de turno en Las Condes",
                "category": "pharmacy_search",
                "expected_tools": ["search_farmacias"],
                "key_features": ["farmacia", "las condes", "turno", "dirección", "teléfono"]
            },
            {
                "id": 2,
                "question": "¿Dónde puedo comprar paracetamol en Providencia?",
                "category": "pharmacy_search",
                "expected_tools": ["search_farmacias"],
                "key_features": ["farmacia", "providencia", "dirección"]
            },
            {
                "id": 3,
                "question": "Busco información sobre el medicamento ibuprofeno",
                "category": "medication_search",
                "expected_tools": ["lookup_medicamento"],
                "key_features": ["ibuprofeno", "medicamento", "laboratorio"]
            },
            {
                "id": 4,
                "question": "¿Qué farmacias están abiertas ahora en Santiago Centro?",
                "category": "pharmacy_search",
                "expected_tools": ["search_farmacias"],
                "key_features": ["farmacia", "santiago", "abierta", "horario"]
            },
            {
                "id": 5,
                "question": "Dame la lista de todas las comunas disponibles",
                "category": "commune_info",
                "expected_tools": ["get_communes"],
                "key_features": ["comuna", "disponible", "lista"]
            },
            {
                "id": 6,
                "question": "Estoy en las coordenadas -33.4372, -70.6506, ¿hay farmacias cerca?",
                "category": "location_search",
                "expected_tools": ["search_farmacias_nearby"],
                "key_features": ["farmacia", "cerca", "coordenadas", "ubicación"]
            },
            {
                "id": 7,
                "question": "¿Tienen farmacias Cruz Verde en Maipú?",
                "category": "pharmacy_search",
                "expected_tools": ["search_farmacias"],
                "key_features": ["farmacia", "maipú", "cruz verde"]
            },
            {
                "id": 8,
                "question": "Necesito farmacias que vendan medicamentos controlados en Ñuñoa",
                "category": "pharmacy_search",
                "expected_tools": ["search_farmacias"],
                "key_features": ["farmacia", "ñuñoa", "controlado", "medicamento"]
            },
            {
                "id": 9,
                "question": "¿Cuáles son los horarios de farmacias en fines de semana en Valparaíso?",
                "category": "pharmacy_search",
                "expected_tools": ["search_farmacias"],
                "key_features": ["farmacia", "valparaíso", "horario", "fin de semana"]
            },
            {
                "id": 10,
                "question": "Busco medicamentos para el dolor de cabeza, ¿qué opciones hay?",
                "category": "medication_safety",
                "expected_tools": ["lookup_medicamento"],
                "key_features": ["medicamento", "dolor", "cabeza", "consulte", "profesional"]
            }
        ]
    
    def evaluate_response(self, question_data, response_data):
        """Evaluar una respuesta"""
        reply = response_data.get("reply", "").lower()
        response_time = response_data.get("response_time", 0)
        status = response_data.get("status", "error")
        
        # Verificar características clave
        features_found = []
        for feature in question_data["key_features"]:
            if feature.lower() in reply:
                features_found.append(feature)
        
        feature_score = len(features_found) / len(question_data["key_features"])
        
        # Evaluar tiempo
        time_score = 1.0
        if response_time > 10:
            time_score = 0.7
        elif response_time > 15:
            time_score = 0.3
        
        # Evaluar longitud de respuesta
        length_score = 1.0 if 50 < len(reply) < 1500 else 0.5
        
        # Puntaje final
        if status != "success":
            final_score = 0.0
        else:
            final_score = (feature_score * 0.6) + (time_score * 0.2) + (length_score * 0.2)
        
        return {
            "score": final_score,
            "features_found": features_found,
            "feature_score": feature_score,
            "time_score": time_score,
            "length_score": length_score,
            "status": status,
            "passed": final_score >= 0.7
        }
    
    def run_benchmark(self):
        """Ejecutar benchmark completo"""
        print("🚀 INICIANDO BENCHMARK RÁPIDO GPT-4O MINI")
        print("=" * 50)
        
        # Crear sesión
        if not self.create_session():
            print("❌ No se pudo crear sesión")
            return
        
        questions = self.get_benchmark_questions()
        start_time = time.time()
        
        print(f"\n📝 Ejecutando {len(questions)} preguntas...\n")
        
        # Ejecutar cada pregunta
        for question_data in questions:
            print(f"⏳ Pregunta {question_data['id']}: {question_data['question'][:50]}...")
            
            # Enviar pregunta
            response = self.send_message(question_data["question"])
            
            if response:
                # Evaluar respuesta
                evaluation = self.evaluate_response(question_data, response)
                
                # Guardar resultado
                self.results.append({
                    "question_data": question_data,
                    "response": response,
                    "evaluation": evaluation
                })
                
                # Mostrar resultado inmediato
                status_icon = "✅" if evaluation["passed"] else "❌"
                print(f"   {status_icon} Score: {evaluation['score']:.2f} | Tiempo: {response['response_time']:.1f}s")
            else:
                print("   ❌ Sin respuesta")
            
            # Pausa entre preguntas
            time.sleep(0.5)
        
        total_time = time.time() - start_time
        
        # Generar reporte
        self.generate_report(total_time)
    
    def generate_report(self, total_time):
        """Generar reporte en archivo de texto"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_gpt4o_mini_results_{timestamp}.txt"
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        # Calcular estadísticas
        total_questions = len(self.results)
        passed = sum(1 for r in self.results if r["evaluation"]["passed"])
        success_rate = (passed / total_questions * 100) if total_questions > 0 else 0
        avg_time = sum(r["response"]["response_time"] for r in self.results) / total_questions
        avg_score = sum(r["evaluation"]["score"] for r in self.results) / total_questions
        
        # Escribir reporte
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("BENCHMARK GPT-4O MINI - RESULTADOS DETALLADOS\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Modelo: GPT-4o Mini\n")
            f.write(f"Total preguntas: {total_questions}\n")
            f.write(f"Preguntas exitosas: {passed}\n")
            f.write(f"Tasa de éxito: {success_rate:.1f}%\n")
            f.write(f"Tiempo promedio: {avg_time:.2f}s\n")
            f.write(f"Score promedio: {avg_score:.2f}\n")
            f.write(f"Tiempo total: {total_time:.1f}s\n\n")
            
            # Análisis por categorías
            categories = {}
            for result in self.results:
                cat = result["question_data"]["category"]
                if cat not in categories:
                    categories[cat] = {"total": 0, "passed": 0, "scores": []}
                categories[cat]["total"] += 1
                if result["evaluation"]["passed"]:
                    categories[cat]["passed"] += 1
                categories[cat]["scores"].append(result["evaluation"]["score"])
            
            f.write("ANÁLISIS POR CATEGORÍAS\n")
            f.write("-" * 30 + "\n")
            for cat, stats in categories.items():
                rate = (stats["passed"] / stats["total"]) * 100
                avg_cat_score = sum(stats["scores"]) / len(stats["scores"])
                f.write(f"{cat}:\n")
                f.write(f"  Éxito: {stats['passed']}/{stats['total']} ({rate:.1f}%)\n")
                f.write(f"  Score promedio: {avg_cat_score:.2f}\n\n")
            
            f.write("\nDETALLE DE CADA PREGUNTA\n")
            f.write("=" * 60 + "\n\n")
            
            # Detalles de cada pregunta
            for i, result in enumerate(self.results, 1):
                question = result["question_data"]
                response = result["response"]
                evaluation = result["evaluation"]
                
                f.write(f"PREGUNTA {i}\n")
                f.write(f"Texto: {question['question']}\n")
                f.write(f"Categoría: {question['category']}\n")
                f.write(f"Herramientas esperadas: {', '.join(question['expected_tools'])}\n")
                f.write(f"Características clave: {', '.join(question['key_features'])}\n\n")
                
                f.write("RESPUESTA:\n")
                f.write(f"Tiempo: {response['response_time']:.2f}s\n")
                f.write(f"Estado: {response['status']}\n")
                f.write(f"Texto: {response['reply'][:300]}{'...' if len(response['reply']) > 300 else ''}\n\n")
                
                f.write("EVALUACIÓN:\n")
                f.write(f"Score final: {evaluation['score']:.2f}\n")
                f.write(f"Resultado: {'✅ ÉXITO' if evaluation['passed'] else '❌ FALLO'}\n")
                f.write(f"Características encontradas: {', '.join(evaluation['features_found'])}\n")
                f.write(f"Score características: {evaluation['feature_score']:.2f}\n")
                f.write(f"Score tiempo: {evaluation['time_score']:.2f}\n")
                f.write(f"Score longitud: {evaluation['length_score']:.2f}\n")
                
                f.write("\n" + "-" * 60 + "\n\n")
        
        # Mostrar resumen en consola
        print("\n" + "=" * 50)
        print("📊 RESUMEN DEL BENCHMARK")
        print("=" * 50)
        print(f"✅ Éxito: {success_rate:.1f}% ({passed}/{total_questions})")
        print(f"⏱️  Tiempo promedio: {avg_time:.2f}s")
        print(f"🎯 Score promedio: {avg_score:.2f}")
        print(f"📄 Reporte: {filename}")
        
        # Análisis cualitativo
        if success_rate >= 80:
            print("🌟 EXCELENTE rendimiento")
        elif success_rate >= 70:
            print("👍 BUEN rendimiento")
        elif success_rate >= 60:
            print("⚠️  ACEPTABLE rendimiento")
        else:
            print("❌ BAJO rendimiento")

if __name__ == "__main__":
    benchmark = QuickBenchmark()
    benchmark.run_benchmark()
