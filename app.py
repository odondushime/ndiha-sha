from flask import Flask, render_template, redirect, url_for, flash, request, session, g
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from forms import RegisterForm, LoginForm, AddWalletForm, TransferForm
from config import Config
from models import db, User, Wallet, Transaction
from datetime import datetime
import requests
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
csrf = CSRFProtect(app)

# Create database tables
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        # Don't raise the error, let the app continue

@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])

@app.route('/')
def index():
    if g.user:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if g.user:
        return redirect(url_for('dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form, user=None)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'error')
    
    return render_template('login.html', form=form, user=None)

@app.route('/dashboard')
def dashboard():
    if not g.user:
        return redirect(url_for('login'))
    
    wallets = Wallet.query.filter_by(user_id=g.user.id).all()
    
    # Initialize forms
    transfer_form = TransferForm()
    add_wallet_form = AddWalletForm()
    
    # Set currency choices for transfer form
    transfer_form.currency.choices = [(wallet.currency, wallet.currency) for wallet in wallets]
    
    # Get recent transactions
    transactions = Transaction.query.filter(
        (Transaction.sender_id == g.user.id) | (Transaction.recipient_id == g.user.id)
    ).order_by(Transaction.timestamp.desc()).limit(10).all()
    
    return render_template('dashboard.html', 
                         user=g.user,
                         wallets=wallets,
                         transactions=transactions,
                         transfer_form=transfer_form,
                         add_wallet_form=add_wallet_form)

@app.route('/add_wallet', methods=['POST'])
def add_wallet():
    if not g.user:
        return redirect(url_for('login'))
    
    form = AddWalletForm()
    if form.validate_on_submit():
        wallet = Wallet(
            user_id=g.user.id,
            currency=form.currency.data,
            balance=0.0
        )
        db.session.add(wallet)
        db.session.commit()
        flash(f'Wallet for {form.currency.data} added successfully!', 'success')
    
    return redirect(url_for('dashboard'))

@app.route('/transfer', methods=['POST'])
def transfer():
    if not g.user:
        return redirect(url_for('login'))
    
    form = TransferForm()
    if form.validate_on_submit():
        # Get sender's wallet
        sender_wallet = Wallet.query.filter_by(
            user_id=g.user.id,
            currency=form.currency.data
        ).first()
        
        if not sender_wallet or sender_wallet.balance < form.amount.data:
            flash('Insufficient funds', 'error')
            return redirect(url_for('dashboard'))
        
        # Get recipient's wallet
        recipient = User.query.filter_by(username=form.recipient.data).first()
        if not recipient:
            flash('Recipient not found', 'error')
            return redirect(url_for('dashboard'))
        
        recipient_wallet = Wallet.query.filter_by(
            user_id=recipient.id,
            currency=form.currency.data
        ).first()
        
        if not recipient_wallet:
            flash('Recipient does not have a wallet for this currency', 'error')
            return redirect(url_for('dashboard'))
        
        # Create transaction
        transaction = Transaction(
            sender_id=g.user.id,
            recipient_id=recipient.id,
            amount=form.amount.data,
            currency=form.currency.data,
            timestamp=datetime.utcnow()
        )
        
        # Update balances
        sender_wallet.balance -= form.amount.data
        recipient_wallet.balance += form.amount.data
        
        db.session.add(transaction)
        db.session.commit()
        
        flash('Transfer successful!', 'success')
    
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal Server Error: {str(error)}")
    return render_template('500.html'), 500

@app.errorhandler(404)
def not_found_error(error):
    logger.error(f"Not Found Error: {str(error)}")
    return render_template('404.html'), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)