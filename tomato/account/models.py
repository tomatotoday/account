# -*- coding: utf-8 -*-

from time import mktime

from tomato.account.core import db

class User(db.Model):

    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=False, default='')
    is_enabled = db.Column(db.Boolean(), nullable=False, default=False)

    def is_active(self):
      return self.is_enabled

    def to_dict(self):
        return dict(
            id=self.id,
            nickname=self.nickname,
            description=self.description,
            is_enabled=self.is_enabled,
        )


# Define UserEmail DataModel.
class UserEmail(db.Model):

    __tablename__ = 'user_email'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # User email information
    email = db.Column(db.String(255), nullable=False, unique=True)
    confirmed_at = db.Column(db.DateTime())
    is_primary = db.Column(db.Boolean(), nullable=False, default=False)

    # Relationship
    user = db.relationship('User', uselist=False)


# Define UserAuth DataModel. Make sure to add flask.ext.user UserMixin!!
class UserAuth(db.Model):

    __tablename__ = 'user_auth'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))

    # User authentication information
    password = db.Column(db.String(255), nullable=False, default='')
    reset_password_token = db.Column(db.String(100), nullable=False, default='')

    # Relationships
    user = db.relationship('User', uselist=False, foreign_keys=user_id)


class Client(db.Model):
    # human readable name, not required
    name = db.Column(db.String(40))

    # human readable description, not required
    description = db.Column(db.String(400))

    # creator of the client, not required
    user_id = db.Column(db.ForeignKey('user.id'))
    # required if you need to support client credential
    user = db.relationship('User')

    client_id = db.Column(db.String(40), primary_key=True)
    client_secret = db.Column(db.String(55), unique=True, index=True,
                              nullable=False)

    # public or confidential
    is_confidential = db.Column(db.Boolean)

    _redirect_uris = db.Column(db.Text)
    _default_scopes = db.Column(db.Text)

    @property
    def client_type(self):
        if self.is_confidential:
            return 'confidential'
        return 'public'

    @property
    def redirect_uris(self):
        if self._redirect_uris:
            return self._redirect_uris.split()
        return []

    @property
    def default_redirect_uri(self):
        return self.redirect_uris and self.redirect_uris[0] or None

    @property
    def default_scopes(self):
        if self._default_scopes:
            return self._default_scopes.split()
        return []

    def to_dict(self):
        return dict(
            name=self.name,
            description=self.description,
            user_id=self.user_id,
            client_id=self.client_id,
            client_secret=self.client_secret,
            client_type=self.client_type,
            redirect_uris=self.redirect_uris,
            default_redirect_uri=self.default_redirect_uri,
            default_scopes=self.default_scopes,
        )

class Grant(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE')
    )
    user = db.relationship('User')

    client_id = db.Column(
        db.String(40), db.ForeignKey('client.client_id'),
        nullable=False,
    )
    client = db.relationship('Client')

    code = db.Column(db.String(255), index=True, nullable=False)

    redirect_uri = db.Column(db.String(255))
    expires = db.Column(db.DateTime)

    _scopes = db.Column(db.Text)

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self

    def to_dict(self):
        return dict(
            id=self.id,
            user_id=self.user_id,
            client_id=self.client_id,
            code=self.code,
            redirect_uri=self.redirect_uri,
            expires=mktime(self.expires.timetuple()),
            scopes=self.scopes,
        )

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []


class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(
        db.String(40), db.ForeignKey('client.client_id'),
        nullable=False,
    )
    client = db.relationship('Client')

    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id')
    )
    user = db.relationship('User')

    # currently only bearer is supported
    token_type = db.Column(db.String(40))

    access_token = db.Column(db.String(255), unique=True)
    refresh_token = db.Column(db.String(255), unique=True)
    expires = db.Column(db.DateTime)
    _scopes = db.Column(db.Text)

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []

    def to_dict(self):
        return dict(
            id=self.id,
            client_id=self.client_id,
            user_id=self.user_id,
            token_type=self.token_type,
            access_token=self.access_token,
            refresh_token=self.refresh_token,
            expires=self.expires,
            scopes=self.scopes,
        )
