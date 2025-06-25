import unittest
import sys
import os
import sqlite3
from unittest.mock import patch, MagicMock

# Add parent directory to path to import search module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from search import find_definition


class TestSearchIntegration(unittest.TestCase):
    """Integration tests for find_definition using real database and real LLM calls."""
    
    def setUp(self):
        """Set up test database path."""
        self.db_name = os.path.join(os.path.dirname(__file__), 'math_base.db')
        # Verify database exists
        self.assertTrue(os.path.exists(self.db_name), "Database file not found")
    
    def test_integration_with_real_llm_exact_match(self):
        """Integration test with real LLM for exact match (requires API key)."""
        # Skip if no API key available
        if not os.getenv("OPENROUTER_API_KEY"):
            self.skipTest("OPENROUTER_API_KEY not available for integration test")
        
        # Test exact match for infinite set
        term = "Бесконечное множество"
        definition = "Множество A называется бесконечным, если оно эквивалентно своей правильной части"
        
        result = find_definition(term, definition, self.db_name)
        self.assertEqual(result, 1, "Should find exact match with real LLM")
    
    def test_integration_with_real_llm_similar_match(self):
        """Integration test with real LLM for similar match (requires API key)."""
        # Skip if no API key available
        if not os.getenv("OPENROUTER_API_KEY"):
            self.skipTest("OPENROUTER_API_KEY not available for integration test")
        
        # Test with a more exact match that LLM should accept
        term = "Бесконечное множество"
        definition = "Множество эквивалентное своей собственной правильной части"
        
        result = find_definition(term, definition, self.db_name)
        self.assertEqual(result, 1, "Should find exact match with real LLM")
        
        # Alternative: test that it returns some valid result or None (both acceptable)
        # self.assertTrue(result is None or isinstance(result, int), "Should return valid result or None")
    
    def test_integration_with_real_llm_no_match(self):
        """Integration test with real LLM for no match (requires API key)."""
        # Skip if no API key available
        if not os.getenv("OPENROUTER_API_KEY"):
            self.skipTest("OPENROUTER_API_KEY not available for integration test")
        
        # Test completely different concept
        term = "Производная функции"
        definition = "Предел отношения приращения функции к приращению аргумента"
        
        result = find_definition(term, definition, self.db_name)
        self.assertIsNone(result, "Should not find match for different concept with real LLM")


class TestSearchManualVerification(unittest.TestCase):
    """Manual verification tests that print results for human inspection."""
    
    def setUp(self):
        """Set up test database path."""
        self.db_name = os.path.join(os.path.dirname(__file__), 'math_base.db')
    
    @patch('search.verify_with_llm')
    def test_manual_verify_top_candidates(self, mock_llm):
        """Manual test to inspect top TF-IDF candidates."""
        mock_llm.return_value = False  # Don't return matches, just inspect candidates
        
        # Get actual definitions from database for inspection
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT id, term_ru, definition_ru FROM definitions WHERE id IN (1, 2, 9, 10)")
        real_definitions = cursor.fetchall()
        conn.close()
        
        test_cases = [
            {
                "query_term": "Бесконечное множество",
                "query_def": "Множество равномощное своей собственной части",
                "expected_match": 1
            },
            {
                "query_term": "Произведение множеств",
                "query_def": "Множество всех упорядоченных пар элементов двух множеств",
                "expected_match": 2
            },
            {
                "query_term": "Инъективное отображение",
                "query_def": "Отображение при котором разные элементы переходят в разные образы",
                "expected_match": 9
            },
            {
                "query_term": "Сюръективная функция",
                "query_def": "Функция образ которой совпадает с областью значений",
                "expected_match": 10
            }
        ]
        
        print("\n" + "="*80)
        print("MANUAL VERIFICATION OF TF-IDF CANDIDATES")
        print("="*80)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\nTest Case {i}:")
            print(f"Query Term: {test_case['query_term']}")
            print(f"Query Definition: {test_case['query_def']}")
            print(f"Expected Match ID: {test_case['expected_match']}")
            
            # This will show us what TF-IDF candidates are found
            result = find_definition(
                test_case['query_term'], 
                test_case['query_def'], 
                self.db_name
            )
            
            # Print the call arguments to see what candidates were considered
            if mock_llm.call_args_list:
                last_call = mock_llm.call_args_list[-1]
                args = last_call[0]
                print(f"LLM was called with candidate:")
                print(f"  Candidate Term: {args[2]}")
                print(f"  Candidate Definition: {args[3][:100]}...")
            
            print("-" * 40)
        
        print("\nNote: Set mock_llm.return_value = True to test actual matching")
        print("="*80)


if __name__ == '__main__':
    # Run specific test suites
    unittest.main(verbosity=2)
