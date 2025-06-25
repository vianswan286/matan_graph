import sqlite3
import os
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import numpy as np
import logging

# Load environment variables
load_dotenv()

# Initialize logger
logger = logging.getLogger(__name__)

def preprocess_text(text):
    """
    Preprocesses text for TF-IDF analysis.
    Removes LaTeX formulas and special characters, converts to lowercase.
    """
    if not text:
        return ""
    
    # Remove LaTeX formulas (everything between $ signs, \[ \], and equation environments)
    text = re.sub(r'\$.*?\$', ' ', text)
    text = re.sub(r'\\begin\{.*?\}.*?\\end\{.*?\}', ' ', text, flags=re.DOTALL)
    text = re.sub(r'\\.*?(?=\s|$)', ' ', text)  # Remove LaTeX commands
    text = re.sub(r'[{}\\]', ' ', text)  # Remove remaining LaTeX characters
    
    # Remove special characters and normalize spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    return text.lower().strip()

def get_all_definitions(db_name='math_base.db'):
    """
    Retrieves all definitions from the database.
    Returns list of tuples: (id, term_ru, definition_ru)
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, term_ru, definition_ru 
        FROM definitions
    """)
    
    results = cursor.fetchall()
    conn.close()
    
    return results

def calculate_tfidf_similarity(query_term, query_definition, existing_definitions):
    """
    Calculates TF-IDF similarity scores for terms and definitions.
    Returns list of tuples: (definition_id, combined_score)
    """
    if not existing_definitions:
        return []
    
    # Prepare texts for TF-IDF
    query_term_clean = preprocess_text(query_term)
    query_definition_clean = preprocess_text(query_definition)
    
    # Extract and preprocess existing terms and definitions
    existing_ids = [def_row[0] for def_row in existing_definitions]
    existing_terms = [preprocess_text(def_row[1]) for def_row in existing_definitions]
    existing_defs = [preprocess_text(def_row[2]) for def_row in existing_definitions]
    
    # Calculate TF-IDF similarity for terms
    term_scores = []
    if query_term_clean and any(existing_terms):
        try:
            vectorizer_terms = TfidfVectorizer(stop_words=None, ngram_range=(1, 2))
            all_terms = [query_term_clean] + existing_terms
            tfidf_matrix_terms = vectorizer_terms.fit_transform(all_terms)
            
            # Calculate cosine similarity between query and each existing term
            similarities_terms = cosine_similarity(tfidf_matrix_terms[0:1], tfidf_matrix_terms[1:])
            term_scores = similarities_terms[0].tolist()
        except:
            term_scores = [0.0] * len(existing_terms)
    else:
        term_scores = [0.0] * len(existing_terms)
    
    # Calculate TF-IDF similarity for definitions
    def_scores = []
    if query_definition_clean and any(existing_defs):
        try:
            vectorizer_defs = TfidfVectorizer(stop_words=None, ngram_range=(1, 2))
            all_defs = [query_definition_clean] + existing_defs
            tfidf_matrix_defs = vectorizer_defs.fit_transform(all_defs)
            
            # Calculate cosine similarity between query and each existing definition
            similarities_defs = cosine_similarity(tfidf_matrix_defs[0:1], tfidf_matrix_defs[1:])
            def_scores = similarities_defs[0].tolist()
        except:
            def_scores = [0.0] * len(existing_defs)
    else:
        def_scores = [0.0] * len(existing_defs)
    
    # Combine scores (weighted average: 40% term similarity, 60% definition similarity)
    combined_scores = []
    for i in range(len(existing_ids)):
        term_score = term_scores[i] if i < len(term_scores) else 0.0
        def_score = def_scores[i] if i < len(def_scores) else 0.0
        combined_score = 0.4 * term_score + 0.6 * def_score
        combined_scores.append((existing_ids[i], combined_score))
    
    # Sort by combined score in descending order
    combined_scores.sort(key=lambda x: x[1], reverse=True)
    
    return combined_scores

