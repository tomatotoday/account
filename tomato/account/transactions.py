# -*- coding: utf-8 -*-

import string
from random import choice
from time import mktime
from datetime import datetime
from datetime import timedelta

from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

from tomato.account.core import db
from tomato.account.models import Client
from tomato.account.models import Grant
from tomato.account.models import Token
from tomato.account.models import User
from tomato.account.models import UserEmail
from tomato.account.models import UserAuth

class AccountError(Exception):
    pass

class AlreadyRegistered(AccountError):
    pass

def get_token_by_access_token(access_token):
    token = Token.query.filter_by(access_token=access_token).first()
    return token and token.to_dict()

def get_token_by_access_token(refresh_token):
    token = Token.query.filter_by(refresh_token=refresh_token).first()
    return token and token.to_dict()

def save_token(client_id, user_id, expires_in, access_token,
               refresh_token, token_type, scopes):
    # make sure that every client has only one token connected to a user
    tokens = Token.query.filter_by(client_id=client_id, user_id=user_id)
    for token in tokens:
        db.session.delete(token)

    expires = datetime.utcnow() + timedelta(seconds=expires_in)

    token = Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type=token_type,
        _scopes=scopes,
        expires=expires,
        client_id=client_id,
        user_id=user_id,
    )
    db.session.add(token)
    db.session.commit()
    return token.to_dict()

def get_client(client_id):
    client = Client.query.filter_by(client_id=client_id).first()
    return client and client.to_dict()

def _gen(length):
    return "".join(choice(string.digits+string.ascii_lowercase) for x in range(length))

def save_client(name, description, user_id, is_confidential, redirect_uris, default_scopes):
    client = Client(
        name=name,
        description=description,
        user_id=user_id,
        is_confidential=is_confidential,
        _redirect_uris=' '.join(redirect_uris),
        _default_scopes=' '.join(default_scopes),
        client_id=_gen(32),
        client_secret=_gen(40),
    )
    db.session.add(client)
    db.session.commit()
    return client.to_dict()

def get_grant(client_id, code):
    grant = Grant.query.filter_by(client_id=client_id, code=code).first()
    return grant and grant.to_dict()

def save_grant(client_id, code, redirect_uri, scopes, user_id):
    expires = datetime.utcnow() + timedelta(seconds=100)
    grant = Grant(
        client_id=client_id,
        code=code,
        redirect_uri=redirect_uri,
        _scopes=' '.join(scopes),
        user_id=user_id,
        expires=expires,
    )
    db.session.add(grant)
    db.session.commit()
    return grant.to_dict()

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

def get_user_by_token(token, token_type='bearer'):
    token = Token.query.filter_by(token=token).first()
    if not token:
        return
    return token.user.to_dict()

def register_user_by_email(nickname, email, password):
    try:
        user = User(nickname=nickname, is_enabled=True)
        db.session.add(user)
        db.session.flush()
        user_email = UserEmail(user_id=user.id, email=email, is_primary=True)
        db.session.add(user_email)
        salted_password = generate_password_hash(password)
        user_auth = UserAuth(user_id=user.id, password=salted_password)
        db.session.add(user_auth)
        db.session.commit()
        return user.to_dict()
    except IntegrityError:
        db.session.rollback()
        raise AlreadyRegistered(email)
