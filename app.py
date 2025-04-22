from flask import Flask, render_template, redirect, url_for, flash, request, session, g
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from forms import RegisterForm, LoginForm, AddWalletForm, TransferForm, DepositForm, CurrencyConversionForm
from config import Config
from models import db, User, Wallet, Transaction
from datetime import datetime
import requests
import os
import logging
from flask_mail import Mail, Message
from logging.handlers import RotatingFileHandler
import traceback

# Configure logging
logging.basicConfig(level=Config.LOG_LEVEL,
                   format=Config.LOG_FORMAT,
                   handlers=[
                       RotatingFileHandler(Config.LOG_FILE, maxBytes=10000, backupCount=3),
                       logging.StreamHandler()
                   ])
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
csrf = CSRFProtect(app)
mail = Mail(app)

# Create database tables
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        logger.error(traceback.format_exc())

@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])

@app.route('/')
def index():
    try:
        if g.user:
            return redirect(url_for('dashboard'))
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        logger.error(traceback.format_exc())
        return render_template('500.html'), 500

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
            
            # Send login notification email
            try:
                msg = Message(
                    'Login Notification - Ndiha-sha',
                    sender=app.config['MAIL_DEFAULT_SENDER'],
                    recipients=[user.email]
                )
                msg.body = f'''
                Hello {user.username},
                
                You have successfully logged into your Ndiha-sha account.
                
                Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
                IP Address: {request.remote_addr}
                
                If this was not you, please contact support immediately.
                
                Thank you for using Ndiha-sha!
                '''
                mail.send(msg)
                logger.info(f"Login notification email sent to {user.email}")
            except Exception as e:
                logger.error(f"Failed to send login notification email: {str(e)}")
            
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

@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if not g.user:
        return redirect(url_for('login'))
    
    form = DepositForm()
    if form.validate_on_submit():
        wallet = Wallet.query.filter_by(
            user_id=g.user.id,
            currency=form.currency.data
        ).first()
        
        if not wallet:
            flash('Wallet not found', 'error')
            return redirect(url_for('dashboard'))
        
        # Create transaction
        transaction = Transaction(
            sender_id=g.user.id,
            recipient_id=g.user.id,  # Self-transaction for deposit
            amount=form.amount.data,
            currency=form.currency.data,
            timestamp=datetime.utcnow(),
            type='deposit'
        )
        
        # Update balance
        wallet.balance += form.amount.data
        
        db.session.add(transaction)
        db.session.commit()
        
        # Send email notification
        try:
            msg = Message(
                'Deposit Confirmation - Ndiha-sha',
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[g.user.email]
            )
            msg.body = f'''
            Hello {g.user.username},
            
            Your deposit of {form.amount.data} {form.currency.data} has been successfully processed.
            
            New balance: {wallet.balance} {form.currency.data}
            
            Thank you for using Ndiha-sha!
            '''
            mail.send(msg)
            flash('Deposit successful! Confirmation email sent.', 'success')
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            flash('Deposit successful, but email notification failed to send.', 'warning')
        
        return redirect(url_for('dashboard'))
    
    return render_template('deposit.html', form=form)

@app.route('/logout')
def logout():
    if 'user_id' in session:
        session.pop('user_id', None)
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 Error: {str(error)}")
    logger.error(traceback.format_exc())
    return render_template('500.html'), 500

@app.errorhandler(404)
def not_found_error(error):
    logger.error(f"404 Error: {str(error)}")
    return render_template('404.html'), 404

def get_exchange_rate(from_currency, to_currency):
    """Get exchange rate from API"""
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        response = requests.get(url)
        data = response.json()
        return data['rates'][to_currency]
    except Exception as e:
        logger.error(f"Error getting exchange rate: {str(e)}")
        return None

@app.route('/convert', methods=['GET', 'POST'])
def convert_currency():
    form = CurrencyConversionForm()
    if form.validate_on_submit():
        from_currency = form.from_currency.data
        to_currency = form.to_currency.data
        amount = form.amount.data
        notes = form.notes.data

        # Get exchange rate
        rate = get_exchange_rate(from_currency, to_currency)
        if not rate:
            flash('Error getting exchange rate. Please try again.', 'danger')
            return redirect(url_for('dashboard'))

        # Calculate converted amount
        converted_amount = amount * rate

        # Create transaction records
        from_wallet = Wallet.query.filter_by(
            user_id=g.user.id,
            currency=from_currency
        ).first()
        to_wallet = Wallet.query.filter_by(
            user_id=g.user.id,
            currency=to_currency
        ).first()

        if not from_wallet or not to_wallet:
            flash('Please add wallets for both currencies first.', 'danger')
            return redirect(url_for('dashboard'))

        if from_wallet.balance < amount:
            flash('Insufficient balance in source wallet.', 'danger')
            return redirect(url_for('dashboard'))

        try:
            # Update balances
            from_wallet.balance -= amount
            to_wallet.balance += converted_amount

            # Create transaction records
            from_transaction = Transaction(
                wallet_id=from_wallet.id,
                amount=-amount,
                transaction_type='conversion',
                notes=f"Converted to {to_currency} at rate {rate}"
            )
            to_transaction = Transaction(
                wallet_id=to_wallet.id,
                amount=converted_amount,
                transaction_type='conversion',
                notes=f"Converted from {from_currency} at rate {rate}"
            )

            db.session.add(from_transaction)
            db.session.add(to_transaction)
            db.session.commit()

            flash(f'Successfully converted {amount} {from_currency} to {converted_amount:.2f} {to_currency}', 'success')
            return redirect(url_for('dashboard'))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during currency conversion: {str(e)}")
            flash('An error occurred during conversion. Please try again.', 'danger')
            return redirect(url_for('dashboard'))

    return render_template('modals/convert.html', form=form)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)