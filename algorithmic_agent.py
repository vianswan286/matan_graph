#!/usr/bin/env python3
"""
Algorithmic Mathematical Knowledge Graph Agent

This agent systematically processes mathematical content using a deterministic algorithm:
1. Process each definition one by one (check duplicates → add to database)
2. Process each theorem one by one (check duplicates → add to database)  
3. Find and create connections between theorems and definitions

No LLM decision-making - pure algorithmic approach.
"""

import os
import json
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from search import find_definition, find_theorem, find_definition_by_term, find_theorem_by_name
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('algorithmic_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AlgorithmicAgent:
    """Deterministic agent that processes mathematical content algorithmically."""
    
    def __init__(self, db_name: str = 'math_base.db', lectures_dir: str = 'parsed_lections'):
        self.db_name = db_name
        self.lectures_dir = lectures_dir
        self.stats = {
            'files_processed': 0,
            'definitions_processed': 0,
            'definitions_added': 0,
            'definitions_duplicates': 0,
            'theorems_processed': 0,
            'theorems_added': 0,
            'theorems_duplicates': 0,
            'connections_created': 0
        }
        # Track newly added items for connection analysis
        self.newly_added_definitions = []  # Store newly added definition data
        self.newly_added_theorems = []     # Store newly added theorem data
    
    def run(self):
        """Main algorithmic workflow."""
        logger.info("🔬 Algorithmic Mathematical Knowledge Graph Agent")
        logger.info("=" * 60)
        
        # Step 1: Get all lecture files
        lecture_files = self._get_lecture_files()
        if not lecture_files:
            logger.warning(f"No JSON files found in {self.lectures_dir}/")
            return
        
        logger.info(f"Found {len(lecture_files)} lecture files to process")
        
        # Step 2: Process each file systematically
        for file_path in lecture_files:
            self._process_file(file_path)
        
        # Step 3: Report final statistics
        self._report_final_stats()
    
    def _get_lecture_files(self) -> List[str]:
        """Get all JSON files from lectures directory."""
        try:
            lectures_path = Path(self.lectures_dir)
            if not lectures_path.exists():
                logger.error(f"Directory {self.lectures_dir} does not exist")
                return []
            
            json_files = list(lectures_path.glob("*.json"))
            return [str(f) for f in json_files]
        except Exception as e:
            logger.error(f"Error reading lectures directory: {e}")
            return []
    
    def _process_file(self, file_path: str):
        """Process a single JSON file algorithmically."""
        logger.info(f"📂 Processing file: {file_path}")
        self.stats['files_processed'] += 1
        
        try:
            # Check if file exists and has content
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return
                
            # Check if file is empty
            if os.path.getsize(file_path) == 0:
                logger.warning(f"Empty file: {file_path}, skipping")
                return
            
            # Try multiple encodings
            for encoding in ['utf-8', 'latin1', 'cp1251']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        # Handle empty or malformed JSON
                        try:
                            data = json.load(f)
                            # If we reach here, the file loaded successfully
                            logger.info(f"Successfully loaded {file_path} with {encoding} encoding")
                            break
                        except json.JSONDecodeError as je:
                            logger.error(f"Invalid JSON in {file_path} with encoding {encoding}: {je}")
                            continue
                except UnicodeDecodeError:
                    # Try the next encoding
                    logger.warning(f"Encoding {encoding} failed for {file_path}, trying another")
                    continue
            else:
                # If we get here, all encodings failed
                logger.error(f"Failed to decode {file_path} with any encoding, skipping file")
                return
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return
        
        # Handle various JSON structures with flexible nested data
        logger.info(f"   Parsing JSON structure...")
        
        # CASE 1: Array with data field containing list of outputs
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and 'data' in data[0]:
            logger.info(f"   Found outer array with 'data' field")
            data_items = data[0].get('data', [])
            
            for i, item in enumerate(data_items, 1):
                logger.info(f"   Processing data item {i}/{len(data_items)}")
                if 'output' in item:
                    output = item['output']
                    
                    # Process definitions first (one by one)
                    if 'definitions' in output and output['definitions']:
                        logger.info(f"   📝 Processing {len(output['definitions'])} definitions...")
                        for definition in output['definitions']:
                            self._process_definition(definition)
                    
                    # Process theorems (one by one)  
                    if 'theorems' in output and output['theorems']:
                        logger.info(f"   🔍 Processing {len(output['theorems'])} theorems...")
                        for theorem in output['theorems']:
                            self._process_theorem(theorem)
        
        # CASE 2: Standard array of items with output field
        elif isinstance(data, list):
            logger.info(f"   Found standard array structure")
            for i, item in enumerate(data, 1):
                logger.info(f"   Processing item {i}/{len(data)}")
                if 'output' in item:
                    output = item['output']
                    
                    # Process definitions first (one by one)
                    if 'definitions' in output and output['definitions']:
                        logger.info(f"   📝 Processing {len(output['definitions'])} definitions...")
                        for definition in output['definitions']:
                            self._process_definition(definition)
                    
                    # Process theorems (one by one)  
                    if 'theorems' in output and output['theorems']:
                        logger.info(f"   🔍 Processing {len(output['theorems'])} theorems...")
                        for theorem in output['theorems']:
                            self._process_theorem(theorem)
        
        # CASE 3: Single object with direct definitions/theorems
        else:
            logger.info(f"   Found single object structure")
            # Process definitions first (one by one)
            if 'definitions' in data and data['definitions']:
                logger.info(f"   📝 Processing {len(data['definitions'])} definitions...")
                for definition in data['definitions']:
                    self._process_definition(definition)
            
            # Process theorems (one by one)
            if 'theorems' in data and data['theorems']:
                logger.info(f"   🔍 Processing {len(data['theorems'])} theorems...")
                for theorem in data['theorems']:
                    self._process_theorem(theorem)
        
        # After processing all items, analyze connections for newly added items
        logger.info(f"   🔗 Finding connections...")
        self._find_connections_for_new_items()
        
        logger.info(f"✅ Completed processing {file_path}")
    
    def _find_connections_for_new_items(self):
        """Find connections only for newly added theorems and definitions."""
        # Analyze newly added theorems for connections to definitions
        if self.newly_added_theorems:
            logger.info("🔗 Starting connection analysis for newly added theorems...")
            for theorem in self.newly_added_theorems:
                name_ru = theorem['name_ru']
                statement_ru = theorem['statement_ru']
                
                logger.info(f"   🔗 Analyzing theorem: '{name_ru}'")
                
                # Analyze statement for connections (more selective)
                if statement_ru and len(statement_ru) > 50:
                    self._analyze_theorem_text_for_connections(theorem['id'], statement_ru, 'statement')
        
        # Analyze newly added definitions for connections to existing definitions
        if self.newly_added_definitions:
            logger.info("🔗 Starting connection analysis for newly added definitions...")
            self._analyze_new_definitions_for_connections()
        
        logger.info("✅ Connection analysis completed")
    
    def _process_definition(self, definition: Dict):
        """Process a single definition algorithmically."""
        # Handle both 'term_ru' and 'term' field names
        term_ru = definition.get('term_ru') or definition.get('term', '').strip()
        definition_ru = definition.get('definition_ru') or definition.get('definition', '').strip()
        
        if not term_ru or not definition_ru:
            logger.warning(f"      Skipping incomplete definition")
            return
        
        logger.info(f"      Processing definition: '{term_ru}'")
        self.stats['definitions_processed'] += 1
        
        # Check for duplicate using our optimized search
        duplicate_id = find_definition(term_ru, definition_ru, self.db_name)
        
        if duplicate_id:
            logger.info(f"      ❌ Duplicate found (ID: {duplicate_id}) - skipping")
            self.stats['definitions_duplicates'] += 1
            return
        
        # Add to database
        new_id = self._add_definition_to_db(definition, term_ru, definition_ru)
        if new_id:
            logger.info(f"      ✅ Added definition (ID: {new_id})")
            self.stats['definitions_added'] += 1
            self.newly_added_definitions.append({'id': new_id, 'term_ru': term_ru, 'definition_ru': definition_ru})
        else:
            logger.error(f"      ❌ Failed to add definition")
    
    def _process_theorem(self, theorem: Dict):
        """Process a single theorem algorithmically."""
        # Handle both 'name_ru' and 'name' field names  
        name_ru = theorem.get('name_ru') or theorem.get('name', '').strip()
        statement_ru = theorem.get('statement_ru') or theorem.get('formulation', '').strip()
        
        if not name_ru or not statement_ru:
            logger.warning(f"      Skipping incomplete theorem")
            return
        
        logger.info(f"      Processing theorem: '{name_ru}'")
        self.stats['theorems_processed'] += 1
        
        # Check for duplicate using our optimized search
        duplicate_id = find_theorem(name_ru, statement_ru, self.db_name)
        
        if duplicate_id:
            logger.info(f"      ❌ Duplicate found (ID: {duplicate_id}) - skipping")
            self.stats['theorems_duplicates'] += 1
            return
        
        # Add to database
        new_id = self._add_theorem_to_db(theorem, name_ru, statement_ru)
        if new_id:
            logger.info(f"      ✅ Added theorem (ID: {new_id})")
            self.stats['theorems_added'] += 1
            self.newly_added_theorems.append({'id': new_id, 'name_ru': name_ru, 'statement_ru': statement_ru})
        else:
            logger.error(f"      ❌ Failed to add theorem")
    
    def _add_definition_to_db(self, definition: Dict, term_ru: str, definition_ru: str) -> Optional[int]:
        """Add definition to database."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO definitions (
                    term_ru, definition_ru, term_en, definition_en, formula
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                term_ru,
                definition_ru,
                definition.get('term_en'),
                definition.get('definition_en'),
                definition.get('formula')
            ))
            
            definition_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return definition_id
            
        except Exception as e:
            logger.error(f"Error adding definition to database: {e}")
            return None
    
    def _add_theorem_to_db(self, theorem: Dict, name_ru: str, statement_ru: str) -> Optional[int]:
        """Add theorem to database."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO theorems (
                    name_ru, statement_ru, proof_ru, statement_en, proof_en, formula
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                name_ru,
                statement_ru,
                theorem.get('proof_ru') or theorem.get('proof'),
                theorem.get('statement_en'),
                theorem.get('proof_en'),
                theorem.get('formula')
            ))
            
            theorem_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return theorem_id
            
        except Exception as e:
            logger.error(f"Error adding theorem to database: {e}")
            return None
    
    def _analyze_theorem_text_for_connections(self, theorem_id: int, text: str, context: str):
        """Use LLM to find potential mathematical concept references in theorem text."""
        try:
            # Get all definitions for comprehensive connection analysis
            definitions = self._get_all_definitions()
            
            # Prepare comprehensive LLM prompt for content-based analysis
            prompt = f"""Проанализируйте математический текст и найдите ВСЕ СВЯЗАННЫЕ понятия из списка определений.

АНАЛИЗИРУЕМЫЙ ТЕКСТ:
{text[:1000]}

СПИСОК ДОСТУПНЫХ ОПРЕДЕЛЕНИЙ:
"""
            
            # Add definitions with their content for better matching
            for i, defn in enumerate(definitions[:40]):
                prompt += f"{i+1}. {defn['term_ru']}: {defn['definition_ru'][:100]}...\n"
            
            prompt += f"""

ЗАДАЧА:
- Найдите ВСЕ понятия из списка, которые УПОМИНАЮТСЯ или ИСПОЛЬЗУЮТСЯ в анализируемом тексте
- Учитывайте синонимы, сокращения и математические обозначения
- Ищите семантические связи, а не только точные совпадения текста
- Включайте понятия, которые необходимы для понимания текста

ФОРМАТ ОТВЕТА:
Перечислите ВСЕ найденные связи в формате:
- [номер определения]: [термин]

Если связей нет, ответьте: "НЕТ СВЯЗЕЙ"
"""

            # Call LLM with expanded parameters for comprehensive analysis
            response = self._call_llm(prompt, max_tokens=500)
            
            # Process response with enhanced connection creation
            self._process_comprehensive_connection_response(theorem_id, response, context, definitions)
            
        except Exception as e:
            logger.error(f"Error analyzing theorem text for connections: {e}")
    
    def _process_comprehensive_connection_response(self, theorem_id: int, response: str, context: str, definitions: List[Dict]):
        """Process LLM response and create connections based on comprehensive analysis."""
        if "НЕТ СВЯЗЕЙ" in response.upper() or "НЕТ ССЫЛОК" in response.upper():
            return
        
        # Parse response for numbered definitions
        lines = response.strip().split('\n')
        connections_created = 0
        
        for line in lines:
            line = line.strip()
            if line.startswith('-') and ':' in line:
                try:
                    # Extract definition number and term: "- [номер]: [термин]"
                    parts = line.replace('-', '').strip().split(':', 1)
                    if len(parts) >= 2:
                        def_num_str = parts[0].strip()
                        term = parts[1].strip()
                        
                        # Extract number (handle various formats like "1", "[1]", etc.)
                        import re
                        num_match = re.search(r'\d+', def_num_str)
                        if num_match:
                            def_num = int(num_match.group()) - 1  # Convert to 0-based index
                            
                            # Validate definition number and create connection
                            if 0 <= def_num < len(definitions):
                                defn = definitions[def_num]
                                
                                # Check if connection already exists
                                if not self._connection_exists(theorem_id, defn['id'], 'theorem_definition'):
                                    self._create_theorem_definition_connection(theorem_id, defn['id'], context)
                                    connections_created += 1
                                    logger.info(f"      🔗 Created theorem→definition: '{defn['term_ru']}' ({context})")
                                
                except Exception as e:
                    logger.warning(f"Error parsing connection line '{line}': {e}")
                    continue
        
        if connections_created > 0:
            self.stats['connections_created'] += connections_created

    def _connection_exists(self, source_id: int, target_id: int, connection_type: str) -> bool:
        """Check if connection already exists to prevent duplicates."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            if connection_type == 'theorem_definition':
                cursor.execute("""
                    SELECT 1 FROM theorem_uses_definition 
                    WHERE theorem_id = ? AND definition_id = ?
                """, (source_id, target_id))
            elif connection_type == 'theorem_theorem':
                cursor.execute("""
                    SELECT 1 FROM theorem_uses_theorem 
                    WHERE theorem_id = ? AND used_theorem_id = ?
                """, (source_id, target_id))
            elif connection_type == 'definition_definition':
                cursor.execute("""
                    SELECT 1 FROM definition_uses_definition 
                    WHERE definition_id = ? AND used_definition_id = ?
                """, (source_id, target_id))
            
            result = cursor.fetchone()
            conn.close()
            return result is not None
            
        except Exception as e:
            logger.error(f"Error checking connection existence: {e}")
            return False
    
    def _find_definition_connections(self):
        """Find connections between definitions."""
        logger.info("   🔗 Analyzing definition-to-definition connections...")
        
        # Get all existing definitions for connection analysis
        definitions = self._get_all_definitions()
        
        if not definitions:
            return
        
        # Create a focused list of definition terms for LLM
        def_terms = [defn['term_ru'] for defn in definitions[:30]]  # Limit to 30 most recent
        
        # Prepare more specific LLM prompt
        prompt = f"""Проанализируйте определения и найдите ТОЛЬКО ПРЯМЫЕ УПОМИНАНИЯ определений из списка.