def verify_with_llm(query_term, query_definition, candidate_term, candidate_definition):
    """
    Uses LLM to verify if the candidate matches the query definition.
    Returns True if they are the same concept, False otherwise.
    """
    try:
        llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            model_name="meta-llama/llama-4-maverick"
        )
        
        prompt = f"""Определи, являются ли эти два математических определения одним и тем же понятием.

Определение 1:
Термин: {query_term}
Определение: {query_definition}

Определение 2:
Термин: {candidate_term}
Определение: {candidate_definition}

Внимательно сравни математическое содержание определений. Не обращай внимание на разные формулировки или нотации - важна только математическая суть.

Ответь только "ДА" если это одно и то же понятие, или "НЕТ" если это разные понятия."""

        response = llm.invoke(prompt)
        answer = response.content.strip().upper()
        
        return "ДА" in answer
        
    except Exception as e:
        logger.error(f"Error calling LLM API: {e}")
        return False

def find_definition(term_ru, definition_ru, db_name='math_base.db'):
    """
    Finds if a definition already exists in the database using TF-IDF techniques
    and LLM verification as described in README.md.
    
    Args:
        term_ru (str): Russian term to search for
        definition_ru (str): Russian definition to search for
        db_name (str): Database filename
    
    Returns:
        int or None: Database ID if existing definition found, None otherwise
    """
    
    # Get all existing definitions from database
    existing_definitions = get_all_definitions(db_name)
    
    if not existing_definitions:
        return None
        
    # First check for exact matches to avoid unnecessary LLM calls
    for def_id, def_term, def_text in existing_definitions:
        # Case-insensitive exact match on term
        if def_term.lower().strip() == term_ru.lower().strip():
            # If term matches exactly, check if definition is also very similar
            if def_text.lower().strip() == definition_ru.lower().strip():
                logger.info(f"Exact match found for term and definition: '{term_ru}' (ID: {def_id})")
                return def_id
            logger.info(f"Exact term match found, checking definition with TF-IDF: '{term_ru}' (ID: {def_id})")

    
    # Calculate TF-IDF similarity scores
    similarity_scores = calculate_tfidf_similarity(term_ru, definition_ru, existing_definitions)
    
    if not similarity_scores:
        return None
    
    # Get top 2 candidates (as specified in README.md)
    top_candidates = similarity_scores[:2]
    
    # Filter candidates with reasonable similarity scores (> 0.1)
    top_candidates = [(def_id, score) for def_id, score in top_candidates if score > 0.1]
    
    if not top_candidates:
        return None
    
    # Verify each candidate with LLM
    for candidate_id, score in top_candidates:
        # Get candidate details from database
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT term_ru, definition_ru 
            FROM definitions 
            WHERE id = ?
        """, (candidate_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            candidate_term, candidate_definition = result
            
            # Use LLM to verify if this is the same concept
            if verify_with_llm(term_ru, definition_ru, candidate_term, candidate_definition):
                return candidate_id
    
    # No matching definition found
    return None

def find_theorem(name_ru, statement_ru, db_name='math_base.db'):
    """
    Find existing theorem in database using TF-IDF similarity and LLM verification.
    
    Args:
        name_ru (str): Russian name of the theorem to search for
        statement_ru (str): Russian statement/formulation of the theorem
        db_name (str): Database file path
        
    Returns:
        int or None: ID of existing theorem if found, None otherwise
    """
    try:
        # Get all theorems from database
        theorems = get_all_theorems(db_name)
        
        if not theorems:
            return None
            
        # First check for exact matches to avoid unnecessary LLM calls
        for theorem in theorems:
            # Case-insensitive exact match on name
            if theorem['name_ru'].lower().strip() == name_ru.lower().strip():
                # If name matches exactly, check if statement is also very similar
                if theorem['statement_ru'].lower().strip() == statement_ru.lower().strip():
                    logger.info(f"Exact match found for theorem name and statement: '{name_ru}' (ID: {theorem['id']})")
                    return theorem['id']
                logger.info(f"Exact theorem name match found, checking statement with TF-IDF: '{name_ru}' (ID: {theorem['id']})")
            
        # Preprocess query
        query_name = preprocess_text(name_ru)
        query_statement = preprocess_text(statement_ru)
        
        # Calculate similarity scores
        similarity_scores = calculate_theorem_similarity_scores(
            query_name, query_statement, theorems
        )
        
        # Get top 2 candidates with similarity > 0.1
        top_candidates = [
            (idx, score) for idx, score in enumerate(similarity_scores) 
            if score > 0.1
        ]
        top_candidates.sort(key=lambda x: x[1], reverse=True)
        top_candidates = top_candidates[:2]
        
        # Check each candidate with LLM
        for idx, score in top_candidates:
            theorem = theorems[idx]
            if verify_theorem_match_with_llm(
                name_ru, statement_ru, 
                theorem['name_ru'], theorem['statement_ru']
            ):
                return theorem['id']
                
        return None
        
    except Exception as e:
        logger.error(f"Error in find_theorem: {e}")
        return None

def get_all_theorems(db_name='math_base.db'):
    """
    Retrieve all theorems from database.
    
    Returns:
        list: List of theorem dictionaries with id, name_ru, statement_ru
    """
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name_ru, statement_ru 
            FROM theorems
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        theorems = []
        for row in results:
            theorems.append({
                'id': row[0],
                'name_ru': row[1], 
                'statement_ru': row[2] or ''
            })
            
        return theorems
        
    except Exception as e:
        logger.error(f"Error retrieving theorems: {e}")
        return []

def calculate_theorem_similarity_scores(query_name, query_statement, theorems):
    """
    Calculate TF-IDF similarity scores between query theorem and existing theorems.
    
    Args:
        query_name (str): Preprocessed query theorem name
        query_statement (str): Preprocessed query theorem statement
        theorems (list): List of existing theorems
        
    Returns:
        list: Similarity scores for each theorem
    """
    try:
        # Prepare corpus
        names = [preprocess_text(t['name_ru']) for t in theorems]
        statements = [preprocess_text(t['statement_ru']) for t in theorems]
        
        # Add query to corpus
        all_names = names + [query_name]
        all_statements = statements + [query_statement]
        
        # Calculate TF-IDF for names
        vectorizer_names = TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1,
            stop_words=None
        )
        
        if any(all_names):  # Check if there are non-empty names
            tfidf_names = vectorizer_names.fit_transform(all_names)
            name_similarities = cosine_similarity(
                tfidf_names[-1:], tfidf_names[:-1]
            )[0]
        else:
            name_similarities = [0.0] * len(theorems)
        
        # Calculate TF-IDF for statements  
        vectorizer_statements = TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1,
            stop_words=None
        )
        
        if any(all_statements):  # Check if there are non-empty statements
            tfidf_statements = vectorizer_statements.fit_transform(all_statements)
            statement_similarities = cosine_similarity(
                tfidf_statements[-1:], tfidf_statements[:-1]
            )[0]
        else:
            statement_similarities = [0.0] * len(theorems)
        
        # Combine similarities: 30% name, 70% statement (statements are more important for theorems)
        combined_scores = [
            0.3 * name_sim + 0.7 * statement_sim
            for name_sim, statement_sim in zip(name_similarities, statement_similarities)
        ]
        
        return combined_scores
        
    except Exception as e:
        logger.error(f"Error calculating theorem similarity: {e}")
        return [0.0] * len(theorems)

def verify_theorem_match_with_llm(query_name, query_statement, candidate_name, candidate_statement):
    """
    Use LLM to verify if query theorem matches candidate theorem.
    
    Args:
        query_name (str): Query theorem name
        query_statement (str): Query theorem statement
        candidate_name (str): Candidate theorem name  
        candidate_statement (str): Candidate theorem statement
        
    Returns:
        bool: True if theorems are equivalent, False otherwise
    """
    try:
        # Log what we're sending to the LLM
        logger.info(f"Verifying theorem match with LLM:")
        logger.info(f"  Query: '{query_name}' (length: {len(query_statement)} chars)")
        logger.info(f"  Candidate: '{candidate_name}' (length: {len(candidate_statement)} chars)")
        
        llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            model_name="meta-llama/llama-4-maverick",
            temperature=0.1
        )
        
        prompt = f"""
