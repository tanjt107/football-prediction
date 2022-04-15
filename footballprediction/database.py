import mysql.connector
from abc import ABC, abstractmethod


class Database(ABC):
    @abstractmethod
    def connect(self, **kwargs):
        pass

    @abstractmethod
    def cursor(self):
        pass


class MySQLDatabase(Database):
    @property
    def connect(self, **kwargs) -> mysql.connector.connection.MySQLConnection:
        return mysql.connector(**kwargs)

    @property
    def cursor(self) -> mysql.connector.cursor.MySQLCursor:
        return self.connect.cursor()
