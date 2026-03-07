import sqlite3
import json
import os

DB_PATH = "presets.db"

def init_db():
    """Создает таблицу, если она еще не существует."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS presets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            parameters TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_preset(name: str, parameters: dict):
    """
    Сохраняет или перезаписывает пресет.
    parameters - словарь со всеми значениями из интерфейса.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    params_json = json.dumps(parameters)
    
    # Используем REPLACE, чтобы перезаписывать пресет, если имя уже существует
    cursor.execute('''
        INSERT OR REPLACE INTO presets (id, name, parameters)
        VALUES ((SELECT id FROM presets WHERE name = ?), ?, ?)
    ''', (name, name, params_json))
    
    conn.commit()
    conn.close()

def load_preset(name: str) -> dict:
    """Загружает пресет по имени. Возвращает словарь параметров."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT parameters FROM presets WHERE name = ?', (name,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return json.loads(row[0])
    return None

def get_all_preset_names() -> list:
    """Возвращает список имен всех сохраненных пресетов (отсортированных по имени)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM presets ORDER BY name COLLATE NOCASE ASC')
    rows = cursor.fetchall()
    conn.close()
    
    return [row[0] for row in rows]

def delete_preset(name: str):
    """Удаляет пресет по имени."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM presets WHERE name = ?', (name,))
    conn.commit()
    conn.close()

# Инициализируем БД при импорте модуля
init_db()
