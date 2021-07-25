from siyu.send_sms import send_message
from siyu.models import UserTable


class StreamChatController():

    def stream_to_sms(self, from_user, to_user, content):
        from_user_info = UserTable.query.filter_by(id=from_user).first()
        to_user_info = UserTable.query.filter_by(id=to_user).first()
        print(from_user_info)
        print(to_user_info)
        if from_user_info is None or to_user_info is None:
            return {'code': 1, 'msg': ERROR.USER_NOT_EXISTS}


        print('{} send to {} content:{}'.format(
            from_user_info.twilio_number , to_user_info.phone_number, content)
        )
        cid = send_message(
            content=content,
            target_number=to_user_info.phone_number ,
            from_number=from_user_info.twilio_number 
        )
        return {'code': 0, 'msg': 'success', 'data': cid}
