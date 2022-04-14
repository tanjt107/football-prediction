import mysql.connector
import psycopg
from abc import ABC, abstractmethod

class Database(ABC):
    @abstractmethod
    def connection(self, **kwargs):
        pass

    @abstractmethod
    def cursor(self):
        pass

    
class MySQLDatabase(Database):
    # TODO Type Hint
    @property
    def connection(self, **kwargs):
        return mysql.connector(**kwargs)

    # TODO Type Hint
    @property
    def cursor(self):
        return self.connection.cursor()

class PostgreSQL(Database):
    @property
    def connection(self, **kwargs) -> psycopg.Connection:
        return psycopg.connect(**kwargs)

    @property
    def cursor(self)-> psycopg.Cursor:
        return self.connection.cursor()
        