# -*- coding: utf-8 -*-

from pytest import fixture
from mock import Mock, patch

from tomato.account.app import create_app

@fixture
def app(request):
    application = create_app()
    application.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite://'
    })
    ctx = application.app_context()
    ctx.push()
    request.addfinalizer(ctx.pop)
    return application

@fixture
def client(app):
    return app.test_client()

@fixture
def db(app, request):
    from tomato.account.core import db
    db.init_app(app)
    db.create_all()
    request.addfinalizer(db.drop_all)
    return db
