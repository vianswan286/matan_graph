#!/usr/bin/env python3
"""
Test script for name-only search functionality.
"""

from search import find_definition_by_term, find_theorem_by_name
import os

def test_name_only_search():
    """Test the name-only search functions."""
    
    # Use the test database with known data
    test_db = os.path.join('tests', 'math_base.db')
    
    print("Testing name-only search functionality...")
    print("=" * 60)
    print(f"Using test database: {test_db}")
    print("=" * 60)
    
    # Test definition search by term only
    print("1. Testing definition search by term only:")
    print("-" * 40)
    
    test_terms = [
        "Множество",
        "Бесконечное множество", 
        "Декартово произведение",
        "Новый термин который не существует"
    ]
    
    for term in test_terms:
        print(f"Searching for term: '{term}'")
        result = find_definition_by_term(term, test_db)
        if result:
            print(f"  ✅ Found definition with ID: {result}")
        else:
            print(f"  ❌ No definition found")
        print()
    
    print("\n" + "=" * 60 + "\n")
    
    # Test theorem search by name only
    print("2. Testing theorem search by name only:")
    print("-" * 40)
    
    test_names = [
        "Теорема Кантора",
        "Лемма о вложенных отрезках",
        "Теорема о супремуме",
        "Новая теорема которой не существует"
    ]
    
    for name in test_names:
        print(f"Searching for theorem: '{name}'")
        result = find_theorem_by_name(name, test_db)
        if result:
            print(f"  ✅ Found theorem with ID: {result}")
        else:
            print(f"  ❌ No theorem found")
        print()
    
    print("=" * 60)
    print("Name-only search testing completed!")

if __name__ == "__main__":
    # Check if API key is available
    if not os.getenv("OPENROUTER_API_KEY"):
        print("⚠️  Warning: OPENROUTER_API_KEY not found. LLM verification will fail.")
        print("Set the API key in .env file for full functionality.")
        print()
    
    test_name_only_search()
