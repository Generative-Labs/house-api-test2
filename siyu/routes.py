from siyu.send_sms import send_message, available_phone
from siyu.controller.sql import save_check, update_check
from siyu.utils import generate_confirmation_token, confirm_token
from functools import wraps
import jwt
import json
from siyu.constants import ERROR
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import re
from siyu.controller.comment_controller import CommentController
from siyu.controller.subscribe_controller import SubscribeController
from siyu.controller.play_controller import PlayController
from siyu.controller.user_profile_controller import UserProfileController
from siyu.s3_api import list_files, download_file, upload_file
from siyu.models import UserTable, PlayTable, CommentTable, ThreadTable, PlayReward, PlayVote, CommentVote, ThreadVote, AvatarTable, Subscribers, TierTable
from siyu import db
from siyu import app
import random
import os
from collections import defaultdict
from datetime import datetime, timedelta
from flask import request, g, jsonify, render_template, url_for
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, jwt_refresh_token_required, create_refresh_token, get_jwt_identity, fresh_jwt_required
import stripe
from siyu.stripeconfig import API_KEY
from siyu.controller.stripe_controller import StripeController

jwt = JWTManager(app)
stripe.api_key = API_KEY

#User####

# login_manager = LoginManager()
# login_manager.init_app(app)


# def token_required(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         token = None
#         if 'x-access-token' in request.headers:
#             token = request.headers['x-access-token']
#         if not token:
#             return jsonify({'code': '1', 'msg': 'Token is missing!'}), 401
#         try:
#             data = jwt.decode(token, app.secret_key)
#             print('data', data)
#             current_user = UserTable.query.filter_by(
#                 username=data['username']).first()
#         except:
#             return jsonify({'code': '1', 'message': 'Token is invalid!'}), 401
#         return f(current_user, *args, **kwargs)
#     return decorated

# @login_manager.user_loader
# def load_user(user_id):
#     return UserTable.query.get(int(user_id))


# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == "POST":
#         payload = request.get_json(silent=True)
#         username = payload.get('username', '')
#         password = payload.get('password', '')
#         user = UserProfileController()
#         result = user.check_auth(username, password)
#         if not result['code']:
#             token = jwt.encode({'username': result['user'].username, 'exp': datetime.utcnow(
#             ) + timedelta(minutes=300)}, app.secret_key)
#             result = {'code': 0, 'msg': {'token': token.decode(
#                 'UTF-8'), 'user_id': result['user'].id, 'username': result['user'].username,
#                 'name': result['user'].name, 'bio': result['user'].bio, 'number_follower': result['user'].number_follower,
#                 'number_following': result['user'].number_following, 'avatar': result['user'].avatar[0].image_url}}
#             return jsonify(result), 200
#             # login_user(result['user'], remember=True)
#             # g.user = result['user']
#         # print(g.user.id, 'g')
#         return jsonify(result), 401

### Comments  ####
@app.route('/login', methods=['POST'])
def login():
    # if request.method == "POST":
    payload = request.get_json(silent=True)
    phone_number = payload.get('phone_number', '')
    password = payload.get('password', '')
    user = UserProfileController()
    result = user.check_auth(phone_number, password)
    if not result['code']:
        result = {
            'code': 0, 
            'msg': {
                'access_token': create_access_token(identity=result['user'].id, fresh=True), 
                'refresh_token': create_refresh_token(identity=result['user'].id), 
                'user_id': result['user'].id, 
                'username': result['user'].username,
                'name': result['user'].name, 
                'bio': result['user'].bio, 
                'customer_id': result['user'].customer_id, 
                'number_follower': result['user'].number_follower,
                'number_following': result['user'].number_following, 
                'creator_house_phone_number': result['user'].twilio_number,
                'avatar': result['user'].avatar[0].image_url
            }
        }
        return jsonify(result), 200
        # login_user(result['user'], remember=True)
        # g.user = result['user']
    # print(g.user.id, 'g')
    return jsonify(result), 401
# Refresh token endpoint. This will generate a new access token from
# the refresh token, but will mark that access token as non-fresh,
# as we do not actually verify a password in this endpoint.


