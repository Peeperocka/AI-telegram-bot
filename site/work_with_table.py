import sqlite3
import os


class DatabaseHandler:
    def __init__(self, db_name):
        self.db_name = db_name
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()

    def create_table(self, table_name: str, columns: str) -> None:
        """
        Создает таблицу в базе данных.

        :param table_name: Название таблицы
        :param columns: Строка с определением колонок (например, "id INTEGER, name TEXT")
        """
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})"
        self.cursor.execute(query)
        self.connection.commit()

    def drop_table(self, table_name: str) -> None:
        """
        Удаляет таблицу из базы данных.

        :param table_name: Название таблицы
        """
        self.cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        self.connection.commit()

    def insert_row(self, table_name: str, data: dict) -> None:
        """
        Добавляет строку в таблицу.

        :param table_name: Название таблицы
        :param data: Словарь с данными (ключи - названия колонок)
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        self.cursor.execute(query, tuple(data.values()))
        self.connection.commit()

    def delete_database(self) -> None:
        """Удаляет файл базы данных и закрывает соединение"""
        self.connection.close()
        if os.path.exists(self.db_name):
            os.remove(self.db_name)

    def __del__(self):
        """Закрывает соединение при удалении объекта"""
        self.connection.close()