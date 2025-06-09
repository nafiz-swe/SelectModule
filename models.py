from db_config import get_db_connection
from datetime import datetime, timedelta

def create_or_update_user(email, phone, plan_days, subscription):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    start_date = datetime.now()
    end_date = start_date + timedelta(days=plan_days)

    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()

    if user:
        cursor.execute("""
            UPDATE users
            SET phone = %s, plan_days = %s, subscription = %s, start_date = %s, end_date = %s, is_active = 1
            WHERE email = %s
        """, (phone, plan_days, subscription, start_date, end_date, email))
    else:
        cursor.execute("""
            INSERT INTO users (email, phone, plan_days, subscription, start_date, end_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (email, phone, plan_days, subscription, start_date, end_date))

    conn.commit()
    cursor.close()
    conn.close()

def get_user_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user
