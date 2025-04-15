from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class AddWalletForm(FlaskForm):
    currency = StringField('Currency', validators=[DataRequired(), Length(min=3, max=3)])
    submit = SubmitField('Add Wallet')

class TransferForm(FlaskForm):
    recipient = StringField('Recipient Username', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    currency = SelectField('Currency', validators=[DataRequired()])
    submit = SubmitField('Transfer')