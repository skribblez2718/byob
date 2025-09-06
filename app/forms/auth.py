from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[
            DataRequired(message='Username is required'),
            Length(min=1, max=50, message='Username must be between 1 and 50 characters')
        ],
        render_kw={'autocomplete': 'username'}
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required'),
            Length(min=8, max=256, message='Password must be between 8 and 256 characters')
        ],
        render_kw={'autocomplete': 'current-password'}
    )
    submit = SubmitField('Sign In')


class MFAForm(FlaskForm):
    code = StringField(
        'Authentication Code',
        validators=[
            DataRequired(message='Authentication code is required'),
            Length(min=6, max=10, message='Authentication code must be between 6 and 10 characters')
        ],
        render_kw={
            'placeholder': 'Enter 6-digit code',
            'maxlength': '6',
            'pattern': '[0-9]{6}',
            'autocomplete': 'one-time-code'
        }
    )
    submit = SubmitField('Verify')
