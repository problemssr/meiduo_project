
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from apps.oauth.constants import OPENID_TOKEN_EXPIRE_TIME
from meiduo_mall import settings
def generate_access_token(openid):

    #1. 创建实例对象
    s = Serializer(secret_key=settings.SECRET_KEY,expires_in=OPENID_TOKEN_EXPIRE_TIME)
    #2.组织数据
    data = {
        'openid':openid
    }
    #3.加密处理
    token = s.dumps(data)
    #4. 返回
    return token.decode()


def check_access_token(token):

    #1.创建实例对象
    s = Serializer(secret_key=settings.SECRET_KEY, expires_in=OPENID_TOKEN_EXPIRE_TIME)
    #2. 解密数据
    result = s.loads(token)
    # script = {'openid':'xxxx'}
    #3.返回数据
    return result['openid']
