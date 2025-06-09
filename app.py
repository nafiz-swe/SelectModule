

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import threading
import time
import webbrowser
import uuid
import os
import psycopg2
import urllib.parse as up
from psycopg2.extras import RealDictCursor


# Try importing pyautogui safely
try:
    import pyautogui
    PYAUTO_AVAILABLE = True
except Exception as e:
    print(f"⚠️ pyautogui could not be loaded: {e}")
    PYAUTO_AVAILABLE = False

app = Flask(__name__)
app.secret_key = "f8a1d5b65cc9473d931b407ec8e8573b"

TRIGGER_TEXTS = ["Select Module", "Select module", "select module", "SELECT MODULES"]
watching = {"b1": False, "b2": False, "kolkata_b1": False}
trigger_audio = {"b1": False, "b2": False, "kolkata_b1": False}

TARGET_URLS = {
    "b1": "https://www.goethe.de/ins/bd/en/spr/prf/gzb1.cfm",
    "b2": "https://www.goethe.de/ins/bd/en/spr/prf/gzb2.cfm",
    "kolkata_b1": "https://www.goethe.de/ins/in/en/sta/kol/prf/gzb1.cfm"
}

ALARM_LIST = [
    ("selectmodule_alarm.mp3", "Morning"),
    ("2-MorningBird1.mp3", "Morning Bird-1"),
    ("3-MorningBird2.mp3", "Morning Bird-2"),
    ("7-Melody.mp3", "Melody"),
    ("4-La_ilaha_ilallah.mp3", "La ilaha illallah"),
    ("5-Subhanallah.mp3", "Subhanallah"),
    ("6-Fire.mp3", "Fire"),
    ("8-kgf.mp3", "KGF Theme")
]

def get_db_connection():
    up.uses_netloc.append("postgres")
    url = up.urlparse("postgres://goethealarm_user:C8LQZlObxUXWyT9CNFMkq8KZVh9M4nQm@dpg-d13agcjuibrs7380e3p0-a.singapore-postgres.render.com/goethealarm")

    return psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port or 5432
    )

def create_table():
    conn = get_db_connection()
    cur = conn.cursor()

    # users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            full_name VARCHAR(255),
            email VARCHAR(255) NOT NULL,
            phone VARCHAR(20),
            subscription VARCHAR(100),
            plan_days INTEGER,
            amount NUMERIC(10, 2),
            start_date TIMESTAMP,
            end_date TIMESTAMP,
            devices TEXT,
            is_active BOOLEAN DEFAULT TRUE
        );
    """)

    # user_devices table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_devices (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255),
            device_id VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("Tables created successfully.")

# এটা একবার কল করলেই যথেষ্ট
create_table()

def get_device_id():
    device_id = request.cookies.get("device_id")
    if not device_id:
        device_id = str(uuid.uuid4())
    return device_id

def click_screen_center():
    if PYAUTO_AVAILABLE:
        try:
            screenWidth, screenHeight = pyautogui.size()
            x, y = screenWidth // 2, screenHeight // 2
            for i in range(3):
                pyautogui.click(x, y)
                time.sleep(0.1)
        except Exception as e:
            print(f"⚠️ pyautogui error during click: {e}")
    else:
        print("ℹ️ pyautogui not available; skipping screen click.")

def check_condition_and_open(level):
    global watching, trigger_audio
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--blink-settings=imagesEnabled=false")
    driver = webdriver.Chrome(options=options)

    while watching[level]:
        try:
            driver.get(TARGET_URLS[level])
            time.sleep(1)
            
            # Change this:
            # body_text = driver.page_source
            
            # To this:
            body_text = driver.find_element("tag name", "body").text

            if any(text in body_text for text in TRIGGER_TEXTS):
                # Trigger front-end to open tab and play alarm
                trigger_audio[level] = True
                watching[level] = False
                print(f"✅ {level.upper()} - Select Module Found!")
            else:
                print(f"❌ {level.upper()} - Not found.")
        except Exception as e:
            print("⚠️ Error:", e)
        time.sleep(1)

    driver.quit()


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')



@app.route('/admin/eurozoom', methods=['GET', 'POST'])
def admin_create_user():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']
        subscription = request.form['subscription']
        plan_days = int(request.form['plan_days'])
        amount = float(request.form['amount'])

        # এখানে start_date ও end_date নেওয়া হচ্ছে স্ট্রিং হিসেবে
        start_date_str = request.form['start_date']
        end_date_str = request.form['end_date']

        # এখানে স্ট্রিং থেকে datetime অবজেক্টে কনভার্ট করবেন
        from datetime import datetime
        start_date = datetime.strptime(start_date_str, "%Y-%m-%dT%H:%M")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%dT%H:%M")

        devices = int(request.form['devices'])  # devices যদি সংখ্যায় নিতে চান তাহলে int করতে পারেন

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (full_name, email, phone, subscription, plan_days, amount, start_date, end_date, devices)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (full_name, email, phone, subscription, plan_days, amount, start_date, end_date, devices))
            conn.commit()
            msg = "User added successfully!"
        except psycopg2.Error as err:
            msg = f"Error: {err}"
        finally:
            cursor.close()
            conn.close()
        return render_template('admin/eurozoom.html', message=msg)

    return render_template('admin/eurozoom.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'email' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        identifier = request.form['identifier']

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT * FROM users
            WHERE (email = %s OR phone = %s) AND is_active = TRUE
        """, (identifier, identifier))
        user = cursor.fetchone()

        if user:
            device_id = get_device_id()

            cursor.execute("SELECT COUNT(*) AS device_count FROM user_devices WHERE email = %s", (user['email'],))
            device_info = cursor.fetchone()
            current_device_count = device_info['device_count']

            allowed_devices = int(user.get('devices', 1))

            cursor.execute("SELECT * FROM user_devices WHERE email = %s AND device_id = %s", (user['email'], device_id))
            existing = cursor.fetchone()

            if not existing and current_device_count >= allowed_devices:
                cursor.close()
                conn.close()
                return render_template('login.html', error="🚫 Maximum device limit reached.")

            if not existing:
                cursor.execute("INSERT INTO user_devices (email, device_id) VALUES (%s, %s)", (user['email'], device_id))
                conn.commit()

            cursor.close()
            conn.close()

            session['email'] = user['email']
            resp = make_response(redirect(url_for('dashboard')))
            resp.set_cookie("device_id", device_id, max_age=30*24*60*60)
            return resp

        else:
            return render_template('login.html', error="Invalid your data or subscription expired.")

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE email = %s", (session['email'],))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template(
        'dashboard.html',
        alarms=ALARM_LIST,
        session_alarm=session.get('alarm_file'),
        user=user
    )


@app.route('/logout')
def logout():
    session.clear() 
    return redirect(url_for('home'))



@app.route('/set-alarm', methods=['POST'])
def set_alarm():
    selected_alarm = request.form.get('alarm_choice')
    if selected_alarm:
        session['alarm_file'] = selected_alarm
    return redirect(url_for('dashboard'))



@app.route('/start-watch/<level>')
def start_watch(level):
    normalized = level.replace('-', '_')
    watching[normalized] = True
    trigger_audio[normalized] = False
    threading.Thread(target=check_condition_and_open, args=(normalized,)).start()
    return redirect(url_for('dashboard') + f"?watch={normalized}")



@app.route("/alarm")
def alarm():
    return render_template("alarm.html")

@app.route("/check-audio/<level>")
def check_audio(level):
    # এখানে শর্ত বসান, উদাহরণ:
    if level.lower() == "b1":
        # যদি condition match করে
        return jsonify({"play": True})
    return jsonify({"play": False})


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)