@app.route('/refresh', methods=['POST'])
@jwt_refresh_token_required
def refresh():
    current_user = get_jwt_identity()
    # print('current_user', type(current_user))
    ret = {
        'access_token': create_access_token(identity=current_user, fresh=False)
    }
    return jsonify(ret), 200

# Fresh login endpoint. This is designed to be used if we need to
# make a fresh token for a user (by verifying they have the
# correct username and password). Unlike the standard login endpoint,
# this will only return a new access token, so that we don't keep
# generating new refresh tokens, which entirely defeats their point.


@app.route('/fresh-login', methods=['POST'])
def fresh_login():
    payload = request.get_json(silent=True)
    username = payload.get('username', '')
    password = payload.get('password', '')
    user = UserProfileController()
    result = user.check_auth(username, password)
    if not result['code']:
        result = {'code': 0, 'msg': {'access_token': create_access_token(identity=result['user'].id, fresh=True), 'refresh_token': create_refresh_token(identity=result['user'].id), 'user_id': result['user'].id, 'username': result['user'].username,
                                     'name': result['user'].name, 'bio': result['user'].bio, 'customer_id': result['user'].customer_id, 'number_follower': result['user'].number_follower,
                                     'number_following': result['user'].number_following, 'avatar': result['user'].avatar[0].image_url}}
        return jsonify(result), 200
        # login_user(result['user'], remember=True)
        # g.user = result['user']
    # print(g.user.id, 'g')
    return jsonify(result), 401

# An endpoint that requires a valid access token (non-expired, either fresh or non-fresh)


@app.route('/protected', methods=['GET'])
@jwt_required
def protected():
    user_id = get_jwt_identity()
    return jsonify(logged_in_as=user_id), 200


# Only fresh JWTs can access this endpoint
@app.route('/protected-fresh', methods=['GET'])
@fresh_jwt_required
def protected_fresh():
    user_id = get_jwt_identity()
    return jsonify(fresh_logged_in_as=user_id), 200


@app.route("/get_comments", methods=['GET', 'POST'])
def get_comments():
    payload = request.get_json(silent=True)
    play_id = payload['play_id']
    page = payload.get('page', 1)
    offset = payload.get('offset', 15)
    comment_controller = CommentController()
    result = comment_controller.get_comments(play_id, page, offset)
    # play_controller = ()
    # result['play'] = play_controller.get_play(visit_account_id,
    #                                           login_user_id, page, offset)['response']
    return jsonify(result)


@app.route("/post_comment", methods=['POST'])
@jwt_required
def post_comment():
    payload = request.get_json(silent=True)
    user_id = get_jwt_identity()
    play_id = payload['play_id']
    content = payload['comment_body']
    controller = CommentController()
    result = controller.post_comment(user_id, play_id, content)
    if not result['code']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


## subscribe ##
@app.route('/subscribe_to_tier', methods=['POST', 'GET'])
@jwt_required
def subscribe_to_tier():
    payload = request.get_json(silent=True)
    creator_id = payload['creator_id']
    tier_id = payload['tier_id']
    user_id = get_jwt_identity()
    controller = SubscribeController()
    result = controller.subscribe(creator_id, tier_id, user_id)
    if not result['code']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@app.route('/subscribe_free_tier', methods=['POST', 'GET'])
