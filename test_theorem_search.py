#!/usr/bin/env python3
"""
Simple test script for theorem duplicate checking functionality.
"""

from search import find_theorem
import os

def test_theorem_search():
    """Test the find_theorem function with some examples."""
    
    print("Testing theorem duplicate detection...")
    print("=" * 50)
    
    # Test case 1: Try to find existing theorem (should find duplicate)
    name1 = "Теорема о существовании и единственности супремума"
    statement1 = "Супремум существует и единственен для любого непустого ограниченного множества"
    
    print(f"Test 1: Searching for existing theorem")
    print(f"Name: {name1}")
    print(f"Statement: {statement1}")
    
    result1 = find_theorem(name1, statement1)
    if result1:
        print(f"✅ Found existing theorem with ID: {result1}")
    else:
        print("❌ No existing theorem found")
    
    print("\n" + "-" * 50 + "\n")
    
    # Test case 2: Try completely new theorem (should not find duplicate)
    name2 = "Теорема о новом математическом результате"
    statement2 = "Это совершенно новая теорема которой не существует в базе данных"
    
    print(f"Test 2: Searching for non-existing theorem")
    print(f"Name: {name2}")
    print(f"Statement: {statement2}")
    
    result2 = find_theorem(name2, statement2)
    if result2:
        print(f"❌ Unexpected: Found theorem with ID: {result2}")
    else:
        print("✅ Correctly found no existing theorem")
    
    print("\n" + "-" * 50 + "\n")
    
    # Test case 3: Try similar wording (should potentially find duplicate)
    name3 = "Лемма Кантора"
    statement3 = "Принцип вложенных отрезков - любая последовательность вложенных отрезков имеет непустое пересечение"
    
    print(f"Test 3: Searching for theorem with similar wording")
    print(f"Name: {name3}")
    print(f"Statement: {statement3}")
    
    result3 = find_theorem(name3, statement3)
    if result3:
        print(f"✅ Found similar theorem with ID: {result3}")
    else:
        print("⚠️  No similar theorem found")
    
    print("\n" + "=" * 50)
    print("Theorem search testing completed!")

if __name__ == "__main__":
    # Check if API key is available
    if not os.getenv("OPENROUTER_API_KEY"):
        print("⚠️  Warning: OPENROUTER_API_KEY not found. LLM verification will fail.")
        print("Set the API key in .env file for full functionality.")
        print()
    
    test_theorem_search()
