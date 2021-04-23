import os
import time
from siyu import app
from siyu import db
from siyu.models import UserTable, PlayTable, CommentTable, ThreadTable, PlayReward, PlayVote, CommentVote, ThreadVote, AvatarTable, TierTable, Subscribers
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from siyu.controller.sql import save_check, update_check
from siyu.s3_api import list_files, download_file, upload_file
from flask import jsonify
from collections import defaultdict
from siyu.awsconfig import CLOUDFRONT
from siyu.controller.subscribe_controller import SubscribeController
from sqlalchemy import or_
import io


class PlayController():
    def get_play(self, visit_account_id, login_user_id, page, offset):
        free_tier_id = TierTable.query.filter_by(
            tier_price=0, creator_id=visit_account_id).first().id  # free tier_id
        play_list = PlayTable.query.filter_by(user_id=visit_account_id).order_by(
            PlayTable.date.desc()).paginate(page=page, per_page=offset)
        if play_list:
            if not login_user_id:  # 访客模式下,仅显示free_tier
                visible_play_list = PlayTable.query.filter_by(user_id=visit_account_id).filter(
                    PlayTable.play_visibility.any(free_tier_id)).all()
            # elif visit_account_id == login_user_id:  # 访问自己页面，显示所有
            #     play_list = PlayTable.query.filter_by(user_id=login_user_id).order_by(
            #         PlayTable.date.desc()).paginate(page=page, per_page=offset)  # 按时间倒叙
            elif login_user_id and visit_account_id != login_user_id:
                # check if subscribe
                subscription = Subscribers.query.filter_by(
                    creator_id=visit_account_id, fan_id=login_user_id).first()
                if not subscription:  # 没有订阅。同访客模式
                    visible_play_list = PlayTable.query.filter_by(user_id=visit_account_id).filter(PlayTable.play_visibility.any(
                        free_tier_id)).all()
                else:  # 订阅了。获取订阅的tier_id
                    tier_id = subscription.tier_id
                    visible_play_list = PlayTable.query.filter_by(user_id=visit_account_id).filter(or_(
                        PlayTable.play_visibility.any(free_tier_id), PlayTable.play_visibility.any(tier_id))).all()
            else:  # 访问自己的页面
                visible_play_list = PlayTable.query.filter_by(
                    user_id=login_user_id).order_by(PlayTable.date.desc())
            visible_play_id = [i.id for i in visible_play_list]
            result = defaultdict(list)
            for play in play_list.items:
                if play.id in visible_play_id:
                    visible = 1
                else:
                    visible = 0
                result['response'].append({'play_id': play.id, 'share_id': play.share_id, 'play_url': play.play_url,
                                           'play_name': play.play_name, 'play_description': play.play_description,
                                           'visible_tier_id': play.play_visibility,
                                           'play_tag': play.play_tag, 'vote_number': play.vote_number,
                                           'save_number': play.save_number, 'visit_number': play.visit_number,
                                           'date': play.date, 'comment_number': play.comment_number, 'play_visibility': visible, 'play_thumbnail_url': play.play_thumbnail_url})
        else:
            result['response'] = []

        return result

    def get_single_play(self, share_id):
        play = PlayTable.query.filter_by(share_id=share_id).first()
        creator = UserTable.query.filter_by(id=play.user_id).first()
        result = {'share_id': share_id}
        result['play_url'] = play.play_url
        # result['play_thumbnail_url'] = play.play_thumbnail_url
        result['play_name'] = play.play_name
        result['play_description'] = play.play_description
        result['play_tag'] = play.play_tag
        result['vote_number'] = play.vote_number
        result['visit_number'] = play.visit_number
        result['date'] = play.date
        result['comment_number'] = play.comment_number
        result['play_thumbnail_url'] = play.play_thumbnail_url
        result['creator_name'] = creator.name
        result['creator_avatar'] = creator.avatar[0].image_url
        return result

    def upload_play(self, file, path):
        print('upload_play, file', file)
        if file:
            response, s3_dir = upload_file(file, path)
        result = {'msg': response, 's3_dir': s3_dir}
        return result

    def post_play(self, file, user_id, play_name, play_description, play_visibility, play_tag):
        # user_id as file folder
        date = datetime.now()
        creator = UserTable.query.filter_by(id=user_id).first()
        result = self.upload_play(file, str(user_id))
        # print('file type is', type(file))
        # thumbnail = capture_thumnail(file)
        # thumbnail_name, ext = os.path.splitext(file.filename)
        # thumbnail_result = self.upload_play(
        #     io.BytesIO(thumbnail), os.path.join(
        #         'thumbnail', str(user_id), thumbnail_name+'.png'))
        # print('thumbnail_result', thumbnail_result)
        play_url = result['s3_dir']
        # play_thumbnail_url = thumbnail_result['s3_dir']
        play_thumbnail_url = "https://d97ch61yqe5j6.cloudfront.net/thumbnail/thumbnail.png"
        play_item = PlayTable(
            play_url=play_url, play_name=play_name,
            play_description=play_description, play_visibility=play_visibility, play_tag=play_tag, date=date, user_id=user_id, play_thumbnail_url=play_thumbnail_url)
        msg = save_check(play_item)
        (code, message) = (1, msg) if msg else (0, '')
        result = {'code': code, 'msg': message,
                  'play_visibility': play_visibility}
        if not code:  # 上传成功
            play_object = PlayTable.query.filter_by(
                play_url=play_url).first()
            result['play_name'] = play_name
            result['play_id'] = play_object.id
            result['creator'] = creator.name
            result['share_id'] = play_object.share_id
            result['twilio_number'] = creator.twilio_number
        return result

    def play_vote(self, share_id, user_id):
        play = PlayTable.query.filter_by(share_id=share_id).first()
        date = datetime.now()
        if play:
            play.vote_number += 1
            msg = update_check()
            (code, message) = (1, msg) if msg else (0, '')
            play_vote_item = PlayVote(
                play_id=play.id, user_id=user_id, date=date)
            msg2 = save_check(play_vote_item)
            (code2, message2) = (1, msg2) if msg2 else (0, '')
            result = {'code': code+code2, 'msg': message + message2}
        else:
            result = {'code': 1, 'msg': "The play doesn't exist"}
        return result