def subscribe_free_tier():
    payload = request.get_json(silent=True)
    phone_number = payload['phone_number']
    creator_id = payload['creator_id']
    user = UserTable.query.filter_by(phone_number=phone_number).first()
    controller = UserProfileController()
    if not user:  # 用户首次使用，数据库中不存在
        name = username = 'house' + \
            str(datetime.now()).split('.')[-1] + \
            str(phone_number)[-4:]  # placeholder
        password = phone_number
        email = '{}@gmail.com'.format(str(datetime.now()).split('.')
                                      [-1]+str(phone_number)[-4:])  # placeholder
        bio = ''
        result = controller.create_profile(0, username, name, password,
                                           phone_number, email, bio)
    else:
        result = {'code': 0, 'msg': ''}
    tier_id = controller.get_free_tier(creator_id)['response'][0]['tier_id']
    if not result['code']:
        token = generate_confirmation_token(phone_number)
        confirm_url = "https://channels.housechan.com/confirm/{}/{}/{}".format(
            token, creator_id, tier_id)
        print('what is confirm_url', confirm_url)
        # use twilio to send out to the phone
        content = 'Please click the link below to confirm your subscription:' + confirm_url
        sid = send_message(content, phone_number)
        # return sid
        result['sid'] = sid
        result['confirm_url'] = confirm_url
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@app.route('/confirm_subscribe', methods=['POST'])
def confirm_subscribe():
    payload = request.get_json(silent=True)
    token = payload['token']
    creator_id = payload['creator_id']
    tier_id = payload['tier_id']
    # token, creator_id, tier_id
    phone_number = confirm_token(token)
    print('confirm_toekn', phone_number)
    if not phone_number:
        return jsonify({'code': 1, 'msg': 'The confirmation link is invalid or has expired.'}), 400
    user = UserTable.query.filter_by(phone_number=phone_number).first_or_404()
    controller = SubscribeController()
    result = controller.subscribe(creator_id, tier_id, user.id)
    if not result['code']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400
    # if request.method == "POST" and not result['code']:
    #     return redirect(url_for('get_profile', json=json.dumps({'visit_account_id': creator_id})), code=307)


@app.route('/unsubscribe', methods=['POST', 'GET'])
@jwt_required
def unsubscribe():
    payload = request.get_json(silent=True)
    creator_id = payload['creator_id']
    tier_id = payload['tier_id']
    user_id = get_jwt_identity()
    controller = SubscribeController()
    result = controller.unsubscribe(creator_id, user_id, tier_id)
    if not result['code']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@app.route('/relationship', methods=['GET', 'POST'])
@jwt_required
def relationship():
    payload = request.get_json(silent=True)
    creator_id = payload['creator_id']
    user_id = get_jwt_identity()
    controller = SubscribeController()
    result = controller.is_subscribing(creator_id, user_id)
    return jsonify(result)


@app.route('/register', methods=['POST'])
def register():
    payload = request.get_json(silent=True)
    creator = payload['creator']  # Boolean
    phone_number = payload['phone_number']
    password = payload["password"]
    username = payload.get('username', '')
    if UserTable.query.filter_by(phone_number=phone_number).one_or_none():
        data = {'code': 1, 'msg': ERROR.USER_EXISTS}
        return jsonify(data), 409
    name = 'house' + \
        str(datetime.now()).split('.')[-1] + \
        str(phone_number)[-4:]  # placeholder
    if not username:
        username = name
    email = '{}@gmail.com'.format(str(datetime.now()).split('.')
                                  [-1]+str(phone_number)[-4:])  # placeholder
    bio = ''
    stripe_controller = StripeController()
    stripe_result = stripe_controller.create_customer(phone_number)
    if not stripe_result['code']:
        customer_id = stripe_result['message']['customer_id']
        controller = UserProfileController()
        result = controller.create_profile(creator, username, name, password,
                                           phone_number, email, bio, customer_id)
        if not result['code']:
            token = generate_confirmation_token(phone_number)
            confirm_url = "https://channels.housechan.com/register/{}".format(
                token)
            print('what is confirm_url', confirm_url)
            # use twilio to send out to the phone
            content = 'Please click the link below to confirm your phone number:' + confirm_url
            sid = send_message(content, phone_number)
            # return sid
            result['sid'] = sid
            result['confirm_url'] = confirm_url
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    else:
        return jsonify({'code': 0, 'msg': 'Stripe customer creation fail'}), 400


@app.route('/confirm_phone', methods=['POST'])
def confirm_phone():
    payload = request.get_json(silent=True)
    token = payload['token']
    phone_number = confirm_token(token)
    if not phone_number:
        return jsonify({'code': 1, 'msg': 'The confirmation link is invalid or has expired.'}), 400
    user = UserTable.query.filter_by(phone_number=phone_number).first_or_404()
    if not user.confirmed:
        user.confirmed = True
        msg = update_check()
        (code, message) = (1, msg) if msg else (
            0, '')  # msg for saving in user table
        result = {'code': code, 'msg': message}
    else:
        result = {'code': 0, 'msg': 'User has confirmed the number'}
    if not result['code']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@app.route('/handle_exist', methods=['POST'])
