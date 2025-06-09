# db_config.py
import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",           # প্রয়োজনে পরিবর্তন করো
        password="",           # প্রয়োজনে পাসওয়ার্ড দাও
        database="goethe_alarm_db"
    )
