# -*- coding: utf-8 -*-

from pytest import fixture
from tomato.account import jsonrpc

@fixture
def user(app, db):
    return jsonrpc.register_user_by_email('nickname', 'test@example.org', 'test')

@fixture
def client(user):
    return jsonrpc.save_client('client', 'desc', user['id'], True, ['http://x.y.z'], ['scope'])

def test_validate_user(user):
    assert user['id']
    assert user['nickname'] == 'nickname'
    assert user == jsonrpc.validate_user('test@example.org', 'test')
    assert not jsonrpc.validate_user('test@example.org', 'wrong password')

def test_client(client):
    assert jsonrpc.get_client(client['client_id']) == client