def handle_exist():
    payload = request.get_json(silent=True)
    username = payload['username']
    if UserTable.query.filter_by(username=username).one_or_none():
        data = {'code': 1, 'msg': ERROR.USER_EXISTS}
        return jsonify(data), 409
    else:
        data = {'code': 0, 'msg': ''}
        return jsonify(data), 200


@app.route('/update_profile', methods=['POST'])
@jwt_required
def update_profile():
    payload = request.get_json(silent=True)
    username = payload['username']
    name = payload.get('name', '')
    phone_number = payload['phone_number']
    email = payload.get('email', '')
    bio = payload.get('bio', '')
    if not username:
        data = {'code': 1, 'msg': ERROR.ARGS}
        return jsonify(data), 412
    # if UserTable.query.filter_by(username=username).one_or_none():
    #     data = {'code': 1, 'msg': ERROR.USER_EXISTS}
    #     return jsonify(data), 409
    # check email validation:
    controller = UserProfileController()
    result = controller.update_profile(
        phone_number, username, name, email, bio)
    if not result['code']:
        result['username'] = username
        result['name'] = name
        result['bio'] = bio
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@app.route('/upload_avatar', methods=['POST'])
@jwt_required
def upload_avatar():
    if request.method == 'POST':
        f = request.files['file']
        # payload = request.get_json(silent=True)
        user_id = get_jwt_identity()
        controller = UserProfileController()
        result = controller.upload_avatar(user_id, f, '')
    if not result['code']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@app.route('/upload_bio', methods=['POST'])
@jwt_required
def uplaod_bio():
    try:
        payload = request.get_json(silent=True)
        bio = payload['bio']
    except:
        bio = ''
    user_id = get_jwt_identity()
    controller = UserProfileController()
    result = controller.upload_bio(user_id, bio)
    if not result['code']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@app.route('/get_profile', methods=['GET', 'POST'])
def get_profile():
    payload = request.get_json()
    visit_username = payload['visit_username']  # username to be viewed
    login_user_id = payload.get('login_user_id', '')
    page = payload.get('page', 1)
    offset = payload.get('offset', 15)
    user_controller = UserProfileController()
    result = user_controller.get_user_profile(visit_username)
    if not result['code']:
        play_controller = PlayController()
        result['play'] = play_controller.get_play(
            result['id'], login_user_id, page, offset)['response']
        return jsonify(result), 200

    else:
        return jsonify(result), 400


# @ app.route('/get_profile_visitor', methods=['GET', 'POST'])
# def get_profile_visitor():
#     payload = request.get_json()
#     visit_account_id = payload['visit_account_id']  # user_id to be viewed
#     page = payload.get('page', 1)
#     offset = payload.get('offset', 15)
#     user_controller = UserProfileController()
#     result = user_controller.get_user_profle(visit_account_id)
#     play_controller = PlayController()
#     result['play'] = play_controller.get_play(visit_account_id,
#                                               '', page=page, offset=offset)['response']
#     return jsonify(result)


@ app.route('/post_play', methods=['POST'])
@ jwt_required
def post_play():
    if request.method == 'POST':
        f = request.files['file']  # file upload to s3 and get url
        data = request.form.get('data')
        payload = json.loads(data)
        play_name = payload.get('play_name', '')
        play_description = payload.get('play_description', '')
        play_visibility = payload.get('play_visibility', [])
        play_tag = payload.get('play_tag', '')
        user_id = get_jwt_identity()
        # user_id = current_user.id
        controller = PlayController()
        result = controller.post_play(
            f, user_id, play_name, play_description, play_visibility, play_tag)
        if not result['code']:
            subscribe_controller = SubscribeController()
            result['twilio_sms'] = subscribe_controller.get_subscriber(
                play_visibility, result['play_name'], result['play_id'], result['creator'], result['twilio_number'])
            return jsonify(result), 200
        else:
            return jsonify(result), 400


@ app.route('/get_play', methods=['GET', 'POST'])
def get_play():
    payload = request.get_json()
    play_id = payload['play_id']
    controller = PlayController()
    result = controller.get_single_play(play_id)
    return jsonify(result)