ОПРЕДЕЛЕНИЯ ДЛЯ ПОИСКА:
{', '.join(def_terms)}

ВАЖНО:
- Ищите только ТОЧНЫЕ совпадения терминов или их очевидные синонимы
- НЕ создавайте связи на основе общих математических понятий
- НЕ связывайте через косвенные ассоциации

ФОРМАТ ОТВЕТА:
Если найдены точные упоминания, перечислите их:
- [точный термин]

Если точных упоминаний нет, ответьте: "НЕТ СВЯЗЕЙ"
"""
        
        # Call LLM with more restrictive parameters
        response = self._call_llm(prompt, max_tokens=200)
        
        # Process response more carefully
        self._process_definition_connection_response(response, definitions)
        
        logger.info("✅ Definition connection analysis completed")
    
    def _process_definition_connection_response(self, response: str, definitions: List[Dict]):
        """Process LLM response and create only precise database connections."""
        if "НЕТ СВЯЗЕЙ" in response.upper() or "НЕТ ССЫЛОК" in response.upper():
            return
        
        # Parse response more carefully
        lines = response.strip().split('\n')
        connections_created = 0
        
        for line in lines:
            line = line.strip()
            if line.startswith('-') or line:
                # Extract term (remove bullet points and clean)
                term = line.replace('-', '').strip()
                
                # Skip empty lines or non-term lines
                if not term or len(term) < 3:
                    continue
                
                # Find exact matching definition with strict matching
                for defn in definitions:
                    def_term = defn['term_ru'].strip()
                    
                    # Use exact or very close matching
                    if (def_term.lower() == term.lower() or 
                        term.lower() in def_term.lower() and len(term) > 5):
                        
                        # Check if connection already exists
                        if not self._connection_exists(defn['id'], self.newly_added_definitions[0]['id'], 'definition_definition'):
                            self._create_definition_definition_connection(defn['id'], self.newly_added_definitions[0]['id'])
                            connections_created += 1
                            logger.info(f"     🔗 Created definition→definition: '{def_term}'")
                        break
        
        if connections_created > 0:
            self.stats['connections_created'] += connections_created
    
    def _create_definition_definition_connection(self, definition_id: int, used_definition_id: int):
        """Create connection between two definitions."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO definition_uses_definition 
                (definition_id, used_definition_id) VALUES (?, ?)
            """, (definition_id, used_definition_id))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error creating definition-definition connection: {e}")
    
    def _get_theorem_id_by_name(self, name_ru: str) -> Optional[int]:
        """Get theorem ID by name."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM theorems WHERE name_ru = ?", (name_ru,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting theorem ID: {e}")
            return None
    
    def _get_all_definitions(self) -> List[Dict]:
        """Get all definitions from database."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT id, term_ru, definition_ru FROM definitions")
            rows = cursor.fetchall()
            conn.close()
            return [{'id': row[0], 'term_ru': row[1], 'definition_ru': row[2]} for row in rows]
        except Exception as e:
            logger.error(f"Error getting definitions: {e}")
            return []
    
    def _create_theorem_definition_connection(self, theorem_id: int, definition_id: int, context: str):
        """Create connection between theorem and definition."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO theorem_uses_definition 
                (theorem_id, definition_id, context) VALUES (?, ?, ?)
            """, (theorem_id, definition_id, context))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error creating theorem-definition connection: {e}")
    
    def _call_llm(self, prompt: str, max_tokens: int = 150) -> str:
        """Call LLM with the given prompt."""
        try:
            from openai import OpenAI
            
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY")
            )
            
            response = client.chat.completions.create(
                model="meta-llama/llama-4-maverick",  # Use maverick model for unlimited usage
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            return "НЕТ ССЫЛОК"
    
    def _analyze_new_definitions_for_connections(self):
        """Analyze newly added definitions for connections to existing definitions."""
        logger.info("   🔗 Analyzing newly added definitions for connections...")
        
        # Get all existing definitions for connection analysis
        all_definitions = self._get_all_definitions()
        
        if not all_definitions or not self.newly_added_definitions:
            return
        
        # For each newly added definition, find connections to existing definitions
        for new_def in self.newly_added_definitions:
            logger.info(f"   🔗 Analyzing definition: '{new_def['term_ru']}'")
            
            # Prepare comprehensive LLM prompt for content-based analysis
            prompt = f"""Проанализируйте определение и найдите ВСЕ СВЯЗАННЫЕ понятия из списка существующих определений.

АНАЛИЗИРУЕМОЕ ОПРЕДЕЛЕНИЕ:
Термин: {new_def['term_ru']}
Определение: {new_def['definition_ru']}

СПИСОК СУЩЕСТВУЮЩИХ ОПРЕДЕЛЕНИЙ:
"""
            
            # Add existing definitions with their content for better matching
            for i, defn in enumerate(all_definitions[:40]):
                if defn['id'] != new_def['id']:  # Don't connect to itself
                    prompt += f"{i+1}. {defn['term_ru']}: {defn['definition_ru'][:150]}...\n"
            
            prompt += f"""

ЗАДАЧА:
- Найдите ВСЕ понятия из списка, которые УПОМИНАЮТСЯ или ИСПОЛЬЗУЮТСЯ в анализируемом определении
- Учитывайте синонимы, сокращения и математические обозначения
- Ищите семантические связи и зависимости между понятиями
- Включайте понятия, которые необходимы для понимания определения

ФОРМАТ ОТВЕТА:
Перечислите ВСЕ найденные связи в формате:
- [номер определения]: [термин]

Если связей нет, ответьте: "НЕТ СВЯЗЕЙ"
"""

            # Call LLM with expanded parameters for comprehensive analysis
            response = self._call_llm(prompt, max_tokens=400)
            
            # Process response with enhanced connection creation
            self._process_definition_connection_response(new_def['id'], response, all_definitions)
        
        logger.info("✅ Definition connection analysis completed")
    
    def _process_definition_connection_response(self, definition_id: int, response: str, definitions: List[Dict]):
        """Process LLM response and create connections based on comprehensive analysis."""
        if "НЕТ СВЯЗЕЙ" in response.upper() or "НЕТ ССЫЛОК" in response.upper():
            return
        
        # Parse response for numbered definitions
        lines = response.strip().split('\n')
        connections_created = 0
        
        for line in lines:
            line = line.strip()
            if line.startswith('-') and ':' in line:
                try:
                    # Extract definition number and term: "- [номер]: [термин]"
                    parts = line.replace('-', '').strip().split(':', 1)
                    if len(parts) >= 2:
                        def_num_str = parts[0].strip()
                        term = parts[1].strip()
                        
                        # Extract number (handle various formats like "1", "[1]", etc.)
                        import re
                        num_match = re.search(r'\d+', def_num_str)
                        if num_match:
                            def_num = int(num_match.group()) - 1  # Convert to 0-based index
                            
                            # Validate definition number and create connection
                            if 0 <= def_num < len(definitions):
                                defn = definitions[def_num]
                                
                                # Check if connection already exists
                                if not self._connection_exists(definition_id, defn['id'], 'definition_definition'):
                                    self._create_definition_definition_connection(definition_id, defn['id'])
                                    connections_created += 1
                                    logger.info(f"     🔗 Created definition→definition: '{defn['term_ru']}'")
                                
                except Exception as e:
                    logger.warning(f"Error parsing connection line '{line}': {e}")
                    continue
        
        if connections_created > 0:
            self.stats['connections_created'] += connections_created
    
    def _report_final_stats(self):
        """Report final processing statistics."""
        logger.info("=" * 60)
        logger.info("📊 FINAL PROCESSING STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Files processed: {self.stats['files_processed']}")
        logger.info(f"Definitions processed: {self.stats['definitions_processed']}")
        logger.info(f"  - Added: {self.stats['definitions_added']}")
        logger.info(f"  - Duplicates: {self.stats['definitions_duplicates']}")
        logger.info(f"Theorems processed: {self.stats['theorems_processed']}")
        logger.info(f"  - Added: {self.stats['theorems_added']}")
        logger.info(f"  - Duplicates: {self.stats['theorems_duplicates']}")
        logger.info(f"Connections created: {self.stats['connections_created']}")
        logger.info("=" * 60)


def main():
    """Main entry point."""
    agent = AlgorithmicAgent()
    agent.run()


if __name__ == "__main__":
    main()
