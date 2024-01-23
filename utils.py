from database import cursor, conn


def is_authorized(user_id):
    # Проверяем, есть ли пользователь в базе данных
    cursor.execute("SELECT * FROM authorized_users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    if result:
        return True
    else:
        return False


# Функция добавления пользователя в базу данных
def add_user_to_database(user_id):
    if not is_authorized(user_id):
        # Выполнение SQL-запроса для добавления пользователя
        cursor.execute("INSERT INTO authorized_users (user_id) VALUES (?)", (user_id,))
        conn.commit()


def get_users():
    # Получаем всех пользователей
    cursor.execute("SELECT * FROM authorized_users")
    result = cursor.fetchall()
    return result

