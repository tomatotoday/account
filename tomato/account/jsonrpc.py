# -*- coding: utf-8 -*-

from time import mktime
from datetime import datetime

from tomato.account.core import db
from tomato.account.core import jsonrpc
from tomato.account.models import Client
from tomato.account.models import Grant
from tomato.account.models import Token

@jsonrpc.method('OAuth2.get_token_by_access_token')
def get_token_by_access_token(access_token):
    token = Token.query.filter_by(access_token=access_token).first()
    return token and token.to_dict()

@jsonrpc.method('OAuth2.get_token_by_refresh_token')
def get_token_by_access_token(refresh_token):
    token = Token.query.filter_by(refresh_token=refresh_token).first()
    return token and token.to_dict()

@jsonrpc.method('OAuth2.save_token')
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
        scopes=scopes,
        expires=expires,
        client_id=client_id,
        user_id=user_id,
    )
    db.session.add(token)
    db.session.commit()
    return token.to_dict()

@jsonrpc.method('OAuth2.get_client')
def get_client(client_id):
    client = Client.query.filter_by(client_id=client_id).first()
    return client and dict(
        name=client.name,
        description=client.description,
        user_id=client.user_id,
        client_id=client.client_id,
        client_secret=client.client_secret,
        client_type=client.client_type,
        redirect_uris=client.redirect_uris,
        default_scopes=client.default_scopes,
    )

@jsonrpc.method('OAuth2.get_grant')
def get_grant(client_id, code):
    grant = Grant.query.filter_by(client_id=client_id, code=code).first()
    return grant and grant.to_dict()

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
