import sqlite3
from datetime import datetime
from contextlib import contextmanager

DATABASE_PATH = 'business_processes.db'

@contextmanager
def get_db_connection():
    """Контекстный менеджер для подключения к БД."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Инициализация базы данных."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                name TEXT NOT NULL,
                username TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица бизнес-процессов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                responsible TEXT NOT NULL,
                frequency TEXT NOT NULL,
                deadline_time TEXT NOT NULL,
                reminder1 TEXT NOT NULL,
                reminder2 TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()

def register_user(telegram_id, name, username=None):
    """Регистрация нового пользователя."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users (telegram_id, name, username)
            VALUES (?, ?, ?)
        ''', (telegram_id, name, username))
        conn.commit()

def get_user_by_telegram_id(telegram_id):
    """Получить пользователя по Telegram ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def add_process(name, responsible, frequency, deadline_time, reminder1, reminder2):
    """Добавить бизнес-процесс."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO processes (name, responsible, frequency, deadline_time, reminder1, reminder2)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, responsible, frequency, deadline_time, reminder1, reminder2))
        conn.commit()

def get_all_processes():
    """Получить все бизнес-процессы"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM processes ORDER BY responsible, deadline_time')
        return [dict(row) for row in cursor.fetchall()]

def get_processes_by_responsible(responsible_name):
    """Получить процессы по ответственному."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM processes 
            WHERE responsible = ? 
            ORDER BY deadline_time
        ''', (responsible_name,))
        return [dict(row) for row in cursor.fetchall()]

def add_sample_data():
    """Добавить тестовые данные бизнес-процессов."""
    processes = [
        {
            'name': 'Заполнить таблицу показателей',
            'responsible': 'Кирилл',
            'frequency': 'Раз в сутки',
            'deadline_time': '23:59',
            'reminder1': '24ч',
            'reminder2': '2ч'
        },
        {
            'name': 'Посмотреть просмотры конкурентов',
            'responsible': 'Кирилл',
            'frequency': 'Раз в день',
            'deadline_time': '18:00',
            'reminder1': '24ч',
            'reminder2': '1ч'
        },
        {
            'name': 'Заполнить КОПы',
            'responsible': 'Иван',
            'frequency': 'Раз в день',
            'deadline_time': '10:30',
            'reminder1': '24ч',
            'reminder2': '2ч'
        },
        {
            'name': 'Проверить рекламные кампании',
            'responsible': 'Иван',
            'frequency': 'Раз в день',
            'deadline_time': '12:00',
            'reminder1': '24ч',
            'reminder2': '1ч'
        }
    ]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Очищаем таблицу (для тестовых целей)
        cursor.execute('DELETE FROM processes')
        
        # Добавляем процессы
        for process in processes:
            cursor.execute('''
                INSERT INTO processes (name, responsible, frequency, deadline_time, reminder1, reminder2)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                process['name'],
                process['responsible'],
                process['frequency'],
                process['deadline_time'],
                process['reminder1'],
                process['reminder2']
            ))
        
        conn.commit()