@ app.route("/storage")
def storage():
    contents = list_files()
    # print(contents)
    return render_template('storage.html')


@ app.route("/")
def say_hello(username="World"):
    return '<p>Hello %s!</p>\n' % username


@ app.route("/logout", methods=["GET"])
@ login_required
def logout():
    """Logout the current user."""
    user = current_user
    logout_user()
    result = {'response': 'You have logged out!'}
    return jsonify(result)


@ app.route("/get_my_id", methods=['GET'])
@ login_required
def get_my_id():
    result = {'id': current_user.id}
    return jsonify(result)


@ app.route("/create_tier", methods=['POST', 'GET'])
@ jwt_required
def create_tier():
    payload = request.get_json(silent=True)
    tier_name = payload['tier_name']
    tier_price = payload['tier_price']
    tier_perks = payload['tier_perks']
    creator_id = get_jwt_identity()
    controller = UserProfileController()
    result = controller.create_tier(
        creator_id, tier_name, tier_price, tier_perks)
    if not result['code']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@ app.route("/get_tiers", methods=['GET', 'POST'])
def get_tiers():
    payload = request.get_json(silent=True)
    creator_id = payload['creator_id']
    controller = UserProfileController()
    result = controller.get_tiers(creator_id)
    return jsonify(result)


@ app.route("/distribute_to_subscriber", methods=['GET', 'POST'])
@ jwt_required
def distribute_to_subscriber():
    payload = request.get_json(silent=True)
    play_visibility = payload['play_visibility']
    play_name = payload['play_name']
    play_url = payload['play_url']
    creator_id = get_jwt_identity()
    # print(list(play_visibility))
    controller = SubscribeController()
    result = controller.get_subscriber(
        play_visibility, play_url, play_name, creator_id)
    return jsonify(result)


@ app.route("/get_creator_subscriber", methods=['GET', 'POST'])
@ jwt_required
def get_creator_subscriber():
    payload = request.get_json(silent=True)
    creator_id = get_jwt_identity()
    offset = payload.get('offset', 15)
    page = payload.get('page', 1)
    # tier_controller = UserProfileController()
    # tiers = tier_controller.get_tiers(creator_id)
    # play_visibility = []
    # for tier in tiers['response']:
    #     play_visibility.append(tier['tier_id'])
    if creator_id:
        controller = SubscribeController()
        result = controller.get_all_subscriber(creator_id)
        return jsonify(result), 200
    else:
        result = {'response': []}
        return jsonify(result), 404

    # @app.route('/get_profile', methods=['GET', 'POST'])
# @token_required
# def get_profile(current_user):


@ app.route("/phone_exist", methods=['GET', 'POST'])
def phone_exist():
    payload = request.get_json(silent=True)
    phone_number = payload.get('phone_number', '')
    if not phone_number:
        return jsonify({'code': 1, 'msg': 'Phone number cannot be empty'}), 400
    else:
        user = UserTable.query.filter_by(phone_number=phone_number).first()
        if not user:
            return jsonify({'response': {'phone_exist': False}}), 200
        else:
            return jsonify({'response': {'phone_exist': True, 'customer_id': user.customer_id}}), 200


@ app.route('/list_phone_number', methods=['GET'])
@ jwt_required
def list_phone_number():
    result = available_phone()
    return jsonify(result)


@app.route("/choose_phone_number", methods=['POST'])
@ jwt_required
def choose_phone_number():
    payload = request.get_json()
    twilio_number = payload['choose_number']  # 用户选择的电话号码
    user_id = get_jwt_identity()
    user_controller = UserProfileController()
    result = user_controller.choose_number(user_id, twilio_number)

    return jsonify(result)


@app.route("/send_reset_link", methods=['POST'])
def send_reset_link():
    payload = request.get_json(silent=True)
    phone_number = payload['phone_number']
    user = UserTable.query.filter_by(phone_number=phone_number).first_or_404()
    if user:
        token = generate_confirmation_token(phone_number)
        confirm_url = "https://channels.housechan.com/reset/{}".format(
            token)
        print('what is confirm_url', confirm_url)
        # use twilio to send out to the phone
        content = 'Please click the link below to reset your password:' + confirm_url
        sid = send_message(content, phone_number)
        # return sid
        result = {}
        result['sid'] = sid
        result['confirm_url'] = confirm_url
        return jsonify(result), 200
    else:
        return jsonify({'code': 1, 'msg': ERROR.USER_NOT_EXISTS})


