# test_vademecum_medicamentos.py
"""
🧪 Test Suite for Vademecum Medication System
==============================================

This test file verifies the medication search and vademecum functionality
of the pharmacy finder system.

Usage:
    python test_vademecum_medicamentos.py

Features tested:
- Medication search by name
- Medication information retrieval
- Vademecum data validation
- API endpoint functionality
- AI agent medication queries
"""

import requests
import json
import time
from datetime import datetime
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class VademecumTester:
    """Test class for medication vademecum functionality"""

    def __init__(self, base_url="http://127.0.0.1:8002"):
        self.base_url = base_url
        self.session_id = None
        self.test_results = []

    def log_test(self, test_name, success, message="", data=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if data:
            print(f"   📊 Data: {data}")
        return success

    def test_api_health(self):
        """Test basic API connectivity"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            return self.log_test(
                "API Health Check",
                response.status_code == 200,
                f"Status: {response.status_code}",
                {"response_time": response.elapsed.total_seconds()}
            )
        except Exception as e:
            return self.log_test("API Health Check", False, str(e))

    def test_medicamentos_endpoint(self):
        """Test the medicamentos API endpoint"""
        try:
            response = requests.get(f"{self.base_url}/medicamentos", timeout=10)
            success = response.status_code == 200

            if success:
                data = response.json()
                total_meds = len(data) if isinstance(data, list) else data.get('total', 0)
                return self.log_test(
                    "Medicamentos Endpoint",
                    True,
                    f"Retrieved {total_meds} medications",
                    {"total_medicamentos": total_meds, "status": response.status_code}
                )
            else:
                return self.log_test(
                    "Medicamentos Endpoint",
                    False,
                    f"HTTP {response.status_code}",
                    {"status": response.status_code}
                )
        except Exception as e:
            return self.log_test("Medicamentos Endpoint", False, str(e))

    def test_chat_session_creation(self):
        """Test creating a new chat session"""
        try:
            payload = {"message": "Hola, soy un test", "session_id": None}
            response = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get('session_id')
                return self.log_test(
                    "Chat Session Creation",
                    bool(self.session_id),
                    f"Session ID: {self.session_id}",
                    {"session_id": self.session_id}
                )
            else:
                return self.log_test(
                    "Chat Session Creation",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
        except Exception as e:
            return self.log_test("Chat Session Creation", False, str(e))

    def test_medication_search_queries(self):
        """Test various medication search queries"""
        test_queries = [
            "información sobre aspirina",
            "qué contiene el ibuprofeno",
            "dosis de paracetamol",
            "medicamentos para dolor de cabeza",
            "información sobre amoxicilina",
            "qué es el omeprazol",
            "medicamentos para hipertensión",
            "información sobre vitamina C"
        ]

        results = []
        for query in test_queries:
            try:
                payload = {"message": query, "session_id": self.session_id}
                response = requests.post(
                    f"{self.base_url}/chat",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=20
                )

                if response.status_code == 200:
                    data = response.json()
                    reply = data.get('reply', '')
                    tools_used = data.get('tools_used', [])

                    # Check if medication-related tools were used
                    med_tools = [tool for tool in tools_used if 'medicamento' in tool.lower()]

                    result = {
                        "query": query,
                        "success": True,
                        "reply_length": len(reply),
                        "tools_used": tools_used,
                        "med_tools_used": med_tools,
                        "has_med_info": len(med_tools) > 0 or 'medicamento' in reply.lower()
                    }
                else:
                    result = {
                        "query": query,
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "reply_length": 0
                    }

                results.append(result)
                self.log_test(
                    f"Medication Query: '{query[:30]}...'",
                    result["success"],
                    f"Reply: {result['reply_length']} chars, Tools: {len(result.get('tools_used', []))}",
                    result
                )

                # Small delay between requests
                time.sleep(1)

            except Exception as e:
                results.append({
                    "query": query,
                    "success": False,
                    "error": str(e)
                })
                self.log_test(f"Medication Query: '{query[:30]}...'", False, str(e))

        # Summary of medication queries
        successful_queries = [r for r in results if r["success"]]
        med_related_queries = [r for r in results if r.get("has_med_info", False)]

        return self.log_test(
            "Medication Queries Summary",
            len(successful_queries) > 0,
            f"{len(successful_queries)}/{len(test_queries)} successful, {len(med_related_queries)} medication-related",
            {
                "total_queries": len(test_queries),
                "successful": len(successful_queries),
                "medication_related": len(med_related_queries)
            }
        )

    def test_specific_medications(self):
        """Test specific medication information retrieval"""
        medications_to_test = [
            "aspirina",
            "ibuprofeno",
            "paracetamol",
            "amoxicilina",
            "omeprazol",
            "losartan",
            "metformina",
            "simvastatina"
        ]

        results = []
        for med in medications_to_test:
            try:
                query = f"información sobre {med}"
                payload = {"message": query, "session_id": self.session_id}

                response = requests.post(
                    f"{self.base_url}/chat",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=20
                )

                if response.status_code == 200:
                    data = response.json()
                    reply = data.get('reply', '').lower()

                    # Check if the reply contains medication information
                    contains_med_name = med.lower() in reply
                    contains_dosage = any(word in reply for word in ['dosis', 'mg', 'ml', 'tabletas', 'cápsulas'])
                    contains_indications = any(word in reply for word in ['para', 'tratamiento', 'indicado'])

                    result = {
                        "medication": med,
                        "success": True,
                        "contains_name": contains_med_name,
                        "contains_dosage": contains_dosage,
                        "contains_indications": contains_indications,
                        "reply_length": len(reply)
                    }
                else:
                    result = {
                        "medication": med,
                        "success": False,
                        "error": f"HTTP {response.status_code}"
                    }

                results.append(result)
                self.log_test(
                    f"Specific Med: {med}",
                    result["success"],
                    f"Name: {result.get('contains_name')}, Dosage: {result.get('contains_dosage')}, Indications: {result.get('contains_indications')}",
                    result
                )

                time.sleep(1.5)  # Longer delay for specific medication queries

            except Exception as e:
                results.append({
                    "medication": med,
                    "success": False,
                    "error": str(e)
                })
                self.log_test(f"Specific Med: {med}", False, str(e))

        # Summary
        successful_meds = [r for r in results if r["success"]]
        meds_with_info = [r for r in results if r.get("contains_name", False)]

        return self.log_test(
            "Specific Medications Summary",
            len(successful_meds) > 0,
            f"{len(successful_meds)}/{len(medications_to_test)} successful, {len(meds_with_info)} with medication info",
            {
                "total_tested": len(medications_to_test),
                "successful": len(successful_meds),
                "with_info": len(meds_with_info)
            }
        )

    def test_vademecum_data_quality(self):
        """Test the quality and completeness of vademecum data"""
        try:
            # Get all medications
            response = requests.get(f"{self.base_url}/medicamentos", timeout=10)

            if response.status_code == 200:
                medications = response.json()

                if isinstance(medications, list) and len(medications) > 0:
                    # Analyze data quality
                    total_meds = len(medications)
                    meds_with_name = sum(1 for m in medications if m.get('nombre'))
                    meds_with_description = sum(1 for m in medications if m.get('descripcion'))
                    meds_with_indications = sum(1 for m in medications if m.get('indicaciones'))
                    meds_with_dosage = sum(1 for m in medications if m.get('dosis') or m.get('dosage'))

                    quality_score = (meds_with_name + meds_with_description + meds_with_indications + meds_with_dosage) / (total_meds * 4) * 100

                    return self.log_test(
                        "Vademecum Data Quality",
                        quality_score > 50,  # At least 50% completeness
                        ".1f",
                        {
                            "total_medicamentos": total_meds,
                            "with_name": meds_with_name,
                            "with_description": meds_with_description,
                            "with_indications": meds_with_indications,
                            "with_dosage": meds_with_dosage,
                            "quality_score": round(quality_score, 1)
                        }
                    )
                else:
                    return self.log_test("Vademecum Data Quality", False, "No medication data found")
            else:
                return self.log_test("Vademecum Data Quality", False, f"HTTP {response.status_code}")

        except Exception as e:
            return self.log_test("Vademecum Data Quality", False, str(e))

    def generate_report(self):
        """Generate a comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests

        print("\n" + "="*60)
        print("📋 VADEMECUM TEST REPORT")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(".1f")

        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['message']}")

        print("\n✅ PASSED TESTS:")
        for result in self.test_results:
            if result["success"]:
                print(f"   • {result['test']}: {result['message']}")

        # Save detailed results to file
        report_file = f"vademecum_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)

        print(f"\n📄 Detailed report saved to: {report_file}")

        return passed_tests, total_tests

    def run_all_tests(self):
        """Run the complete test suite"""
        print("🧪 Starting Vademecum Medication Tests")
        print("="*50)

        # Basic connectivity tests
        self.test_api_health()
        self.test_medicamentos_endpoint()

        # Chat and AI functionality tests
        self.test_chat_session_creation()

        # Medication-specific tests
        self.test_medication_search_queries()
        self.test_specific_medications()
        self.test_vademecum_data_quality()

        # Generate final report
        return self.generate_report()


def main():
    """Main test execution"""
    print("💊 Vademecum Medication System Tester")
    print("=====================================")

    # Initialize tester
    tester = VademecumTester()

    # Run all tests
    passed, total = tester.run_all_tests()

    # Exit with appropriate code
    if passed == total:
        print("\n🎉 All tests passed! Vademecum system is working correctly.")
        sys.exit(0)
    else:
        print(f"\n⚠️ {total - passed} tests failed. Check the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
