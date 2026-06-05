import unittest
import sys
import os

# Add src directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from guardrails import process_guardrails

class TestIntentGuardrails(unittest.TestCase):
    def setUp(self):
        # 10 Factual Queries
        self.factual_queries = [
            "What is the NAV of HDFC Defence Fund?",
            "Who manages the HDFC Balanced Advantage Fund?",
            "What is the expense ratio for HDFC Liquid Fund?",
            "List the top holdings of HDFC Gold ETF.",
            "What is the minimum SIP amount for HDFC Multi Cap Fund?",
            "When was the fund launched?",
            "Does HDFC Infrastructure Fund have an exit load?",
            "Tell me the AUM of HDFC Sensex Index Fund.",
            "What sector does the HDFC Pharma fund invest in?",
            "Is there a lock-in period?"
        ]
        
        # 5 Advisory Queries
        self.advisory_queries = [
            "Should I invest my bonus in HDFC Defence Fund?",
            "Is it a good time to buy HDFC Gold ETF?",
            "Which fund will give me the best returns in 5 years?",
            "Can you recommend a safe fund for my retirement?",
            "Is the HDFC Liquid fund better than keeping money in a savings account?"
        ]
        
        # 5 Comparative Queries
        self.comparative_queries = [
            "How does HDFC Defence Fund compare to HDFC Pharma Fund?",
            "Which is better: HDFC Nifty 50 or HDFC Sensex Index Fund?",
            "Show me the difference between HDFC Liquid Fund and HDFC Ultra Short Term Fund.",
            "Which fund has a higher expense ratio, Gold ETF or Defence Fund?",
            "Compare the returns of HDFC Multi Cap and HDFC Large and Mid Cap."
        ]

    def test_factual_queries(self):
        print("\n--- Testing Factual Queries ---")
        for q in self.factual_queries:
            result = process_guardrails(q)
            print(f"[Factual] {q} -> {result['intent']}")
            self.assertTrue(result['passed'], f"Failed on: {q}")
            self.assertEqual(result['intent'], "Factual_Query")

    def test_advisory_queries(self):
        print("\n--- Testing Advisory Queries ---")
        for q in self.advisory_queries:
            result = process_guardrails(q)
            print(f"[Advisory] {q} -> {result['intent']}")
            self.assertFalse(result['passed'], f"Failed on: {q} - It incorrectly passed.")
            self.assertIn(result['intent'], ["Advisory_Query", "Comparative_Query"])

    def test_comparative_queries(self):
        print("\n--- Testing Comparative Queries ---")
        for q in self.comparative_queries:
            result = process_guardrails(q)
            print(f"[Comparative] {q} -> {result['intent']}")
            self.assertFalse(result['passed'], f"Failed on: {q} - It incorrectly passed.")
            self.assertIn(result['intent'], ["Advisory_Query", "Comparative_Query"])

if __name__ == "__main__":
    unittest.main()
