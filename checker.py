# checker.py
import requests

CONDITIONS = ['Select modules', 'Select Modules', 'select modules', 'SELECT MODULES']

def check_goethe_page(url):
    try:
        response = requests.get(url, timeout=10)
        html = response.text
        return any(condition in html for condition in CONDITIONS)
    except Exception as e:
        print(f"Error checking Goethe page: {e}")
        return False
