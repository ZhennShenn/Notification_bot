# Подключение к базе данных SQLite
import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Создание таблицы для хранения авторизованных пользователей
cursor.execute('''CREATE TABLE IF NOT EXISTS authorized_users
                  (user_id INTEGER PRIMARY KEY)''')
conn.commit()