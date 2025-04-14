from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()  # Initialize SQLAlchemy instance

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique user ID
    username = db.Column(db.String(80), unique=True, nullable=False)  # Unique username
    password_hash = db.Column(db.String(120), nullable=False)  # Hashed password
    email = db.Column(db.String(120), unique=True, nullable=False)  # Unique email
    wallets = db.relationship('Wallet', backref='user', lazy=True)  # Link to wallets

class Wallet(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique wallet ID
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Link for currencies
    currency = db.Column(db.String(3), nullable=False)  # Currency code (e.g., USD, EUR)
    balance = db.Column(db.Float, default=0.0)  # Wallet balance
    transactions = db.relationship('Transaction', backref='wallet', lazy=True)  # Link to transactions

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique transaction ID
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallet.id'), nullable=False)  # Wallet involved
    amount = db.Column(db.Float, nullable=False)  # Transaction amount
    currency = db.Column(db.String(3), nullable=False)  # Transaction currency
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Recipient user
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # Transaction time
    status = db.Column(db.String(20), default='pending')  # Status (pending, completed, flagged)
    recipient = db.relationship('User', foreign_keys=[recipient_id])  # Link to recipient