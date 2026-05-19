from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
import bcrypt
import random

app = Flask(__name__)
app.secret_key = 'aurabank_secret_secure_key'

# MySQL Configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'      # Replace with your MySQL username
app.config['MYSQL_PASSWORD'] = 'prakash'  # Replace with your MySQL password
app.config['MYSQL_DB'] = 'aurabank_db'

mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['fullname']
        email = request.form['email']
        pwd = request.form['password']
        pin = request.form['pin']
        
        
        hashed_pwd = bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        hashed_pin = bcrypt.hashpw(pin.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO users(fullname, email, password, transaction_pin) VALUES (%s, %s, %s, %s)", (name, email, hashed_pwd, hashed_pin))
            user_id = cur.lastrowid
            
            # Auto-generate a unique 10 digit account number
            acc_num = "".join([str(random.randint(0, 9)) for _ in range(10)])
            cur.execute("INSERT INTO accounts(user_id, account_number, balance) VALUES (%s, %s, 1000.00)", (user_id, acc_num))
            
            mysql.connection.commit()
            flash('Registration successful! Your opening balance is $1,000.00', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            mysql.connection.rollback()
            flash('Email already registered or internal error.', 'danger')
        finally:
            cur.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        pwd_candidate = request.form['password']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, fullname, password FROM users WHERE email = %s", [email])
        user = cur.fetchone()
        cur.close()
        
        if user and bcrypt.checkpw(pwd_candidate.encode('utf-8'), user[2].encode('utf-8')):
            session['logged_in'] = True
            session['user_id'] = user[0]
            session['username'] = user[1]    
            return redirect(url_for('index'))
        else:
            flash('Invalid login credentials.', 'danger')
            
    return render_template('login.html')
 
@app.route('/userprofile')
def userprofile():
    return render_template('userprofile.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT account_number, balance FROM accounts WHERE user_id = %s", [session['user_id']])
    account = cur.fetchone()
    cur.close()
    return render_template('dashboard.html', account=account)

@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if not session.get('logged_in'): return redirect(url_for('login'))
    if request.method == 'POST':
        amount = float(request.form['amount'])
        pin_candidate = request.form['pin']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT transaction_pin FROM users WHERE id = %s", [session['user_id']])
        hashed_pin = cur.fetchone()[0]
        
        if bcrypt.checkpw(pin_candidate.encode('utf-8'), hashed_pin.encode('utf-8')):
            cur.execute("SELECT id, balance FROM accounts WHERE user_id = %s", [session['user_id']])
            acc = cur.fetchone()
            new_balance = float(acc[1]) + amount
            
            cur.execute("UPDATE accounts SET balance = %s WHERE id = %s", (new_balance, acc[0]))
            cur.execute("INSERT INTO transactions(account_id, type, amount) VALUES (%s, 'Deposit', %s)", (acc[0], amount))
            mysql.connection.commit()
            flash(f'Successfully deposited ${amount:.2f}', 'success')
        else:
            flash('Incorrect secure PIN.', 'danger')
        cur.close()
        return redirect(url_for('dashboard'))
    return render_template('deposit.html')

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if not session.get('logged_in'): return redirect(url_for('login'))
    if request.method == 'POST':
        amount = float(request.form['amount'])
        pin_candidate = request.form['pin']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT transaction_pin FROM users WHERE id = %s", [session['user_id']])
        hashed_pin = cur.fetchone()[0]
        
        if bcrypt.checkpw(pin_candidate.encode('utf-8'), hashed_pin.encode('utf-8')):
            cur.execute("SELECT id, balance FROM accounts WHERE user_id = %s", [session['user_id']])
            acc = cur.fetchone()
            
            if float(acc[1]) >= amount:
                new_balance = float(acc[1]) - amount
                cur.execute("UPDATE accounts SET balance = %s WHERE id = %s", (new_balance, acc[0]))
                cur.execute("INSERT INTO transactions(account_id, type, amount) VALUES (%s, 'Withdrawal', %s)", (acc[0], amount))
                mysql.connection.commit()
                flash(f'Successfully withdrew ${amount:.2f}', 'success')
            else:
                flash('Insufficient account funds.', 'warning')
        else:
            flash('Incorrect secure PIN.', 'danger')
        cur.close()
        return redirect(url_for('dashboard'))
    return render_template('withdraw.html')

@app.route('/statements', methods=['GET', 'POST'])
def statements():
    if not session.get('logged_in'): return redirect(url_for('login'))
    transactions = None
    
    if request.method == 'POST':
        pin_candidate = request.form['pin']
        cur = mysql.connection.cursor()
        cur.execute("SELECT transaction_pin FROM users WHERE id = %s", [session['user_id']])
        hashed_pin = cur.fetchone()[0]
        
        if bcrypt.checkpw(pin_candidate.encode('utf-8'), hashed_pin.encode('utf-8')):
            cur.execute("""
                SELECT t.type, t.amount, t.timestamp FROM transactions t 
                JOIN accounts a ON t.account_id = a.id 
                WHERE a.user_id = %s ORDER BY t.timestamp DESC
            """, [session['user_id']])
            transactions = cur.fetchall()
        else:
            flash('Incorrect PIN verification access blocked.', 'danger')
        cur.close()
    return render_template('statements.html', transactions=transactions)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))
 

if __name__ == '__main__':
    app.run(debug=True)