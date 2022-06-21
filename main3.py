import os
import re
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] ="postgres://kirti1:root@localhost/db3"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
def to_underscore(name):

    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

class BaseMixin(object):

    @declared_attr
    def __tablename__(self):
        return to_underscore(self.__name__)

    id = db.Column(db.Integer, primary_key=True)
    created_on = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    updated_on = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())


class ReprMixin(object):

    __repr_fields__ = ['id', 'name']

    def __repr__(self):
        fields = {f: getattr(self, f, '<BLANK>') for f in self.__repr_fields__}
        pattern = ['{0}={{{0}}}'.format(f) for f in self.__repr_fields__]
        pattern = ' '.join(pattern)
        pattern = pattern.format(**fields)
        return '<{} {}>'.format(self.__class__.__name__, pattern)


class User(db.Model, BaseMixin, ReprMixin):
    __tablename__ = 'user'

    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(255))
    first_name = db.Column(db.String(40), nullable=False)
    last_name = db.Column(db.String(40))
    profile_picture = db.Column(db.Text())
    bio = db.Column(db.Text())
    active = db.Column(db.Boolean())
    last_login_at = db.Column(db.DateTime())
    date_of_birth = db.Column(db.Date)
    roles = db.relationship('Role', secondary='user_role', back_populates='users')

    @hybrid_property
    def name(self):
        return '{}'.format(self.first_name) + (' {}'.format(self.last_name) if self.last_name else '')

class Role(db.Model, BaseMixin, ReprMixin):
    __tablename__ = 'role'

    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.Text, unique=True)
    users = db.relationship('User', secondary='user_role', back_populates='roles')


class UserRole(db.Model, BaseMixin, ReprMixin):
    __tablename__ = 'user_role'
    __repr_fields__ = ['user_id', 'role_id']

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role', foreign_keys=[role_id])
    user = db.relationship('User', foreign_keys=[user_id])


@app.route('/')
def hello_world():
    return 'Hello, World!'


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True,port=3000)