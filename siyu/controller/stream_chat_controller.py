from siyu.send_sms import send_message
from siyu.models import UserTable
from siyu.provider.stream_chat_client import StreamChatClient
from siyu.constants import ERROR


class StreamChatController():
    '''
    im business logic class
    '''

    def stream_to_sms(self, from_user, to_user, content):
        '''
        getStream message send to twilio sms 
        :param from_user: sender user id
        :param to_user: resive user id
        :param content: message text content
        '''
        from_user_info = UserTable.query.filter_by(id=from_user).first()
        to_user_info = UserTable.query.filter_by(id=to_user).first()
        print(from_user_info)
        print(to_user_info)
        if from_user_info is None or to_user_info is None:
            return {'code': 1, 'msg': ERROR.USER_NOT_EXISTS}

        print('stream to sms {} send to {} content:{}'.format(
            from_user_info.twilio_number, to_user_info.phone_number, content)
        )
        cid = send_message(
            content=content,
            target_number=to_user_info.phone_number,
            from_number=from_user_info.twilio_number
        )
        return {'code': 0, 'msg': 'success', 'data': cid}

    def sms_to_stream(self, from_user_number, to_user_number, content):
        '''
        twilio sms send to getStream message 
        :param from_user_number: sender user phone number
        :param to_user_number: resive user twilio number
        :param content: message text content
        '''
        from_user_info = UserTable.query.filter_by(
            phone_number=from_user_number).first()
        to_user_info = UserTable.query.filter_by(
            twilio_number=to_user_number).first()
        print(from_user_info)
        print(to_user_info)
        if from_user_info is None or to_user_info is None:
            return {'code': 1, 'msg': ERROR.USER_NOT_EXISTS}

        print('sms to stream {} send to {} content:{}'.format(
            from_user_info.twilio_number, to_user_info.phone_number, content)
        )
        stream_client = StreamChatClient()
        stream_client.send_message(
            from_user_info.id, to_user_info.id, message={"Text": content}
        )
        return {'code': 0, 'msg': 'success', 'data': ''}
