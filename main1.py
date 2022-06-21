import os
import re
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declared_attr

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] ="postgres://kirti:root@localhost/mydb"
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

    name = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True)

class Role(db.Model, BaseMixin, ReprMixin):
    __tablename__ = 'role'

    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.Text, unique=True)


class UserRole(db.Model, BaseMixin, ReprMixin):
    __tablename__ = 'user_role'
    __repr_fields__ = ['user_id', 'role_id']

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))


@app.route('/')
def hello_world():
    return 'Hello, World!'


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True,port=3000)