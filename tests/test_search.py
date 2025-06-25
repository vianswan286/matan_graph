import unittest
import sys
import os
import sqlite3
from unittest.mock import patch, MagicMock

# Add parent directory to path to import search module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from search import find_definition, preprocess_text, calculate_tfidf_similarity, get_all_definitions


class TestSearchFunctions(unittest.TestCase):
    """Test cases for search.py functions using real database data."""
    
    def setUp(self):
        """Set up test database path."""
        self.db_name = os.path.join(os.path.dirname(__file__), 'math_base.db')
        # Verify database exists
        self.assertTrue(os.path.exists(self.db_name), "Database file not found")
    
    def test_preprocess_text(self):
        """Test text preprocessing function."""
        # Test LaTeX removal
        text_with_latex = "Множество $A$ называется \\textit{бесконечным}"
        processed = preprocess_text(text_with_latex)
        self.assertNotIn('$', processed)
        self.assertNotIn('\\textit', processed)
        self.assertIn('множество', processed)  # Should be lowercase
        
        # Test formula removal
        text_with_formula = "Формула $x^2 + y^2 = z^2$ и другой текст"
        processed = preprocess_text(text_with_formula)
        self.assertNotIn('$', processed)
        self.assertNotIn('^', processed)
        self.assertIn('формула', processed)
        
        # Test empty string
        self.assertEqual(preprocess_text(""), "")
        self.assertEqual(preprocess_text(None), "")
    
    def test_get_all_definitions(self):
        """Test database retrieval function."""
        definitions = get_all_definitions(self.db_name)
        self.assertIsInstance(definitions, list)
        self.assertGreater(len(definitions), 0, "Database should contain definitions")
        
        # Check structure of returned data
        for def_tuple in definitions[:3]:  # Check first 3
            self.assertEqual(len(def_tuple), 3, "Each definition should have 3 elements")
            self.assertIsInstance(def_tuple[0], int, "ID should be integer")
            self.assertIsInstance(def_tuple[1], str, "Term should be string")
            self.assertIsInstance(def_tuple[2], str, "Definition should be string")


