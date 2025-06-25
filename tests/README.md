# Tests for search.py

This directory contains comprehensive tests for the `find_definition` function and related components in `search.py`.

## Test Database

The tests use a database file `tests/math_base.db` which contains real mathematical definitions for testing. This database was moved from the main project directory to ensure tests are isolated and use consistent test data.

## Test Files

### `test_search.py`
Main test suite covering:

1. **TestSearchFunctions**
   - `test_preprocess_text()` - Tests LaTeX removal and text preprocessing
   - `test_get_all_definitions()` - Tests database retrieval functionality

2. **TestFindDefinitionRealData** 
   - `test_exact_match_infinite_set()` - Tests exact matching with ID 1 (Бесконечное множество)
   - `test_similar_match_cartesian_product()` - Tests similar matching with ID 2 (Декартово произведение)
   - `test_injection_definition_match()` - Tests injection-related matching
   - `test_surjection_definition_match()` - Tests surjection-related matching
   - `test_no_match_completely_different()` - Tests rejection of unrelated concepts
   - `test_llm_rejects_false_positive()` - Tests LLM rejection of TF-IDF false positives
   - `test_partial_match_with_latex()` - Tests matching with LaTeX formulas
   - `test_empty_database_scenario()` - Tests behavior with empty database
   - `test_low_similarity_threshold()` - Tests filtering of low-similarity candidates
   - `test_llm_api_error_handling()` - Tests graceful handling of API errors

3. **TestTfidfSimilarity**
   - `test_calculate_similarity_scores()` - Tests TF-IDF calculation with real data
   - `test_similarity_with_empty_query()` - Tests empty query handling
   - `test_similarity_with_no_definitions()` - Tests empty database handling

### `test_integration.py`
Integration tests using real database and real LLM calls:

1. **TestSearchIntegration**
   - `test_integration_with_real_llm_exact_match()` - Real LLM test (requires API key)
   - `test_integration_with_real_llm_similar_match()` - Real LLM test (requires API key)  
   - `test_integration_with_real_llm_no_match()` - Real LLM test (requires API key)

2. **TestSearchManualVerification**
   - `test_manual_verify_top_candidates()` - Prints TF-IDF candidates for manual inspection

### `run_tests.py`
Test runner script that executes all tests and provides summary.

## Real Data Used

Tests use actual definitions from `tests/math_base.db` including:
- ID 1: Бесконечное множество
- ID 2: Декартово произведение  
- ID 6: Отображение (многозначное)
- ID 9: Инъекция
- ID 10: Сюръекция

## Running Tests

### Run All Tests
```bash
cd /home/sasha/Desktop/matan_agent
python tests/run_tests.py
```

### Run Specific Test File
```bash
python -m pytest tests/test_search.py -v
python -m pytest tests/test_integration.py -v
```

### Run Individual Test
```bash
python -m pytest tests/test_search.py::TestFindDefinitionRealData::test_exact_match_infinite_set -v
```

## Test Results Analysis

The tests demonstrate that:

1. **TF-IDF Similarity Works**: Successfully identifies similar mathematical concepts
2. **Text Preprocessing Effective**: Properly handles LaTeX formulas and special characters
3. **LLM Integration Functional**: OpenRouter/GPT-4 API calls work correctly
4. **Edge Cases Handled**: Empty databases, API errors, low similarities
5. **Real Data Compatible**: Works with actual mathematical definitions in Russian

## Key Findings

- TF-IDF often finds "Отображение (многозначное)" as similar to injection/surjection queries because of the common term "отображение"
- The LLM verification step is crucial for filtering out false positives from TF-IDF
- Text preprocessing successfully removes LaTeX formatting while preserving semantic content
- The 40%/60% weighting of term vs definition similarity works well for mathematical content

## Mock vs Real LLM

Most tests use mocked LLM calls for fast, predictable testing. Integration tests with real LLM require:
- Valid `OPENROUTER_API_KEY` environment variable
- Internet connection
- API credits

Tests are skipped automatically if API key is not available.

## Adding New Tests

When adding new tests:
1. Use real data from the database when possible
2. Mock LLM calls for unit tests, use real calls sparingly for integration tests
3. Test both positive and negative cases
4. Include edge cases (empty inputs, API errors, etc.)
5. Verify TF-IDF candidates manually using the verification test