Определи, являются ли эти две математические теоремы одинаковыми или эквивалентными по смыслу.

Теорема 1:
Название: {query_name}
Формулировка: {query_statement}

Теорема 2:  
Название: {candidate_name}
Формулировка: {candidate_statement}

Ответь только "ДА" если теоремы эквивалентны по математическому смыслу, или "НЕТ" если они разные.
Учитывай, что разные формулировки могут выражать одну и ту же математическую идею.
"""
        
        response = llm.invoke([HumanMessage(content=prompt)])
        answer = response.content.strip().upper()
        
        logger.info(f"  LLM response: {answer}")
        return "ДА" in answer
        
    except Exception as e:
        logger.error(f"Error calling LLM API: {e}")
        return False

def find_definition_by_term(term_ru, db_name='math_base.db'):
    """
    Find existing definition in database by term name only using TF-IDF similarity and LLM verification.
    
    Args:
        term_ru (str): Russian term/concept name to search for
        db_name (str): Database file path
        
    Returns:
        int or None: ID of existing definition if found, None otherwise
    """
    try:
        # Get all definitions from database
        definitions = get_all_definitions(db_name)
        
        if not definitions:
            return None
        
        # First check for exact matches to avoid unnecessary LLM calls
        for def_id, def_term, _ in definitions:
            # Case-insensitive exact match
            if def_term.lower().strip() == term_ru.lower().strip():
                logger.info(f"Exact term match found: '{term_ru}' = '{def_term}' (ID: {def_id})")
                return def_id
            
        # Preprocess query term
        query_term = preprocess_text(term_ru)
        
        # Calculate similarity scores for terms only
        similarity_scores = calculate_term_similarity_scores(query_term, definitions)
        
        # Get top 2 candidates with similarity > 0.2 (higher threshold for name-only search)
        top_candidates = [
            (idx, score) for idx, score in enumerate(similarity_scores) 
            if score > 0.2
        ]
        top_candidates.sort(key=lambda x: x[1], reverse=True)
        top_candidates = top_candidates[:2]
        
        # Check each candidate with LLM
        for idx, score in top_candidates:
            definition = definitions[idx]
            logger.info(f"Checking term similarity with LLM: '{term_ru}' vs '{definition[1]}' (score: {score:.2f})")
            if verify_term_match_with_llm(term_ru, definition[1]):
                return definition[0]
                
        return None
        
    except Exception as e:
        logger.error(f"Error in find_definition_by_term: {e}")
        return None

def find_theorem_by_name(name_ru, db_name='math_base.db'):
    """
    Find existing theorem in database by name only using TF-IDF similarity and LLM verification.
    
    Args:
        name_ru (str): Russian theorem name to search for
        db_name (str): Database file path
        
    Returns:
        int or None: ID of existing theorem if found, None otherwise
    """
    try:
        # Get all theorems from database
        theorems = get_all_theorems(db_name)
        
        if not theorems:
            return None
        
        # First check for exact matches to avoid unnecessary LLM calls
        for theorem in theorems:
            # Case-insensitive exact match
            if theorem['name_ru'].lower().strip() == name_ru.lower().strip():
                logger.info(f"Exact theorem name match found: '{name_ru}' = '{theorem['name_ru']}' (ID: {theorem['id']})")
                return theorem['id']
            
        # Preprocess query name
        query_name = preprocess_text(name_ru)
        
        # Calculate similarity scores for names only
        similarity_scores = calculate_theorem_name_similarity_scores(query_name, theorems)
        
        # Get top 2 candidates with similarity > 0.2 (higher threshold for name-only search)
        top_candidates = [
            (idx, score) for idx, score in enumerate(similarity_scores) 
            if score > 0.2
        ]
        top_candidates.sort(key=lambda x: x[1], reverse=True)
        top_candidates = top_candidates[:2]
        
        # Check each candidate with LLM
        for idx, score in top_candidates:
            theorem = theorems[idx]
            logger.info(f"Checking theorem name similarity with LLM: '{name_ru}' vs '{theorem['name_ru']}' (score: {score:.2f})")
            if verify_theorem_name_match_with_llm(name_ru, theorem['name_ru']):
                return theorem['id']
                
        return None
        
    except Exception as e:
        logger.error(f"Error in find_theorem_by_name: {e}")
        return None

def calculate_term_similarity_scores(query_term, definitions):
    """
    Calculate TF-IDF similarity scores between query term and existing definition terms.
    
    Args:
        query_term (str): Preprocessed query term
        definitions (list): List of existing definitions
        
    Returns:
        list: Similarity scores for each definition term
    """
    try:
        # Prepare corpus of terms
        terms = [preprocess_text(d[1]) for d in definitions]
        
        # Add query to corpus
        all_terms = terms + [query_term]
        
        # Calculate TF-IDF for terms
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1,
            stop_words=None
        )
        
        if any(all_terms):  # Check if there are non-empty terms
            tfidf_matrix = vectorizer.fit_transform(all_terms)
            similarities = cosine_similarity(
                tfidf_matrix[-1:], tfidf_matrix[:-1]
            )[0]
        else:
            similarities = [0.0] * len(definitions)
        
        return similarities
        
    except Exception as e:
        logger.error(f"Error calculating term similarity: {e}")
        return [0.0] * len(definitions)

def calculate_theorem_name_similarity_scores(query_name, theorems):
    """
    Calculate TF-IDF similarity scores between query theorem name and existing theorem names.
    
    Args:
        query_name (str): Preprocessed query theorem name
        theorems (list): List of existing theorems
        
    Returns:
        list: Similarity scores for each theorem name
    """
    try:
        # Prepare corpus of theorem names
        names = [preprocess_text(t['name_ru']) for t in theorems]
        
        # Add query to corpus
        all_names = names + [query_name]
        
        # Calculate TF-IDF for names
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1,
            stop_words=None
        )
        
        if any(all_names):  # Check if there are non-empty names
            tfidf_matrix = vectorizer.fit_transform(all_names)
            similarities = cosine_similarity(
                tfidf_matrix[-1:], tfidf_matrix[:-1]
            )[0]
        else:
            similarities = [0.0] * len(theorems)
        
        return similarities
        
    except Exception as e:
        logger.error(f"Error calculating theorem name similarity: {e}")
        return [0.0] * len(theorems)

def verify_term_match_with_llm(query_term, candidate_term):
    """
    Use LLM to verify if query term matches candidate term.
    
    Args:
        query_term (str): Query term name
        candidate_term (str): Candidate term name
        
    Returns:
        bool: True if terms are equivalent, False otherwise
    """
    # First check for exact matches to avoid unnecessary LLM calls
    if query_term.lower().strip() == candidate_term.lower().strip():
        logger.info(f"Exact term match found without LLM: '{query_term}' = '{candidate_term}'")
        return True
        
    try:
        # Log what we're sending to the LLM
        logger.info(f"Verifying term match with LLM:")
        logger.info(f"  Query term: '{query_term}' (length: {len(query_term)} chars)")
        logger.info(f"  Candidate term: '{candidate_term}' (length: {len(candidate_term)} chars)")
        
        llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            model_name="meta-llama/llama-4-maverick",
            temperature=0.1
        )
        
        prompt = f"""
