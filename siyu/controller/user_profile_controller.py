import os
import time
from flask import jsonify
from siyu import app
from siyu import db
from siyu.models import UserTable, PlayTable, CommentTable, ThreadTable, PlayReward, PlayVote, CommentVote, ThreadVote, AvatarTable, TierTable
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from siyu.controller.sql import save_check, update_check
from siyu.s3_api import list_files, download_file, upload_file
from siyu.constants import ERROR
from siyu.awsconfig import CLOUDFRONT, LINK_PICS_DIR
import re
from collections import defaultdict
from siyu.utils import generate_confirmation_token, confirm_token
from siyu.send_sms import send_message, available_phone, provision_phone
from siyu.controller.stripe_controller import StripeController


class UserProfileController():
    def create_profile(self, creator, username, name, password,
                       phone_number, email, bio, customer_id, confirmed=False):
        '''
        创建用户，
        '''
        regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
        if not re.search(regex, email):
            result = {'code': 1, 'msg': 'not a valid email'}
            return result
        hashed_password = generate_password_hash(password, method='sha256')

        registered_on = datetime.now()
        user_profile = UserTable(
            creator=creator, username=username, name=name, password=hashed_password,
            registered_on=registered_on, phone_number=phone_number, email=email, bio=bio, customer_id=customer_id,
            confirmed=confirmed)
        msg1 = save_check(user_profile)
        (code, message) = (1, msg1) if msg1 else (
            0, '')  # msg for saving in user table
        result1 = {'code': code, 'msg': message}
        # get default avatar image
        if not result1['code']:
            user_id = UserTable.query.filter_by(username=username).first().id
            image_dir = os.path.join(CLOUDFRONT, 'avatar',
                                     '{}.png'.format(name[0].capitalize()))

            result2 = self.upload_avatar(user_id, '', image_dir)
            # if creator, register a free tier automatically
            if creator:
                self.create_tier(user_id, 'free', 0, ['Free for all'])
            if not result2['code']:
                result2['user_id'] = user_id
                result2['customer_id'] = customer_id
                return result2
            else:
                return {'code': 1, 'msg': 'create user profile:'+result1['msg']+' upload avatar:'+result2['msg']}
        else:
            return {'code': 1, 'msg': 'create user profile:'+result1['msg']}

    def upload_avatar(self, user_id, file, image_dir):
        '''
        用户创建时，会initial名字首字母作为avatar， 从aws 的avatar文件夹中读取。
        自定义，图片上传至aws，文件路径存储在数据库
        '''
        if file:
            response, image_dir = upload_file(file, 'avatar')
        # print('image_dir', image_dir, 'user_id', user_id)
        user = AvatarTable.query.filter_by(user_id=user_id).first()
        if user:
            user.image_url = image_dir
            msg = update_check()
        else:
            avatar = AvatarTable(
                user_id=user_id, image_url=image_dir, date=datetime.now())
            msg = save_check(avatar)
        (code, message) = (1, msg) if msg else (0, '')
        result = {
            'code': code,
            'msg': message,
            'avatar': image_dir
        }
        return result

    def update_profile(self, user_id, phone_number, username, name, email, bio):
        user = UserTable.query.filter_by(id=user_id).first()
        if user:
            user.name = name
            user.phone_number = phone_number
            user.bio = bio
            user.username = username
            # user.email = email #see if email error when '' can be fixed by commenting out
            msg = update_check()
        else:
            msg = ERROR.USER_NOT_EXISTS
        (code, message) = (1, msg) if msg else (0, '')
        result = {
            'code': code,
            'msg': message
        }
        if user:
            result['user_id'] = user.id
            result['avatar'] = user.avatar[0].image_url
        return result

    def get_user_profile(self, visit_username):
        profile = UserTable.query.filter_by(username=visit_username).first()
        if profile:
            result = {'code': 0}
            result['id'] = profile.id
            result['creator'] = profile.creator
            result['username'] = visit_username
            result['name'] = profile.name
            result['bio'] = profile.bio
            result['number_follower'] = profile.number_follower
            result['number_following'] = profile.number_following
            result['avatar'] = profile.avatar[0].image_url
            result['social_links'] = profile.links
        else:
            result = {'code': 1, 'msg': ERROR.USER_NOT_EXISTS}
        # print('profile.avatar', profile.avatar)
        return result

    def get_user_profile_by_id(self, user_id):
        profile = UserTable.query.filter_by(id=user_id).first()
        if profile:
            result = {'code': 0}
            result['id'] = profile.id
            result['creator'] = profile.creator
            result['name'] = profile.name
            result['bio'] = profile.bio
            result['phone_number'] = profile.phone_number
            result['twilio_number'] = profile.twilio_number
        else:
            result = {'code': 1, 'msg': ERROR.USER_NOT_EXISTS}
        return result

    def check_auth(self, phone_number, password):
        if not phone_number or not password:
            data = {'code': 1, 'msg': ERROR.ARGS}
            return data
        user = UserTable.query.filter_by(phone_number=phone_number).first()
        if not user:
            data = {'code': 1, 'msg': ERROR.USER_NOT_EXISTS}
            return data
        else:
            if not check_password_hash(user.password, password):
                data = {'code': 1, 'msg': ERROR.USER_COUNT_OR_PASS}
                return data
        data = {'code': 0, 'msg': '', 'user': user}
        return data

    def create_tier(self, creator_id, tier_name, tier_price, tier_perks):
        create_date = datetime.now()
        tier = TierTable(tier_name=tier_name, tier_price=tier_price,
                         tier_perks=tier_perks, creator_id=creator_id, create_date=create_date)
        msg = save_check(tier)
        (code, message) = (1, msg) if msg else (0, '')
        result = {'code': code, 'msg': message}
        if not result['code']:
            stripe_controller = StripeController()
            # tier = TierTable.query.filter_by(
            #     tier_name=tier_name, tier_price=tier_price).first()
            stripe_result = stripe_controller.create_product(
                tier_name, tier.id, creator_id, tier_price)
            if not stripe_result['code']:
                tier.price_id = stripe_result['message']['price_id']
                tier.product_id = stripe_result['message']['product_id']
                msg = update_check()
            else:
                result['code'] = 1
                result['msg'] = 'stripe create product fail'

            result['tier'] = {'tier_id': tier.id, 'tier_name': tier.tier_name,
                              'creator_id': tier.creator_id, 'price': tier.tier_price, 'product_id': tier.product_id, 'price_id': tier.price_id}
        return result

    def get_tiers(self, creator_id):
        tiers = TierTable.query.filter_by(creator_id=creator_id).order_by(
            TierTable.tier_price.asc())
        result = defaultdict(list)
        if tiers:
            for tier in tiers:
                result['response'].append(
                    {'tier_id': tier.id, 'tier_name': tier.tier_name, 'tier_price': tier.tier_price,
                     'tier_perks': tier.tier_perks, 'creator_id': tier.creator_id, 'product_id': tier.product_id, 'price_id': tier.price_id, 'create_date': tier.create_date})
        else:
            result['response'] = []
        return result

    def get_free_tier(self, creator_id):
        tiers = TierTable.query.filter_by(creator_id=creator_id).order_by(
            TierTable.tier_price.asc())
        result = defaultdict(list)
        if tiers:
            for tier in tiers:
                if tier.tier_price == 0:
                    result['response'].append(
                        {'tier_id': tier.id, 'tier_name': tier.tier_name, 'tier_price': tier.tier_price,
                         'tier_perks': tier.tier_perks, 'creator_id': tier.creator_id, 'product_id': tier.product_id, 'price_id': tier.price_id, 'create_date': tier.create_date})
        else:
            result['response'] = []
        return result

    def choose_number(self, creator_id, twilio_number):
        user = UserTable.query.filter_by(id=creator_id).first()
        if user.creator == 1:
            user.twilio_number = twilio_number
            msg = update_check()
        else:
            msg = ERROR.USER_NOT_EXISTS
        if not msg:
            sid = provision_phone(twilio_number)
        (code, message) = (1, msg) if msg else (0, '')
        result = {'code': code, 'msg': message, 'sid': sid}
        return result
        # def phone_confirmation(self, phone_number):

    def reset_password(self, user_id, reset_password):
        user = UserTable.query.filter_by(id=user_id).first()
        hashed_password = generate_password_hash(
            reset_password, method='sha256')
        if user:
            user.password = hashed_password
            msg = update_check()
        else:
            msg = ERROR.USER_NOT_EXISTS
        (code, message) = (1, msg) if msg else (0, '')
        result = {'code': code, 'msg': message}
        return result

    def change_to_creator(self, user_id):
        user = UserTable.query.filter_by(id=user_id).first()
        if user:
            if not user.creator:
                user.creator = 1
                msg = update_check()
                result = self.create_tier(user_id, 'free', 0, ['Free for all'])
            else:
                msg = ERROR.USER_CREATOR
                result = {'code': 1, 'msg': msg}
        else:
            msg = ERROR.USER_NOT_EXISTS
            result = {'code': 1, 'msg': msg}
        return result

    def update_links(self, user_id, links):
        user = UserTable.query.filter_by(id=user_id).first()
        if user:
            user.links = links
            # user.email = email #see if email error when '' can be fixed by commenting out
            msg = update_check()
        else:
            msg = ERROR.USER_NOT_EXISTS
        (code, message) = (1, msg) if msg else (0, '')
        result = {
            'code': code,
            'msg': message
        }
        if user:
            result['user_id'] = user.id
            result['links'] = user.links
        return result

    def upload_link_pic(self, file):
        path = ""
        if file:
            response, path = upload_file(file, LINK_PICS_DIR)
            if not path:
                print("file_name:", file.filename, "response:", response)
        return path
