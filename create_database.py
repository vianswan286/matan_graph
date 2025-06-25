import sqlite3

def create_database(db_name='math_base.db'):
    """
    Создает базу данных SQLite с таблицами для определений и теорем.
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    # --- Создание таблицы для определений ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS definitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        term_ru TEXT NOT NULL,
        definition_ru TEXT NOT NULL,
        term_en TEXT,                  -- только слова на английском языке
        definition_en TEXT,            -- только слова на английском языке
        formula TEXT                   -- формула ассоциированная с определением в tex формате
    );
    ''')
    # --- Создание таблицы для теорем ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS theorems (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name_ru TEXT NOT NULL,
        statement_ru TEXT NOT NULL,
        proof_ru TEXT,
        statement_en TEXT,             -- только слова на английском языке
        proof_en TEXT,                 -- только слова на английском языке
        formula TEXT                   -- формула ассоциированная с формулировкой в tex формате
    );
    ''')

    # --- Создание таблицы связей "Теорема использует Определение" ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS theorem_uses_definition (
        theorem_id INTEGER NOT NULL,
        definition_id INTEGER NOT NULL,
        context TEXT CHECK(context IN ('statement', 'proof')),
        FOREIGN KEY (theorem_id) REFERENCES theorems (id),
        FOREIGN KEY (definition_id) REFERENCES definitions (id),
        PRIMARY KEY (theorem_id, definition_id)
    );
    ''')

    # --- Создание таблицы связей "Теорема использует Теорему" ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS theorem_uses_theorem (
        theorem_id INTEGER NOT NULL,
        used_theorem_id INTEGER NOT NULL,
        context TEXT CHECK(context IN ('statement', 'proof')),
        FOREIGN KEY (theorem_id) REFERENCES theorems (id),
        FOREIGN KEY (used_theorem_id) REFERENCES theorems (id),
        PRIMARY KEY (theorem_id, used_theorem_id)
    );
    ''')

    # --- Создание таблицы связей "Определение использует Определение" ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS definition_uses_definition (
        definition_id INTEGER NOT NULL,
        used_definition_id INTEGER NOT NULL,
        FOREIGN KEY (definition_id) REFERENCES definitions (id),
        FOREIGN KEY (used_definition_id) REFERENCES definitions (id),
        PRIMARY KEY (definition_id, used_definition_id)
    );
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_database()
