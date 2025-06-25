import sqlite3
import os
import re

def sanitize_filename(name):
    """Очищает имя файла от недопустимых символов."""
    return re.sub(r'[\\/:*?"<>|]', '_', name)

def generate_obsidian_files(db_name='math_base.db', output_dir='visualisation'):
    """Генерирует Markdown файлы для Obsidian из базы данных."""
    # 1. Создание директории для вывода
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Создана директория: {output_dir}")

    # 2. Подключение к БД
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # 3. Получение всех данных
    cursor.execute("SELECT id, term_ru, definition_ru FROM definitions")
    definitions = {row[0]: {'term': row[1], 'text': row[2]} for row in cursor.fetchall()}

    cursor.execute("SELECT id, name_ru, statement_ru, proof_ru FROM theorems")
    theorems = {row[0]: {'name': row[1], 'statement': row[2], 'proof': row[3]} for row in cursor.fetchall()}

    # 4. Генерация файлов для определений
    print("\n--- Генерация файлов для определений ---")
    for def_id, data in definitions.items():
        filename = sanitize_filename(data['term']) + '.md'
        filepath = os.path.join(output_dir, filename)
        links = []

        # Поиск связей
        cursor.execute("SELECT used_definition_id FROM definition_uses_definition WHERE definition_id = ?", (def_id,))
        used_def_ids = [row[0] for row in cursor.fetchall()]
        for used_id in used_def_ids:
            if used_id in definitions:
                links.append(f"[[{sanitize_filename(definitions[used_id]['term'])}]]")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {data['term']}\n\n")
            f.write(f"#определение\n\n")  # Добавлен тег определения
            f.write(f"{data['text']}\n\n")
            if links:
                f.write("\n---\n**Ссылки:**\n")
                f.write(", ".join(links))
        print(f"Создан файл: {filename}")

    # 5. Генерация файлов для теорем
    print("\n--- Генерация файлов для теорем ---")
    for theorem_id, data in theorems.items():
        filename = sanitize_filename(data['name']) + '.md'
        filepath = os.path.join(output_dir, filename)
        links = []

        # Связи с определениями
        cursor.execute("SELECT definition_id FROM theorem_uses_definition WHERE theorem_id = ?", (theorem_id,))
        used_def_ids = [row[0] for row in cursor.fetchall()]
        for used_id in used_def_ids:
            if used_id in definitions:
                links.append(f"[[{sanitize_filename(definitions[used_id]['term'])}]]")

        # Связи с теоремами
        cursor.execute("SELECT used_theorem_id FROM theorem_uses_theorem WHERE theorem_id = ?", (theorem_id,))
        used_theorem_ids = [row[0] for row in cursor.fetchall()]
        for used_id in used_theorem_ids:
            if used_id in theorems:
                links.append(f"[[{sanitize_filename(theorems[used_id]['name'])}]]")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {data['name']}\n\n")
            f.write(f"#теорема\n\n")  # Добавлен тег теоремы
            f.write(f"**Формулировка:**\n{data['statement']}\n\n")
            if data['proof']:
                f.write(f"**Доказательство:**\n{data['proof']}\n\n")
            
            if links:
                f.write("\n---\n**Ссылки:**\n")
                f.write(", ".join(links))
        print(f"Создан файл: {filename}")

    conn.close()
    print("\nГенерация файлов завершена.")

if __name__ == '__main__':
    generate_obsidian_files()
