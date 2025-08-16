from dbutils.pooled_db import PooledDB
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

class DBHelper:
    def __init__(self, host, user, password, database):
        self.pool = PooledDB(
            creator=mysql.connector,
            maxconnections=6,
            mincached=2,
            maxcached=5,
            maxshared=3,
            blocking=True,
            maxusage=None,
            setsession=[],
            ping=0,
            host=host,
            user=user,
            password=password,
            database=database,
        )

    def get_connection(self):
        return self.pool.connection()

    def close_connection(self, conn):
        conn.close()

    def execute_query(self, query, params=None):
        conn = self.get_connection()
        cursor = conn.cursor()