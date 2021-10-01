from stream_chat import StreamChat
from siyu.config.get_stream import GET_STREAM_API_KEY, GET_STREAM_API_SECRET


class StreamChatClient:
    '''
    getStream.io client
    '''

    def __init__(self, api_key=GET_STREAM_API_KEY, api_secret=GET_STREAM_API_SECRET):
        self.server_client = StreamChat(api_key=api_key, api_secret=api_secret)

    def create_token(self, user_id):
        '''
        create getStream conversation token
        :param from_user: create user id
        '''
        return self.server_client.create_token(user_id)

    def send_message(self, from_user, to_user, message):
        '''
        getStream send message
        :param from_user: sender user id
        :param to_user: resive user id
        :param message: message body, example:{'Text':'test msg'}
        '''
        cannel_id = ['{}'.format(from_user), '{}'.format(to_user)]
        cannel_id.sort()
        channel = self.server_client.channel(
            "messaging", '-'.join(cannel_id)
        )
        # channel create by system
        channel.create("admin")
        channel.send_message(message, '{}'.format(from_user))
