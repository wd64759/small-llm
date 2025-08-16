import mysql.connector
import sys
import project_root_finder
PROJECT_ROOT = project_root_finder.root.as_posix()
sys.path.append(PROJECT_ROOT)

from config.env import Config

conn = mysql.connector.connect(
    host=Config.MYSQL_HOST,
    port=Config.MYSQL_PORT,
    user=Config.MYSQL_USER,
    password=Config.MYSQL_PASSWORD,
    database=Config.MYSQL_DB
)

cursor = conn.cursor()
cursor.execute("SELECT * FROM cityark.fund_info limit 10")
print(cursor.fetchall())

cursor.close()
conn.close()