import stripe
from siyu.stripeconfig import API_KEY
import os
import time
from siyu import app
from siyu import db
from siyu.models import UserTable, PlayTable, CommentTable, ThreadTable, PlayReward, PlayVote, CommentVote, ThreadVote, AvatarTable
from siyu.controller.sql import save_check, update_check
from siyu.s3_api import list_files, download_file, upload_file
from flask import jsonify

stripe.api_key = API_KEY


class StripeController():
    def create_product(self, name, tier_id, creator_id, price):
        # payload = json.loads(request.data or '{}')
        try:
            productObj = stripe.Product.create(
                name=name,
                id=tier_id,
                metadata={
                    'on_behalf_of_id': creator_id
                }
            )
            price = stripe.Price.create(
                unit_amount=price,
                currency="usd",
                recurring={
                    # "interval": "day" #for testing only
                    "interval": "month",
                },
                product=productObj.id,
            )
            return {'code': 0, 'message': {
                'product_id': productObj.id,
                'price_id': price.id}}

        except Exception as e:
            return {'code': 1, 'message': str(e)}

    def create_customer(self, phone_number):
        print('im here')
        # payload = request.json
        try:
            customer = stripe.Customer.create(
                name=phone_number,
                phone=phone_number,
                description='House user with number of '+phone_number
            )
            print('im here 1')
            stripe_result = {'code': 0, 'message': {
                'customer_id': customer.id}}
            return stripe_result

        except Exception as e:
            stripe_result = {'code': 1, 'message': str(e)}
            return stripe_result
