from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_mysqldb import MySQL
import MySQLdb
import MySQLdb.cursors

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_me'

# 1. MySQL Connection Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'prakash'  # 👈 Make sure this matches your MySQL root password!
app.config['MYSQL_DB'] = 'smart_bank'

mysql = MySQL(app)

# 2. AUTOMATIC DATABASE & TABLE CREATOR
def initialize_database():
    try:
        conn = MySQLdb.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            passwd=app.config['MYSQL_PASSWORD']
        )
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS smart_bank;")
        cursor.execute("USE smart_bank;")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            email VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            balance DECIMAL(15, 2) DEFAULT 1000.00
        );
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            type VARCHAR(20) NOT NULL,
            amount DECIMAL(15, 2) NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("🎉 Database and tables are ready and verified!")
    except Exception as e:
        print(f"⚠️ Automatic setup failed. Please check your MySQL password! Error: {e}")

# Run the database initial check right now
initialize_database()

# -----------------------------------------------------------------
# 3. APPLICATION ROUTES
# -----------------------------------------------------------------

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        try:
            cursor = mysql.connection.cursor()
            cursor.execute('INSERT INTO users (username, email, password) VALUES (%s, %s, %s)', (username, email, password))
            mysql.connection.commit()
            cursor.close()
            return redirect(url_for('login'))
        except Exception as e:
            return f"Error during registration: {e}"
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        user = cursor.fetchone()
        cursor.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            msg = 'Invalid credentials!'
    return render_template('login.html', msg=msg)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    u_id = session['user_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    if request.method == 'POST':
        action = request.form.get('action')
        amount_str = request.form.get('amount', '0')
        amount = float(amount_str) if amount_str else 0.0
        
        # Get Current Balance securely
        cursor.execute('SELECT balance FROM users WHERE id = %s', (u_id,))
        current_balance = float(cursor.fetchone()['balance'])
        
        if action == 'deposit' and amount > 0:
            new_balance = current_balance + amount
            cursor.execute('UPDATE users SET balance = %s WHERE id = %s', (new_balance, u_id))
            cursor.execute('INSERT INTO transactions (user_id, type, amount) VALUES (%s, %s, %s)', (u_id, 'Deposit', amount))
        elif action == 'withdraw' and 0 < amount <= current_balance:
            new_balance = current_balance - amount
            cursor.execute('UPDATE users SET balance = %s WHERE id = %s', (new_balance, u_id))
            cursor.execute('INSERT INTO transactions (user_id, type, amount) VALUES (%s, %s, %s)', (u_id, 'Withdrawal', amount))
        
        mysql.connection.commit()
        
    # Gather fresh data for UI render
    cursor.execute('SELECT balance FROM users WHERE id = %s', (u_id,))
    user_data = cursor.fetchone()
    
    cursor.execute('SELECT type, amount, timestamp FROM transactions WHERE user_id = %s ORDER BY timestamp DESC', (u_id,))
    statements = cursor.fetchall()
    cursor.close()
    
    return render_template('dashboard.html', balance=user_data['balance'], statements=statements)

@app.route('/investments')
def investments():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    options = [
        {"name": "Alpha High-Yield Index Fund", "rate": "7.5% APY", "risk": "Low"},
        {"name": "Smart-AI Auto Crypto Vault", "rate": "12.4% APY", "risk": "High"},
        {"name": "Green Energy Bond Tier-1", "rate": "5.2% APY", "risk": "Very Low"}
    ]
    return render_template('investments.html', options=options)

@app.route('/ai-assistant', methods=['POST'])
def ai_assistant():
    user_msg = request.json.get('message', '').lower()
    
    if 'interest' in user_msg or 'invest' in user_msg:
        reply = "Our Alpha High-Yield Index Fund is matching records at 7.5% APY this quarter. Tap the Investments portal to lock it in!"
    elif 'balance' in user_msg or 'money' in user_msg:
        reply = "You can view your real-time liquidity directly on the main dashboard layout banner."
    elif 'secure' in user_msg or 'hack' in user_msg:
        reply = "This instance runs transactional state commits over database sandboxing protocols preventing rollbacks."
    else:
        reply = "Hi! I'm your Smart Bank AI. Ask me about 'best investment rates', 'checking balance instructions', or 'security protocols'."
        
    return jsonify({"reply": reply})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)