from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, SelectField, SubmitField, DecimalField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange
from models import User

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=80, message='Username must be between 3 and 80 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Invalid email address')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=6, message='Password must be at least 6 characters')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username is already taken')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email is already registered')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(message='Username is required')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required')
    ])

class AddWalletForm(FlaskForm):
    currency = StringField('Currency', validators=[
        DataRequired(message='Currency is required'),
        Length(min=3, max=3, message='Currency must be 3 characters')
    ])

class TransferForm(FlaskForm):
    recipient = StringField('Recipient Username', validators=[
        DataRequired(message='Recipient username is required')
    ])
    amount = FloatField('Amount', validators=[
        DataRequired(message='Amount is required')
    ])
    currency = SelectField('Currency', validators=[
        DataRequired(message='Currency is required')
    ])

class DepositForm(FlaskForm):
    amount = DecimalField('Amount', validators=[
        DataRequired(message='Please enter an amount'),
        NumberRange(min=0.01, message='Amount must be greater than 0')
    ])
    currency = SelectField('Currency', choices=[
        ('USD', 'USD'),
        ('EUR', 'EUR'),
        ('GBP', 'GBP'),
        ('RWF', 'RWF')
    ], validators=[DataRequired(message='Please select a currency')])