@app.route("/get_reset_password", methods=['POST'])
def get_reset_password():
    payload = request.get_json(silent=True)
    token = payload['token']
    reset_password = payload['reset_password']
    # token, creator_id, tier_id
    try:
        phone_number = confirm_token(token)
    except:
        return jsonify({'code': 1, 'msg': 'The confirmation link is invalid or has expired.'}), 400
    user = UserTable.query.filter_by(phone_number=phone_number).first_or_404()
    if user:
        user_controller = UserProfileController()
        result = user_controller.reset_password(user.id, reset_password)
    return jsonify(result), 200


@app.route("/change_to_creator", methods=['POST'])
@ jwt_required
def change_to_creator():
    user_id = get_jwt_identity()
    user_controller = UserProfileController()
    result = user_controller.change_to_creator(user_id)
    if not result['code']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@app.route("/play_vote", methods=['POST'])
@ jwt_required
def play_vote():
    payload = request.get_json(silent=True)
    play_id = payload['play_id']
    user_id = get_jwt_identity()
    play_controller = PlayController()
    result = play_controller.play_vote(play_id, user_id)
    if not result['code']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@app.route('/create_product', methods=['POST'])
def create_product():
    # payload = json.loads(request.data or '{}')
    payload = request.json
    try:
        productObj = stripe.Product.create(
            name=payload['name'],
            id=payload['tier_id'],
            metadata={
                'on_behalf_of_id': payload['creator_id']
            }
        )
        price = stripe.Price.create(
            unit_amount=payload['price'],
            currency="usd",
            recurring={
                # "interval": "day" #for testing only
                "interval": "month",
            },
            product=productObj.id,
        )
        return jsonify(
            {
                'response': {
                    'product_id': productObj.id,
                    'price_id': price.id
                }
            }
        )

    except Exception as e:
        return jsonify(error={'message': str(e)}), 400


@app.route('/create_customer', methods=['POST'])
def create_customer():
    payload = request.json
    try:
        customer = stripe.Customer.create(
            name=payload['phone_number'],
            phone=payload['phone_number'],
            description='House user with number of '+payload['phone_number']
        )
        return jsonify(
            {
                'response': {
                    'customer_id': customer.id
                }
            }
        )
    except Exception as e:
        return jsonify(error={'message': str(e)}), 400


@app.route('/create_subscription', methods=['POST'])
def create_subscription():
    payload = request.json
    creator_id = payload['creator_id']
    tier_id = payload['tier_id']
    phone_number = payload['phone_number']
    user = UserTable.query.filter_by(phone_number=phone_number).first()
    if not user:
        return jsonify(error={'message': "phone number doesn't exists, register now"}), 400
    else:
        stripe_controller = StripeController()
        exists = stripe_controller.check_stripe_subscription_exists(
            payload['customerId'], payload['priceId'])
        if exists:
            return jsonify(error={'message': 'stripe subscription exists'}), 400
        else:
            try:
                # Attach the payment method to the customer
                stripe.PaymentMethod.attach(
                    payload['paymentMethodId'],
                    customer=payload['customerId'],
                )
                # Set the default payment method on the customer
                stripe.Customer.modify(
                    payload['customerId'],
                    invoice_settings={
                        'default_payment_method': payload['paymentMethodId'],
                    },
                )

                # Create the subscription
                subscription = stripe.Subscription.create(
                    customer=payload['customerId'],
                    items=[
                        {
                            'price': payload['priceId']
                        }
                    ],
                    # expand=['latest_invoice.payment_intent'],
                )
                # call stripe controller 的函数
                controller = SubscribeController()
                result = controller.subscribe(creator_id, tier_id, user.id)
                subscription['subscribe_to_tier'] = result
                if not result['code']:
                    return jsonify(subscription), 200
                else:
                    return jsonify(subscription), 400
            except Exception as e:
                # actual production use 200 to unify with Stripe way of doing things?
                return jsonify(error={'message': str(e)}), 400
