# -*- coding: utf-8 -*-

import string
from random import choice
from time import mktime
from datetime import datetime
from datetime import timedelta

from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask_jsonrpc.exceptions import InvalidParamsError
from wtforms import Form
from wtforms.fields import StringField
from wtforms.fields import IntegerField
from wtforms.fields import PasswordField
from wtforms.fields import FieldList
from wtforms.validators import Email
from wtforms.validators import Length
from wtforms.validators import DataRequired
from wtforms.validators import ValidationError

from tomato.account.core import db
from tomato.account.core import jsonrpc
import tomato.account.transactions as txc
from tomato.account.consts import ALLOWED_SCOPES
from tomato.account.models import Client
from tomato.account.models import Grant
from tomato.account.models import Token
from tomato.account.models import User
from tomato.account.models import UserEmail
from tomato.account.models import UserAuth


class AccessTokenForm(Form):
    access_token = StringField('Access Token', [Length(min=1, )])

@jsonrpc.method('OAuth2.get_token_by_access_token')
def get_token_by_access_token(access_token):
    form = AccessTokenForm(data={'access_token': access_token})
    if not form.validate():
        raise InvalidParamsError
    return txc.get_token_by_access_token(access_token)

class RefreshTokenForm(Form):
    refresh_token = StringField('Refresh Token', [Length(min=1, )])

@jsonrpc.method('OAuth2.get_token_by_refresh_token')
def get_token_by_refresh_token(refresh_token):
    form = RefreshTokenForm(data={'refresh_token': refresh_token})
    if not form.validate():
        raise InvalidParamsError
    return txc.get_token_by_refresh_token(refresh_token)

class SaveTokenForm(Form):
    client_id = StringField('Client ID', [DataRequired(), Length(min=1, )])
    user_id = IntegerField('User ID', [DataRequired(), ])
    expires_in = IntegerField('Expires In', [DataRequired(), ])
    access_token = StringField('Access Token', [DataRequired(), ])
    refresh_token = StringField('Refresh Token', [DataRequired(), ])
    token_type = StringField('Token Type', [DataRequired(), ])
    scopes = FieldList(StringField('Scope', [DataRequired(), ]))

    def validate_user_id(self, field):
        if not User.query.get(field.data):
            raise ValidationError('User must be existed.')

    def validate_token_type(self, field):
        if field.data != 'bearer':
            raise ValidationError(
                    'Currently only support `bearer`, but given `%s`' % field.data)

    def validate_scopes(self, field):
        invalid_scopes = [
            scope for scope in field.data
            if scope not in ALLOWED_SCOPES
        ]
        if invalid_scopes:
            raise ValidationError(
                    'Invalid scopes: %s' % ','.join(invalid_scopes))

@jsonrpc.method('OAuth2.save_token')
def save_token(client_id, user_id, expires_in, access_token,
               refresh_token, token_type, scopes):
    form = SaveTokenForm(data={
        'client_id': client_id,
        'user_id': user_id,
        'expires_in': expires_in,
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': token_type,
        'scopes': scopes,
    })
    if not form.validate():
        raise InvalidParamsError

    return txc.save_token(**field.data)

@jsonrpc.method('OAuth2.get_client')
def get_client(client_id):
    return txc.get_client(client_id)


@jsonrpc.method('OAuth2.get_grant')
def get_grant(client_id, code):
    return txc.get_grant(client_id, code)

@jsonrpc.method('OAuth2.save_grant')
def save_grant(client_id, code, redirect_uri, scopes, user_id):
    expires = datetime.utcnow() + timedelta(seconds=100)
    grant = Grant(
        client_id=client_id,
        code=code,
        redirect_uri=request.redirect_uri,
        _scopes=' '.join(request.scopes),
        user_id=user_id,
        expires=expires,
    )
    db.session.add(grant)
    db.session.commit()
    return grant.to_dict()

@jsonrpc.method('Account.validate_user')
def validate_user(username, password):
    email = UserEmail.query.filter_by(email=username).first()
    if not email:
        return
    user_id = email.user_id
    auth = UserAuth.query.filter_by(user_id=user_id).first()
    if not auth:
        return
    if not check_password_hash(auth.password, password):
        return
    return email.user.to_dict()

@jsonrpc.method('Account.get_user_by_token')
def get_user_by_token(token, token_type='bearer'):
    return txc.get_user_by_token(token, token_type)

class RegisterByEmail(Form):
    nickname = StringField('Nickname', [Length(min=1, max=32)])
    email = Email()
    password = PasswordField('Password', [DataRequired(), ])

@jsonrpc.method('Account.register_user_by_email')
def register_user_by_email(nickname, email, password):
    form = RegisterByEmail(data={
        'nickname': nickname,
        'email': email,
        'password': password,
    })
    if not form.validate():
        raise InvalidParamsError
    try:
        return txc.register_user_by_email(
            nickname=nickname,
            email=email,
            password=password,
        )
    except txc.AlreadyRegistered:
        raise InvalidParamsError
