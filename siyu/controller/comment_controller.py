import os
import time
from siyu import app
from siyu import db
from siyu.models import UserTable, PlayTable, CommentTable, ThreadTable, PlayReward, PlayVote, CommentVote, ThreadVote, AvatarTable
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from siyu.controller.sql import save_check, update_check
from siyu.s3_api import list_files, download_file, upload_file
from flask import jsonify
from collections import defaultdict
from siyu.awsconfig import CLOUDFRONT
# from siyu.utils import capture_thumnail


class CommentController():
    def get_comments(self, play_id, page, offset):

        comment_feed = CommentTable.query.filter_by(
            play_id=play_id).order_by(CommentTable.vote_number.desc()).paginate(page=page, per_page=offset)
        result = defaultdict(list)
        if comment_feed:
            print('length', len(comment_feed.items))
            for comment in comment_feed.items:
                user = UserTable.query.filter_by(id=comment.user_id).first()
                result['response'].append({'id': comment.id, 'content': comment.content, 'date': comment.date, 'vote_number': comment.vote_number,
                                           'reply_number': comment.reply_number, 'play_id': comment.play_id, 'user_id': comment.user_id, 'user_name': user.name,
                                           'user_avatar': user.avatar[0].image_url})
        else:
            result['response'] = []
        return result

    def post_comment(self, user_id, play_id, content):
        date = datetime.now()
        comment_item = CommentTable(
            content=content, date=date, play_id=play_id, user_id=user_id)
        msg = save_check(comment_item)
        (code, message) = (1, msg) if msg else (0, '')
        if not code:
            play = PlayTable.query.filter_by(id=play_id).first()
            play.comment_number += 1
            msg_play = update_check()
        (code, message) = (code+1, message +
                           msg_play) if msg_play else (code, message)
        result = {'code': code, 'msg': message}
        return result