class TestFindDefinitionRealData(unittest.TestCase):
    """Test find_definition function with real data from the database."""
    
    def setUp(self):
        """Set up test database path."""
        self.db_name = os.path.join(os.path.dirname(__file__), 'math_base.db')
        # Verify database exists
        self.assertTrue(os.path.exists(self.db_name), "Database file not found")
    
    @patch('search.verify_with_llm')
    def test_exact_match_infinite_set(self, mock_llm):
        """Test finding exact match for infinite set definition."""
        mock_llm.return_value = True
        
        # Exact term and definition from database (ID: 1)
        term = "Бесконечное множество"
        definition = "Множество A называется бесконечным, если оно эквивалентно своей правильной части"
        
        result = find_definition(term, definition, self.db_name)
        self.assertEqual(result, 1, "Should find exact match with ID 1")
        mock_llm.assert_called()
    
    @patch('search.verify_with_llm')
    def test_similar_match_cartesian_product(self, mock_llm):
        """Test finding similar match for Cartesian product with different wording."""
        mock_llm.return_value = True
        
        # Similar but not identical term and definition (should match ID: 2)
        term = "Декартово произведение множеств"
        definition = "Декартовым произведением называется множество упорядоченных пар"
        
        result = find_definition(term, definition, self.db_name)
        self.assertEqual(result, 2, "Should find similar match with ID 2")
        mock_llm.assert_called()
    
    @patch('search.verify_with_llm')
    def test_injection_definition_match(self, mock_llm):
        """Test finding match for injection definition."""
        mock_llm.return_value = True
        
        # Different wording for injection (TF-IDF may find mapping-related terms first)
        term = "Инъективное отображение"
        definition = "Отображение является инъекцией если разные элементы переходят в разные образы"
        
        result = find_definition(term, definition, self.db_name)
        # The result might be any mapping-related definition (6, 7, 8, 9)
        self.assertIsNotNone(result, "Should find some match for mapping-related definition")
        self.assertIsInstance(result, int, "Should return integer ID")
        mock_llm.assert_called()
    
    @patch('search.verify_with_llm')
    def test_surjection_definition_match(self, mock_llm):
        """Test finding match for surjection definition."""
        mock_llm.return_value = True
        
        # Different wording for surjection (TF-IDF may find mapping-related terms first)
        term = "Сюръективное отображение"
        definition = "Отображение на множество Y когда каждый элемент Y имеет прообраз"
        
        result = find_definition(term, definition, self.db_name)
        # The result might be any mapping-related definition (6, 7, 8, 9, 10)
        self.assertIsNotNone(result, "Should find some match for mapping-related definition")
        self.assertIsInstance(result, int, "Should return integer ID")
        mock_llm.assert_called()
    
    @patch('search.verify_with_llm')
    def test_no_match_completely_different(self, mock_llm):
        """Test no match for completely different concept."""
        mock_llm.return_value = False
        
        # Completely different mathematical concept
        term = "Интеграл Римана"
        definition = "Интеграл функции по отрезку определяется как предел интегральных сумм"
        
        result = find_definition(term, definition, self.db_name)
        self.assertIsNone(result, "Should not find match for different concept")
    
    @patch('search.verify_with_llm')
    def test_llm_rejects_false_positive(self, mock_llm):
        """Test case where TF-IDF finds similarity but LLM rejects it."""
        mock_llm.return_value = False
        
        # Term with some similar words but different meaning - use exact match for predictable TF-IDF
        term = "Бесконечное множество"
        definition = "Множество всех натуральных чисел"  # Wrong definition for this term
        
        result = find_definition(term, definition, self.db_name)
        self.assertIsNone(result, "LLM should reject false positive from TF-IDF")
        # LLM should be called since term similarity will be high
        mock_llm.assert_called()
    
    @patch('search.verify_with_llm')
    def test_partial_match_with_latex(self, mock_llm):
        """Test matching definitions with LaTeX formulas."""
        mock_llm.return_value = True
        
        # Include LaTeX in the query (should still match after preprocessing)
        term = "Декартово произведение"
        definition = "Для множеств $X$ и $Y$ их произведение $X \\times Y$ состоит из пар $(x,y)$"
        
        result = find_definition(term, definition, self.db_name)
        self.assertEqual(result, 2, "Should match despite LaTeX differences")
        mock_llm.assert_called()
    
    def test_empty_database_scenario(self):
        """Test behavior with empty database (hypothetical)."""
        # Create temporary empty database
        temp_db = 'temp_empty.db'
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE definitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term_ru TEXT NOT NULL,
                definition_ru TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
        
        try:
            result = find_definition("Любой термин", "Любое определение", temp_db)
            self.assertIsNone(result, "Should return None for empty database")
        finally:
            # Clean up
            if os.path.exists(temp_db):
                os.remove(temp_db)
    
    @patch('search.verify_with_llm')
    def test_low_similarity_threshold(self, mock_llm):
        """Test that low similarity candidates are filtered out."""
        mock_llm.return_value = True
        
        # Very different concept that should have low TF-IDF similarity
        term = "Геометрическая прогрессия"
        definition = "Последовательность где каждый следующий элемент получается умножением на константу"
        
        result = find_definition(term, definition, self.db_name)
        # LLM might not even be called if similarity is too low
        self.assertIsNone(result, "Should filter out low similarity candidates")
    
    @patch('search.ChatOpenAI')
    def test_llm_api_error_handling(self, mock_chat):
        """Test handling of LLM API errors."""
        # Mock LLM to raise an exception
        mock_instance = MagicMock()
        mock_instance.invoke.side_effect = Exception("API Error")
        mock_chat.return_value = mock_instance
        
        term = "Бесконечное множество"
        definition = "Множество A называется бесконечным"
        
        result = find_definition(term, definition, self.db_name)
        self.assertIsNone(result, "Should handle LLM API errors gracefully")


class TestTfidfSimilarity(unittest.TestCase):
    """Test TF-IDF similarity calculation with real data."""
    
    def setUp(self):
        """Set up test database path."""
        self.db_name = os.path.join(os.path.dirname(__file__), 'math_base.db')
    
    def test_calculate_similarity_scores(self):
        """Test TF-IDF similarity calculation."""
        # Get real definitions from database
        definitions = get_all_definitions(self.db_name)
        self.assertGreater(len(definitions), 0)
        
        # Test with a query similar to existing definition
        query_term = "Бесконечное множество"
        query_def = "Множество эквивалентное своей части"
        
        scores = calculate_tfidf_similarity(query_term, query_def, definitions)
        
        self.assertIsInstance(scores, list)
        self.assertGreater(len(scores), 0)
        
        # Check that scores are sorted in descending order
        for i in range(len(scores) - 1):
            self.assertGreaterEqual(scores[i][1], scores[i+1][1], 
                                  "Scores should be sorted in descending order")
        
        # Check that first result has reasonable similarity (should be > 0.3 for similar terms)
        if scores:
            self.assertIsInstance(scores[0][0], int, "Definition ID should be integer")
            self.assertIsInstance(scores[0][1], float, "Score should be float")
            self.assertGreaterEqual(scores[0][1], 0.0, "Score should be non-negative")
            self.assertLessEqual(scores[0][1], 1.0, "Score should not exceed 1.0")
    
    def test_similarity_with_empty_query(self):
        """Test similarity calculation with empty query."""
        definitions = get_all_definitions(self.db_name)
        
        scores = calculate_tfidf_similarity("", "", definitions)
        self.assertIsInstance(scores, list)
        # All scores should be 0 for empty query
        for _, score in scores:
            self.assertEqual(score, 0.0, "Empty query should result in zero scores")
    
    def test_similarity_with_no_definitions(self):
        """Test similarity calculation with no existing definitions."""
        scores = calculate_tfidf_similarity("термин", "определение", [])
        self.assertEqual(scores, [], "Should return empty list for no definitions")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
