from dbutils.pooled_db import PooledDB
import mysql.connector
from config.env import Config
from dotenv import load_dotenv

load_dotenv()

class DBHelper:
    def __init__(self):
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
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            port=Config.MYSQL_PORT,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
        )

    def get_connection(self):
        return self.pool.connection()

    def close_connection(self, conn):
        conn.close()

    def execute_query(self, query, params=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def execute_update(self, query, params=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()