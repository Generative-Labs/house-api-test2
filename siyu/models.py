from siyu import db
from flask_paginate import Pagination, get_page_parameter
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql import func

followers = db.Table('followers', db.Column('follower_id', db.Integer, db.ForeignKey(
    'user_table.id')), db.Column('followed_id', db.Integer, db.ForeignKey('user_table.id')), db.Column('follow_on', db.TIMESTAMP))
# a many-to-many relationship requires an association table. The foreign keys in this table are both pointing at entries in the user table,
# subscribers = db.Table('subscribers', db.Column('fan_id', db.Integer, db.ForeignKey('user_table.id')),
#                        db.Column('creator_id', db.Integer,
#                                  db.ForeignKey('user_table.id')),
#                        db.Column('subscribe_on', db.TIMESTAMP), db.Column('tier_id', db.Integer))
# 两个价位level的订阅(1 普通订阅（可查阅play_visibility 0/1） 2 premium订阅-0/1/2)，如果没有订阅，只能查阅play_visibility 0 的内容


class UserTable(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # if user is creator,default false
    creator = db.Column(db.Integer, default=0)  # 1 is creator, 0 not
    username = db.Column(db.Text, unique=True, nullable=True)  # handle
    bio = db.Column(db.Text)
    name = db.Column(db.Text, nullable=True)
    password = db.Column(db.String, nullable=True)  # save hashed
    registered_on = db.Column(db.DateTime, nullable=True)
    number_follower = db.Column(db.Integer, default=0)  # 有多少订阅者
    number_following = db.Column(db.Integer, default=0)  # 订阅了多少人
    twilio_number = db.Column(db.Text)
    # name on the profile, can be changed
    phone_number = db.Column(db.Text, unique=True)
    customer_id = db.Column(db.Text)  # stripe id
    confirmed = db.Column(db.Boolean, default=False)
    # verified by email/phone or not
    email = db.Column(db.Text, unique=True)
    links = db.Column(JSON)
    followed = db.relationship(
        'UserTable', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
    # user1.followed.append(user2)  make the first follow the second
    # subscribed = db.relationship(
    #     'UserTable', secondary=subscribers,
    #     primaryjoin=(subscribers.c.fan_id == id),
    #     secondaryjoin=(subscribers.c.creator_id == id),
    #     backref=db.backref('subscribers', lazy='dynamic'), lazy='dynamic')
    # fan.subscribe.append(creator) make the fan subscribe the creator
    video = db.relationship("PlayTable", backref='author',
                            lazy=True)  # user创建play  user创建评论
    comment = db.relationship("CommentTable", backref='author', lazy=True)
    avatar = db.relationship("AvatarTable", backref='author', lazy=True)
    creator_tier = db.relationship('TierTable', backref='author', lazy=True)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
            self.follower_add()

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    # def subscribe(self, user):
    #     if not self.is_subscribing(user):  # if not subscribe this creator
    #         # subscribe fucntion add this user(creator) as its
    #         self.subscribed.append(user)

    # def unsubscribe(self, user):
    #     if self.is_subscribing(user):
    #         self.subscribed.remove(user)

    # def is_subscribing(self, user):
    #     return self.subscribed.filter(subscribers.c.creator_id == user.id).count() > 0


class AvatarTable(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    image_url = db.Column(db.Text)
    date = db.Column(db.TIMESTAMP)
    user_id = db.Column(db.Integer, db.ForeignKey(
        UserTable.id), nullable=False)


class PlayTable(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    play_url = db.Column(db.Text, nullable=False)
    play_thumbnail_url = db.Column(db.Text)
    # a list of visible tier_id
    play_visibility = db.Column(db.ARRAY(db.Integer))
    play_name = db.Column(db.Text, nullable=False)
    play_description = db.Column(db.Text)  # introduction
    play_tag = db.Column(db.ARRAY(db.String))
    vote_number = db.Column(db.Integer, default=0)
    save_number = db.Column(db.Integer, default=0)
    visit_number = db.Column(db.Integer, default=0)
    comment_number = db.Column(db.Integer, default=0)
    share_id = db.Column(db.Text)  # hash过得id，用于分享出去
    sms_count = db.Column(db.Integer, default=0)
    date = db.Column(db.TIMESTAMP)
    user_id = db.Column(db.Integer, db.ForeignKey(
        UserTable.id), nullable=False)
    comment = db.relationship(
        "CommentTable", backref='play', lazy=True)


class CommentTable(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.TIMESTAMP)
    vote_number = db.Column(db.Integer, default=0)
    reply_number = db.Column(db.Integer, default=0)
    play_id = db.Column(db.Integer, db.ForeignKey(
        PlayTable.id), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(
        UserTable.id), nullable=False)
    thread = db.relationship("ThreadTable", backref='comment', lazy=True)


class ThreadTable(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.TIMESTAMP)
    vote_number = db.Column(db.Integer, default=0)
    parent_id = db.Column(db.Integer, db.ForeignKey(
        'thread_table.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey(
        CommentTable.id), nullable=False)
    replies = db.relationship(
        'ThreadTable', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')


class PlayReward(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False)
    play_id = db.Column(db.Integer, db.ForeignKey(
        PlayTable.id), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(
        UserTable.id), nullable=False)
    date = db.Column(db.TIMESTAMP)


class PlayVote(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    play_id = db.Column(db.Integer, db.ForeignKey(
        PlayTable.id), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(
        UserTable.id), nullable=False)
    date = db.Column(db.TIMESTAMP)

    @ classmethod
    def exists(cls, play_id, user_id):  # one user cannot vote twice
        exists = db.session.query(PlayVote.id).filter_by(
            play_id=play_id).filter_by(user_id=user_id).scalar()
        if not exists:
            return True


class CommentVote(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    comment_id = db.Column(db.Integer, db.ForeignKey(
        CommentTable.id), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(
        UserTable.id), nullable=False)
    date = db.Column(db.TIMESTAMP)

    @ classmethod
    def exists(cls, comment_id, user_id):  # one user cannot vote twice
        exists = db.session.query(CommentVote.id).filter_by(
            comment_id=comment_id).filter_by(user_id=user_id).scalar()
        if not exists:
            return True


class ThreadVote(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    thread_id = db.Column(db.Integer, db.ForeignKey(
        ThreadTable.id), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(
        UserTable.id), nullable=False)
    date = db.Column(db.TIMESTAMP)

    @ classmethod
    def exists(cls, thread_id, user_id):  # one user cannot vote twice
        exists = db.session.query(ThreadVote.id).filter_by(
            thread_id=thread_id).filter_by(user_id=user_id).scalar()
        if not exists:
            return True


class TierTable(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tier_name = db.Column(db.Text)
    tier_price = db.Column(db.Integer, default=0)
    tier_perks = db.Column(db.ARRAY(db.String))
    creator_id = db.Column(db.Integer, db.ForeignKey(
        UserTable.id), nullable=False)
    create_date = db.Column(db.TIMESTAMP)
    price_id = db.Column(db.Text)  # stripe price id
    product_id = db.Column(db.Text)  # sripe product id
    # subscribe = db.relationship(
    #     "Subscribers", backref='tier', lazy=True)


class Subscribers(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    creator_id = db.Column(db.Integer, db.ForeignKey(UserTable.id))
    fan_id = db.Column(db.Integer, db.ForeignKey(UserTable.id))
    tier_id = db.Column(db.Integer, db.ForeignKey(TierTable.id))
    subscribe_date = db.Column(db.DateTime, nullable=True)
    creator = relationship("UserTable", foreign_keys=[creator_id])
    fan = relationship("UserTable", foreign_keys=[fan_id])
    status = db.Column(db.Integer, default=0)  # 0 is active, 1 not


# class StripeTable(db.Model):
#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
