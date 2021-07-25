from stream_chat import StreamChat
from siyu.config.get_stream import GET_STREAM_API_KEY, GET_STREAM_API_SECRET


class StreamChatClient:
    '''
    getStream.io 客户端
    '''

    def __init__(self, api_key=GET_STREAM_API_KEY, api_secret=GET_STREAM_API_SECRET):
        self.server_client = StreamChat(api_key=api_key, api_secret=api_secret)

    def create_token(self, user_id):
        '''
        创建 getStream token
        '''
        return self.server_client.create_token(user_id)

    def send_message(self, from_user, to_user, message):
        '''
        发送消息
        '''
        cannel_id = ['{}'.format(from_user), '{}'.format(to_user)]
        cannel_id.sort()
        channel = self.server_client.channel(
            "messaging", '-'.join(cannel_id)
        )
        # 频道由系统创建
        channel.create("admin")
        channel.send_message(message, '{}'.format(from_user))
