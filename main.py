from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User, Wallet, Transaction
from config import Config
from ai_fraud_detection import FraudDetector
import bcrypt
import requests
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
fraud_detector = FraudDetector()

# Initialize database
with app.app_context():
    db.create_all()

def get_exchange_rate(from_currency, to_currency):
    # Fetch exchange rate from API
    api_key = app.config['EXCHANGE_RATE_API_KEY']
    url = f"https://v6.exchangerate-api.com/v6/{api_key}/pair/{from_currency}/{to_currency}"
    try:
        response = requests.get(url)
        data = response.json()
        return data['conversion_rate']
    except:
        return 1.0  # Fallback to 1:1 if API fails

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        # Check if user exists
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash('Username or email already exists.')
            return redirect(url_for('register'))
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create user
        user = User(username=username, password_hash=password_hash.decode('utf-8'), email=email)
        db.session.add(user)
        db.session.commit()
        
        # Create default USD wallet
        wallet = Wallet(user_id=user.id, currency='USD', balance=0.0)
        db.session.add(wallet)
        db.session.commit()
        
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user)

@app.route('/add_wallet', methods=['POST'])
def add_wallet():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    currency = request.form['currency'].upper()
    user_id = session['user_id']
    
    # Check if wallet exists
    if Wallet.query.filter_by(user_id=user_id, currency=currency).first():
        flash(f'{currency} wallet already exists.')
        return redirect(url_for('dashboard'))
    
    wallet = Wallet(user_id=user_id, currency=currency, balance=0.0)
    db.session.add(wallet)
    db.session.commit()
    flash(f'{currency} wallet added.')
    return redirect(url_for('dashboard'))

@app.route('/transfer', methods=['POST'])
def transfer():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    sender_id = session['user_id']
    recipient_username = request.form['recipient']
    amount = float(request.form['amount'])
    currency = request.form['currency'].upper()
    
    sender_wallet = Wallet.query.filter_by(user_id=sender_id, currency=currency).first()
    recipient = User.query.filter_by(username=recipient_username).first()
    
    if not sender_wallet or not recipient:
        flash('Invalid wallet or recipient.')
        return redirect(url_for('dashboard'))
    
    if sender_wallet.balance < amount:
        flash('Insufficient balance.')
        return redirect(url_for('dashboard'))
    
    # Create transaction
    transaction = Transaction(
        wallet_id=sender_wallet.id,
        amount=amount,
        currency=currency,
        recipient_id=recipient.id,
        timestamp=datetime.utcnow()
    )
    
    # AI fraud detection
    fraud_detector.train(Transaction.query.all())  # Train on all transactions
    if fraud_detector.predict(transaction):
        transaction.status = 'flagged'
        db.session.add(transaction)
        db.session.commit()
        flash('Transaction flagged for review.')
        return redirect(url_for('dashboard'))
    
    # Convert currency if recipient's wallet is different
    recipient_wallet = Wallet.query.filter_by(user_id=recipient.id, currency=currency).first()
    if not recipient_wallet:
        recipient_wallet = Wallet(user_id=recipient.id, currency=currency, balance=0.0)
        db.session.add(recipient_wallet)
    
    sender_wallet.balance -= amount
    recipient_wallet.balance += amount  # Simplified; assumes same currency for now
    
    transaction.status = 'completed'
    db.session.add(transaction)
    db.session.commit()
    
    flash('Transfer successful.')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)