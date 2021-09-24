import os
import time
from siyu import app
from siyu import db
from siyu.models import UserTable, PlayTable, CommentTable, ThreadTable, PlayReward, PlayVote, CommentVote, ThreadVote, AvatarTable, Subscribers
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from siyu.controller.sql import save_check, update_check
from siyu.s3_api import list_files, download_file, upload_file
from flask import jsonify
from collections import defaultdict
from siyu.awsconfig import CLOUDFRONT
from sqlalchemy import and_
from collections import defaultdict
from siyu.send_sms import send_message


class SubscribeController():
    def if_follow(self, visit_account_id, login_user_id):
        visit_account = UserTable.query.filter_by(id=visit_account_id).first()
        login_user = UserTable.query.filter_by(id=login_user_id).first()
        if login_user.is_following(visit_account):
            result = {'response': {'followed': True}}
        else:
            result = {'response': {'followed': False}}
        return result

    def is_subscribing(self, creator_id, user_id):
        creator = UserTable.query.filter_by(id=creator_id).first()
        user = UserTable.query.filter_by(id=user_id).first()
        subscription = Subscribers.query.filter_by(
            creator_id=creator_id, fan_id=user_id).first()
        if subscription:
            tier = subscription.tier_id
            result = {'response': {'subscribed': True, 'tier_id': tier}}
        else:
            result = {'response': {'subscribed': False}}
        return result

    def subscribe(self, creator_id, tier_id, user_id):
        subscribe_exist = Subscribers.query.filter_by(
            creator_id=creator_id, fan_id=user_id).first()
        if not subscribe_exist:  # 是否已经订阅，若无，创立新的订阅
            creator = UserTable.query.filter_by(id=creator_id).first()
            user = UserTable.query.filter_by(id=user_id).first()
            if creator and user:  # 用户存在
                # follower will follow the followed_user
                user.number_following += 1
                creator.number_follower += 1
                msg_1 = update_check()
                date = datetime.now()
                subscription = Subscribers(
                    creator_id=creator_id, tier_id=tier_id, fan_id=user_id, subscribe_date=date)
                msg_2 = save_check(subscription)
                (code, message) = (1, msg_1+msg_2) if msg_1 or msg_2 else (
                    0, '')  # msg for saving in user table
            else:
                (code, message) = (1, 'creator or user does not exist')
        else:
            subscribe_exist.status = 1  # 当前订阅的deactive掉
            msg_1 = update_check()
            date = datetime.now()
            subscription = Subscribers(
                creator_id=creator_id, tier_id=tier_id, fan_id=user_id, subscribe_date=date)
            msg_2 = save_check(subscription)  # 创立一个新的subscription
            (code, message) = (1, msg_1+msg_2) if msg_1 or msg_2 else (
                0, '')  # msg for saving in user table

        result = {'code': code, 'msg': message}
        return result

    def unsubscribe(self, creator_id, user_id, tier_id):
        creator = UserTable.query.filter_by(id=creator_id).first()
        user = UserTable.query.filter_by(id=user_id).first()
        # follower will unfollow the followed_user
        print(creator_id, user_id, 'user_id')  # ?????test this one
        db.session.query(Subscribers).filter(and_(Subscribers.creator_id == creator_id,
                                                  Subscribers.fan_id == user_id)).filter(Subscribers.tier_id == tier_id).delete()
        msg = update_check()
        if not msg:
            user.number_following -= 1
            creator.number_follower -= 1
            msg2 = update_check()
            (code, message) = (1, msg2) if msg2 else (0, '')
            result = {'code': code, 'msg': message}
        else:
            result = {'code': 1, 'msg': "You have not subscribe"}
        return result

    def get_subscriber(self, tier_id_list, play_name, play_id, creator, twilio_number):
        '''获取该play的订阅者并发出'''
        result = defaultdict(list)
        subscribers = Subscribers.query.filter(Subscribers.tier_id.in_(
            tier_id_list)).order_by(Subscribers.subscribe_date.desc())
        if subscribers:
            for subscriber in subscribers:
                sid = self.send_post_to_subscriber(play_name, play_id, creator,
                                                   subscriber.fan.phone_number, twilio_number,
                                                   source='createPost', medium='sms')
                result['response'].append(
                    {'tier_id': subscriber.tier_id, 'fan_id': subscriber.fan_id, 'fan_username': subscriber.fan.username,
                        'fan_tel': subscriber.fan.phone_number, 'fan_email': subscriber.fan.email, 'subscribe_date': subscriber.subscribe_date, 'twilio_sid': sid})
            # print(result)
            play_object = PlayTable.query.filter_by(id=play_id).first()
            play_object.sms_count += len(result['response'])
            update_check()
        else:
            result['response'] = []

        return result

    def get_all_subscriber(self, creator_id):
        result = defaultdict(list)
        subscribers = Subscribers.query.filter_by(
            creator_id=creator_id).order_by(Subscribers.tier_id.desc())
        if subscribers:
            for subscriber in subscribers:
                result['response'].append({'fan_id': subscriber.fan_id, 'fan_username': subscriber.fan.username,
                                           'fan_tel': subscriber.fan.phone_number, 'fan_email': subscriber.fan.email, 'subscribe_date': subscriber.subscribe_date})
        else:
            result['response'] = []

        return result

    def send_post_to_subscriber(self, play_name, play_id, creator, phone_number, twilio_number,
                                source = '', medium = ''):
        # creator = UserTable.query.filter_by(name=creator).first()
        utm_source = 'utm_source={}'.format(source) if source else ''
        utm_medium = 'utm_medium={}'.format(medium) if medium else ''
        utm = '&'.join({utm_source, utm_medium}) if len(utm_medium) > 0 and len(
            utm_source) > 0 else utm_medium + utm_source


        content = "{} has just posted a play: {}, see https://channels.housechan.com/post/{}{}".format(
            creator, play_name, play_id, '?' + utm if utm else '')
        print("content", content)
        sid = send_message(content, phone_number, twilio_number)
        return sid
