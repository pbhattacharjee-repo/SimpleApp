"""
Deliberately Insecure Flask Application for CodeQL Testing
WARNING: This code contains intentional security vulnerabilities
DO NOT use in production or any real environment
"""

from flask import Flask, request, render_template_string, redirect
import sqlite3
import os
import pickle
import subprocess

app = Flask(__name__)

DATABASE = 'users.db'
ADMIN_PASSWORD = 'admin123'
SECRET_KEY = 'hardcoded_secret_key_12345'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT,
            email TEXT
        )
    ''')
    cursor.execute("INSERT INTO users (username, password, email) VALUES ('admin', 'admin123', 'admin@example.com')")
    conn.commit()
    conn.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        cursor.execute(query)
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return f"Welcome {username}!"
        return "Login failed"
    
    return '''
        <form method="post">
            Username: <input name="username"><br>
            Password: <input name="password" type="password"><br>
            <input type="submit" value="Login">
        </form>
    '''

@app.route('/ping')
def ping():
    host = request.args.get('host', 'localhost')
    result = os.popen(f'ping -c 1 {host}').read()
    return f'<pre>{result}</pre>'

@app.route('/read_file')
def read_file():
    filename = request.args.get('file', 'default.txt')
    try:
        with open(filename, 'r') as f:
            content = f.read()
        return f'<pre>{content}</pre>'
    except:
        return 'File not found'

@app.route('/greet')
def greet():
    name = request.args.get('name', 'Guest')
    template = '<h1>Hello {{ name }}!</h1>'
    return render_template_string(template, name=name)

@app.route('/load_data', methods=['POST'])
def load_data():
    data = request.form.get('data')
    try:
        obj = pickle.loads(bytes.fromhex(data))
        return f'Loaded: {obj}'
    except:
        return 'Invalid data'

@app.route('/parse_xml', methods=['POST'])
def parse_xml():
    import xml.etree.ElementTree as ET
    xml_data = request.data
    try:
        root = ET.fromstring(xml_data)
        return f'Parsed: {root.tag}'
    except:
        return 'Invalid XML'

@app.route('/redirect')
def redirect_url():
    url = request.args.get('url', '/')
    return redirect(url)


@app.route('/hash_password')
def hash_password():
    import hashlib
    password = request.args.get('password', '')
    hashed = hashlib.md5(password.encode()).hexdigest()
    return f'Hashed password: {hashed}'


@app.route('/debug')
def debug():
    return f'''
    <h2>Debug Info</h2>
    <p>Database: {DATABASE}</p>
    <p>Admin Password: {ADMIN_PASSWORD}</p>
    <p>Secret Key: {SECRET_KEY}</p>
    <p>Environment: {os.environ}</p>
    '''


@app.route('/execute')
def execute():
    cmd = request.args.get('cmd', 'ls')
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return f'<pre>{result.stdout}</pre>'


@app.route('/admin/delete_user')
def delete_user():
    user_id = request.args.get('id')
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM users WHERE id = {user_id}")
    conn.commit()
    conn.close()
    return 'User deleted'

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0')