from flask import Flask, request, jsonify
import requests

from flask_cors import CORS

import stripe
# from twilio.twiml.messaging_response import MessagingResponse
# from stream_chat import StreamChat

app = Flask(__name__)
CORS(app)

stripe.api_key = "sk_test_51I9JshLXpKNZDmCJ3c2PZclzs9NoQENputwbxbWdcSBE2aaOrnGWgayaKI2Y2WgGfUAt0jKHUhYUJok8oDjO6s6q00dHx3fUfd"


@app.route('/create_product', methods=['POST'])
def create_product():
    # payload = json.loads(request.data or '{}')
    payload = request.json
    try:
        productObj = stripe.Product.create(
            name=payload['name'],
            id=payload['tier_id'],
            metadata={
                'on_behalf_of_id':payload['creator_id']
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
                'response':{
                    'product_id':productObj.id,
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
                'response':{
                    'customer_id': customer.id
                }
            }
        )
    except Exception as e:
        return jsonify(error={'message': str(e)}), 400

@app.route('/create_subscription', methods=['POST'])
def create_subscription():
    payload = request.json
    # data = request.json
    # data = json.loads(request.data)
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
        return jsonify(subscription)
    except Exception as e:
        return jsonify(error={'message': str(e)}), 400 #actual production use 200 to unify with Stripe way of doing things?
        # return jsonify(error={'message': str(e)}), 200


if __name__ == '__main__':

    app.run()