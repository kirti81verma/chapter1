import os
import re

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func, select, UniqueConstraint, Index

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgres://kirti:root@localhost/mydb1"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db = SQLAlchemy(app)
db.create_all()


def to_underscore(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class BaseMixin(object):

    @declared_attr
    def __tablename__(self):
        return to_underscore(self.__name__)

    id = db.Column(db.Integer, primary_key=True, index=True)
    created_on = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    updated_on = db.Column(db.TIMESTAMP, onupdate=db.func.current_timestamp())


class ReprMixin(object):
    # __repr_fields__ = ['id', 'name']

    def __repr__(self):
        fields = {f: getattr(self, f, '<BLANK>') for f in self.__repr_fields__}
        pattern = ['{0}={{{0}}}'.format(f) for f in self.__repr_fields__]
        pattern = ' '.join(pattern)
        pattern = pattern.format(**fields)
        return '<{} {}>'.format(self.__class__.__name__, pattern)


class User(db.Model, BaseMixin, ReprMixin):
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean(), default=False)
    last_login_at = db.Column(db.DateTime())
    mobile_number = db.Column(db.String(10), unique=True, index=True)

    roles = db.relationship('Role', back_populates='users', secondary='user_role')
    user_profile = db.relationship("UserProfile", back_populates="user",
                                   uselist=False, cascade='all, delete-orphan',
                                   lazy='select')
    comments = db.relationship('Comment', back_populates='commenter', uselist=True,
                               lazy='dynamic')
    ratings = db.relationship('UserRating', back_populates='rater', uselist=True,
                              lazy='dynamic')


@hybrid_property
def name(self):
    return '{}'.format(self.user_profile.first_name) + ('{}'.format(self.user_profile.last_name) if  self.user_profile.last_name else '')


class UserProfile(db.Model, BaseMixin, ReprMixin):
    # __repr_fields__ = ['id', 'first_name']

    first_name = db.Column(db.String(40), nullable=False)
    last_name = db.Column(db.String(40))
    profile_picture = db.Column(db.Text())
    bio = db.Column(db.Text())
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.Enum('male', 'female', 'other', name='varchar'))
    marital_status = db.Column(db.Enum('single', 'married', 'divorced', 'widowed', name='varchar'))
    education = db.Column(db.Enum('undergraduate', 'graduate', 'post_graduate', name='varchar'))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), unique=True, index=True)

    user = db.relationship('User', back_populates="user_profile", single_parent=True)


class Role(db.Model, BaseMixin, ReprMixin):
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.Text, unique=True)

    users = db.relationship('User', secondary='user_role', back_populates='roles')


class UserRole(db.Model, BaseMixin, ReprMixin):
    __repr_fields__ = ['user_id', 'role_id']

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

    role = db.relationship('Role', foreign_keys=[role_id])
    user = db.relationship('User', foreign_keys=[user_id])

    UniqueConstraint(role_id, user_id, 'role_user_un')


class Post(db.Model, BaseMixin, ReprMixin):
    __repr_fields__ = ['id', 'slug']

    slug = db.Column(db.String(55), unique=True, nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    data = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)

    author = db.relationship('User', single_parent=True, foreign_keys=[author_id])
    ratings = db.relationship('UserRating', back_populates='post', uselist=True,
                              lazy='dynamic')
    comments = db.relationship('Comment', back_populates='post', uselist=True,
                               lazy='dynamic')

    @hybrid_property
    def avg_rating(self):
        return self.ratings.with_entities(func.Avg(UserRating.rating)).filter(UserRating.post_id == self.id).scalar()

    @hybrid_property
    def total_comments(self):
        return self.comments.with_entities(func.Count(Comment.id)).filter(Comment.post_id == self.id).scalar()

    @avg_rating.expression
    def avg_rating(cls):
        return select([func.Avg(UserRating.rating)]).where(cls.id == UserRating.post_id).as_scalar()


class Comment(db.Model, BaseMixin, ReprMixin):
    __repr_fields__ = ['id', 'commented_by']

    data = db.Column(db.Text, nullable=False)
    is_moderated = db.Column(db.Boolean(), default=False)

    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), index=True)
    commented_by = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), index=True)

    post = db.relationship('Post', foreign_keys=[post_id], back_populates='comments')
    commenter = db.relationship('User', foreign_keys=[commented_by], back_populates='comments')
    parent_comment = db.relationship('Comment', remote_side='Comment.id')
    children_comment = db.relationship('Comment', remote_side='Comment.parent_comment_id')


class UserRating(db.Model, BaseMixin, ReprMixin):
    __repr_fields__ = ['rating', 'post_id', 'rated_by']

    rating = db.Column(db.SmallInteger, nullable=False)

    rated_by = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), index=True)

    post = db.relationship('Post', back_populates='ratings', foreign_keys=[post_id])
    rater = db.relationship('User', foreign_keys=[rated_by], back_populates='ratings')

    UniqueConstraint(rated_by, post_id, 'user_post_un')


@app.route('/')
def hello_world():
    return 'Hello, World!'

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True,port=5000)