Определи, являются ли эти два математических термина одинаковыми или эквивалентными по смыслу.

Термин 1: {query_term}
Термин 2: {candidate_term}

Ответь только "ДА" если термины эквивалентны по математическому смыслу, или "НЕТ" если они разные.
Учитывай синонимы и разные формулировки одного понятия.
"""
        
        response = llm.invoke([HumanMessage(content=prompt)])
        answer = response.content.strip().upper()
        
        logger.info(f"  LLM response: {answer}")
        return "ДА" in answer
        
    except Exception as e:
        logger.error(f"Error calling LLM API for term verification: {e}")
        return False

def verify_theorem_name_match_with_llm(query_name, candidate_name):
    """
    Use LLM to verify if query theorem name matches candidate theorem name.
    
    Args:
        query_name (str): Query theorem name
        candidate_name (str): Candidate theorem name
        
    Returns:
        bool: True if theorem names are equivalent, False otherwise
    """
    try:
        llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            model_name="meta-llama/llama-4-maverick"
        )
        
        prompt = f"""
Определи, являются ли эти два названия математических теорем одинаковыми или эквивалентными по смыслу.

Название 1: {query_name}
Название 2: {candidate_name}

Ответь только "ДА" если названия эквивалентны по математическому смыслу, или "НЕТ" если они разные.
Учитывай синонимы и разные формулировки одного понятия.
"""
        
        response = llm.invoke([HumanMessage(content=prompt)])
        answer = response.content.strip().upper()
        
        return "ДА" in answer
        
    except Exception as e:
        logger.error(f"Error calling LLM API for theorem name verification: {e}")
        return False

# Example usage
if __name__ == "__main__":
    # Test the function
    test_term = "Бесконечное множество"
    test_definition = "Множество A называется бесконечным, если оно эквивалентно своей правильной части"
    
    result = find_definition(test_term, test_definition)
    if result:
        print(f"Found existing definition with ID: {result}")
    else:
        print("No existing definition found")
