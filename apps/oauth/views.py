from django import http
from django.contrib.auth import login
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.views import View
from QQLoginTool.QQtool import OAuthQQ

from apps.oauth.models import OAuthQQUser
from apps.oauth.utils import generate_access_token, check_access_token
from apps.users.models import User
from meiduo_mall import settings

"""

1.拼接用户跳转的url,当用户同意登陆之后,会生成code
2. 通过code换取token
3. 通过token换取openid
4. 绑定用户

"""

"""
1. 实现QQ 按钮的跳转
   ① 直接把拼接号的url放在a标签上 https://graph.qq.com/oauth2.0/authorize?response_type=code&client_id=101518219&redirect_uri=http://www.meiduo.site:8000/oauth_callback&state=test
    ② 我们可以通过 让前端发送一个ajax请求
"""


class OauthQQURLView(View):

    def get(self, request):
        # 1.创建实例对象
        state = 'test'
        qqoauth = OAuthQQ(
            client_secret=settings.QQ_CLIENT_SECRET,
            client_id=settings.QQ_CLIENT_ID,
            redirect_uri=settings.QQ_REDIRECT_URI,
            state=state
        )

        # 2.调用方法
        login_url = qqoauth.get_qq_url()

        return http.JsonResponse({'login_url': login_url})


"""

一 把需求写下来 (前端需要收集什么 后端需要做什么)
    前端需要把用户同意的code(code是认证服务器返回的) 提交给后端

    后端通过code换取token

二 把大体思路写下来(后端的大体思路)
    1.获取code
    2. 通过读取文档将code转换为token

三 把详细思路完善一下(纯后端)

四 确定我们请求方式和路由

    GET oauth_callback
"""


class OauthQQUserView(View):

    def get(self, request):

        # 1.获取code
        code = request.GET.get('code')
        if code is None:
            return render(request, 'oauth_callback.html', context={'errmsg': '没有获取到指定参数'})
        # 2. 通过读取文档将code转换为token
        qqoauth = OAuthQQ(
            client_secret=settings.QQ_CLIENT_SECRET,
            client_id=settings.QQ_CLIENT_ID,
            redirect_uri=settings.QQ_REDIRECT_URI
        )

        token = qqoauth.get_access_token(code)

        # 3.通过token换取openid
        openid = qqoauth.get_open_id(token)

        # 4. 我们需要根据 openid 进行数据的查询
        try:
            qquser = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 如果没有同样的openid,则说明用户没有绑定过

            # 对openid进行一个加密的处理

            openid_access_token = generate_access_token(openid)

            return render(request, 'oauth_callback.html', context={'openid_access_token': openid_access_token})
        else:
            # 如果有同样的openid,则说明用户绑定过
            # 则直接登陆

            response = redirect(reverse('contents:index'))

            # 1. 设置登陆状态
            login(request, qquser.user)

            # 2.设置cookie信息
            response.set_cookie('username', qquser.user.username, max_age=14 * 24 * 3600)

            return response

        # return render(request,'oauth_callback.html')

    """
    我们通过post方法来绑定

    1.先接收数据
    2.获取数据
    3.验证数据
    4.access_token( 加密之后的openid)解密
    5.根据手机号进行用户信息的判断
        如果此手机号之前注册过,则和当前这个用户进行绑定,绑定前要验证密码
        如果此手机号之前没有注册过,则重新创建用户
    6.设置登陆的状态
    7.设置cookie信息
    8.跳转指定页面

    """

    def post(self, request):
        # 1.先接收数据
        data = request.POST
        # 2.获取数据
        mobile = data.get('mobile')
        password = data.get('pwd')
        sms_code = data.get('sms_code')
        access_token = data.get('access_token')

        # 3.验证数据
        # 省略

        # 4.access_token( 加密之后的openid)解密
        openid = check_access_token(access_token)
        # 5.根据手机号进行用户信息的判断
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            #     如果此手机号之前没有注册过,则重新创建用户
            user = User.objects.create_user(
                username=mobile,
                password=password,
                mobile=mobile
            )

        else:
            #     如果此手机号之前注册过,绑定前要验证密码
            if not user.check_password(password):
                return http.HttpResponseBadRequest('密码错误')

        # 则和用户进行绑定,
        qquser = OAuthQQUser.objects.create(
            user=user,
            openid=openid
        )
        # 6.设置登陆的状态
        login(request, user)
        # 7.设置cookie信息
        response = redirect(reverse('contents:index'))
        response.set_cookie('username', user.username, max_age=14 * 24 * 3600)
        # 8.跳转指定页面
        return response


######################itsdangerous的使用 加密########################################

# 1.导入
from meiduo_mall import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

# 2.创建实例对象
# secret_key, expires_in = None
# secret_key            秘钥:         习惯上使用 settings.secret_key
#  expires_in = None    过期时间:      单位是 秒
s = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600)
# 3.组织要加密的数据
data = {
    'openid': '1234'
}
# 4.加密
s.dumps(data)
# b'eyJleHAiOjE1NjA3NDkyNzQsImlhdCI6MTU2MDc0NTY3NCwiYWxnIjoiSFM1MTIifQ.
# eyJvcGVuaWQiOiIxMjM0In0.
# 8s2iWVMNU2gIh-d7lksVCqqzAyc3Mz3-eEdMtzlo9SOXAYV2hqssM3uGfLz0rLEfRwORjwC92ejl2eTHzNbGDQ'


# json.dumps  将字典转换为字符串
# json.loads  将字符串转换为字典

###########################itsdangerous的使用 解密#####################################


# 解密所需要的秘钥 和时间是一样的
# 1.导入
from meiduo_mall import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

# 2.创建实例对象
# secret_key, expires_in = None
# secret_key            秘钥:         习惯上使用 settings.secret_key
#  expires_in = None    过期时间:      单位是 秒
s = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600)

# 3.解密
# s.loads()

# {'openid': '1234'}
